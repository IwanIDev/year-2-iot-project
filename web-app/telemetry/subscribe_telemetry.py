import json
from datetime import datetime
from urllib.parse import quote
import websocket
from database import db
from telemetry.Telemetry import Telemetry
from users import Users

def parse_message(message):
    payload = json.loads(message)

    if "data" not in payload:
        return None

    results = []

    for key, values in payload["data"].items():
        for ts, value in values:
            results.append({
                "waste_type": value,
                "timestamp": ts
            })

    return results

def subscribe(app, token, device_id):

    base_url = (app.config.get("THINGSBOARD_URL") or "https://thingsboard.cs.cf.ac.uk").rstrip("/")
    if base_url.startswith("https://"):
        ws_base = "wss://" + base_url[len("https://"):]
    elif base_url.startswith("http://"):
        ws_base = "ws://" + base_url[len("http://"):]
    else:
        ws_base = "wss://" + base_url
    ws_url = f"{ws_base}/api/ws/plugins/telemetry?token={quote(token, safe='')}"

    def on_open(ws):
        app.logger.info(f"WebSocket opened for device {device_id}")

        # Subscribe to latest telemetry for this device after handshake auth.
        ws.send(json.dumps({
            "tsSubCmds": [{
                "entityType": "DEVICE",
                "entityId": device_id,
                "scope": "LATEST_TELEMETRY",
                "cmdId": 1
            }],
            "historyCmds": [],
            "attrSubCmds": []
        }))
        app.logger.info(f"Sent subscription command for device {device_id}")

    def on_error(ws, error):
        app.logger.error(f"WebSocket error for device {device_id}: {error}")

    def on_close(ws, close_status_code, close_msg):
        app.logger.warning(
            f"WebSocket closed for device {device_id}. status={close_status_code}, message={close_msg}"
        )

    def on_message(ws, message):
        app.logger.info(f"Received telemetry message for device {device_id}: {message}")
        results = parse_message(message)
        
        if not results:
            return

        with app.app_context():
            user = Users.query.filter_by(device_id=device_id).first()
            points_earned = 0

            for item in results:
                ts = item["timestamp"]
                if isinstance(ts, (int, float)):
                    ts = datetime.fromtimestamp(ts / 1000) if ts > 1e10 else datetime.fromtimestamp(ts)

                existing_row = Telemetry.query.filter_by(
                    deviceId=device_id,
                    wasteType=item["waste_type"], #Need to change so that points added based on wasteType
                    timestamp=ts,
                ).first()
                if existing_row:
                    continue

                row = Telemetry(
                    deviceId=device_id,
                    wasteType=item["waste_type"],
                    timestamp=ts,
                )
                db.session.add(row)
                points_earned += 1

            if user and points_earned:
                user.points += points_earned

            if points_earned:
                db.session.commit()
    
    app.logger.info(f"Starting telemetry subscription for device {device_id}")
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()
