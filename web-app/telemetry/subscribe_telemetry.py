
import json
from datetime import datetime
import websocket

from database import db
from telemetry.Telemetry import Telemetry

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

    def on_open(ws):
    

        # 🔐 Authenticate
        ws.send(json.dumps({
            "authCmd": {
                "cmdId": 0,
                "token": token
            }
        }))

        # 📡 Subscribe to device
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

    def on_message(ws, message):
        results = parse_message(message)
        
        if not results:
            return

        with app.app_context():
            for item in results:
                # Convert timestamp to datetime if needed
                ts = item["timestamp"]
                if isinstance(ts, (int, float)):
                    ts = datetime.fromtimestamp(ts / 1000) if ts > 1e10 else datetime.fromtimestamp(ts)
                
                row = Telemetry(
                    deviceId=device_id,
                    wasteType=item["waste_type"],
                    timestamp=ts,
                )
                db.session.add(row)
            db.session.commit()

    ws = websocket.WebSocketApp(
        "wss://thingsboard.cs.cf.ac.uk/api/ws",
        on_open=on_open,
        on_message=on_message,
    )
    ws.run_forever()