from datetime import datetime, timezone, timedelta
from flask import Blueprint, current_app, jsonify, request
import httpx
import logging
from api.email_reminders import send_email_reminder
from .collection_dates import fetch_new_collection_dates, get_collection_dates_for_device, parse_collection_dates, update_collection_dates_in_thingsboard
from users import Users
from flask import current_app as app


api_view = Blueprint('api_view', __name__, url_prefix='/api')

@api_view.route('/localAuthority/<device_id>', methods=['POST'])
def set_local_authority(device_id):
    """
    Set the local authority for a device. Expects a JSON payload with 'device_id' and 'local_authority' fields.
    """
    if not device_id:
        return jsonify({'error': 'Device ID is required'}), 400

    payload = request.get_json(silent=True) or {}
    local_authority = payload.get('local_authority', None)
    if not local_authority:
        return jsonify({'error': 'Local authority is required'}), 400
    
    thingsboard_payload = {
            "local_authority": local_authority
    }

    tb_auth = current_app.extensions.get("thingsboard_auth")
    if not tb_auth:
        return jsonify({'error': 'ThingsBoard auth client not initialized'}), 500
    if not tb_auth.is_configured():
        return jsonify({'error': 'ThingsBoard credentials are not configured'}), 503

    def _post_attributes(force_refresh=False):
        return httpx.post(
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SHARED_SCOPE",
            json=thingsboard_payload,
            headers=tb_auth.auth_headers(force_refresh=force_refresh),
            timeout=10,
        )

    try:
        r = _post_attributes()
    except Exception as exc:
        logging.error(f"ThingsBoard request failed for device {device_id}: {exc}")
        return jsonify({'error': 'Failed to contact ThingsBoard'}), 502

    if r.status_code == 401:
        try:
            r = _post_attributes(force_refresh=True)
        except Exception as exc:
            logging.error(f"ThingsBoard retry failed for device {device_id}: {exc}")
            return jsonify({'error': 'Failed to contact ThingsBoard after re-authentication'}), 502

    if not r.is_success:
        logging.error(f"Failed to update Thingsboard device {device_id} with local authority {local_authority}. Response: {r.text}")
        return jsonify({'error': 'Failed to update Thingsboard device', 'details': f"{r.text}"}), 500

    return jsonify({'message': 'Local authority updated successfully'}), 200

@api_view.route('/collectionDates/<device_id>', methods=['POST'])
def set_bin_collection_dates(device_id: str):
    """
    Set the bin collection dates for a device. Expects a JSON payload with 'device_id' and 'collection_dates' fields.
     - 'collection_dates' should be a dictionary of bin types and their corresponding dates in ISO 8601 format.
     - The dates will be stored in ThingsBoard as a shared attribute for the device.
     - Returns a success message if the update is successful, or an error message if there is an issue with the request or ThingsBoard interaction.
    """
    if not device_id: 
        return jsonify({'error': 'Device ID is required'}), 400

    payload = request.get_json(silent=True) or {}
    collection_dates = payload.get('collection_dates', None)
    if not collection_dates:
        return jsonify({'error': 'Collection dates are required'}), 400
   
    tb_auth = current_app.extensions.get("thingsboard_auth")
    if not tb_auth:
        return jsonify({'error': 'ThingsBoard auth client not initialized'}), 500

    try:
        dates = parse_collection_dates(collection_dates)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    thingsboard_payload = {
            "collection_dates": {bc.bin_type.value: bc.collection_date.isoformat() for bc in dates}
    }
    
    def _post_attributes(force_refresh=False):
        return httpx.post(
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/SHARED_SCOPE",
            json=thingsboard_payload,
            headers=tb_auth.auth_headers(force_refresh=force_refresh),
            timeout=10,
        )

    try:
        r = _post_attributes()
    except Exception as exc:
        logging.error(f"ThingsBoard request failed for device {device_id}: {exc}")
        return jsonify({'error': 'Failed to contact ThingsBoard'}), 502
    
    if not r.is_success:
        logging.error(f"Failed to update Thingsboard device {device_id} with collection dates. Response: {r.text}")
        return jsonify({'error': 'Failed to update Thingsboard device', 'details': f"{r.text}"}), 500

    return jsonify({'message': 'Collection dates updated successfully'}), 200

@api_view.route('/bins', methods=['GET'])
def update_bin_dates():
    """
    Endpoint to trigger a check of each device's bin collection dates,
    updating any dates that have passed with the next collection date.
    """
    # Check every user's device on Thingsboard and get bin collection dates
    devices = Users.query.with_entities(Users.device_id).all()
    
    devices_to_update = []
    devices_to_notify = []

    if devices is None:
        return jsonify({'message': 'No devices found'}), 200

    def should_notify_user(collection_date):
        now = datetime.now(timezone.utc)
        if collection_date > now:
            return False
        return (now - collection_date) <= timedelta(days=1)


    for device in devices:
        device_id = device.device_id
        date = get_collection_dates_for_device(device_id, current_app.extensions.get("thingsboard_auth"))
        if date is None:
            logging.warning(f"No collection date found for device {device_id}")
            continue

        if date < datetime.now(timezone.utc):
            devices_to_update.append(device_id)

        if should_notify_user(date):
            devices_to_notify.append(device_id)

    # Send email reminders to users
    for device_id in devices_to_notify:
        user = Users.query.filter_by(device_id=device_id).first()

        if not user:
            logging.error(f"No user found for device {device_id}")
            continue
        
        with httpx.Client() as Client:
            tb_auth = app.extensions["thingsboard_auth"]
            r = Client.get(f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/SHARED_SCOPE", headers=tb_auth.auth_headers(), timeout=10)

            if not r.is_success:
                app.logger.error(f"Failed to retrieve Thingsboard device {device_id} collection dates. Response: {r.text}")
                return "HTTPS request failed", 500
            
            payload = r.json()

            date_dict = [attribute for attribute in payload if attribute.get("key", "") == "next_collection_iso"][0]
            bins_str = [attribute for attribute in payload if attribute.get("key", "") == "bins"][0]
            # Parse bins comma-seperated string into list
            bins = bins_str.get("value", "").split(",") if bins_str.get("value", "") else []
            date = datetime.fromisoformat(date_dict.get("value", "")) if date_dict.get("value", "") else None

        
        if not bins or not date:
            logging.error(f"Failed to retrieve bins or collection date for device {device_id}")
            continue

        send_email_reminder(user, bins, date)
        logging.info(f"Sent email reminder to {user.email} for device {device_id}")
        

    # If collection date has passed, fetch new collection dates and update Thingsboard attributes
    if not devices_to_update:
        return jsonify({'message': 'No devices with past collection dates found'}), 200
    
    # Fetch new collection dates from Bin Collection API and update Thingsboard attributes

    for device_id in devices_to_update:
        # Fetch new collection dates from Bin Collection API
        user = Users.query.filter_by(device_id=device_id).first()

        if not user:
            logging.error(f"No user found for device {device_id}")
            continue

        dates = fetch_new_collection_dates(user)

        if not dates:
            logging.error(f"Failed to fetch new collection dates for device {device_id}")
            continue

        # Update Thingsboard attributes with new collection dates
        if not update_collection_dates_in_thingsboard(device_id, dates, current_app.extensions.get("thingsboard_auth")):
            logging.error(f"Failed to update Thingsboard collection dates for device {device_id}")
            continue

    return jsonify({'message': 'Bin collection dates updated successfully'}), 200

@api_view.route('/reminder/<user_id>', methods=['GET'])
def test_send_reminder(user_id):
    """
    Test endpoint to send an email reminder to a user about their bin collection schedule.
    Expects a user ID as a URL parameter and sends a reminder email to the associated user's email address.
    """
    user = Users.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    bins = get_collection_dates_for_device(user.device_id, current_app.extensions.get("thingsboard_auth"))
    if not bins:
        return jsonify({'error': 'No collection dates found for user\'s device'}), 404
    device_id = user.device_id
    tb_auth = current_app.extensions["thingsboard_auth"]

    with httpx.Client() as Client:

        r = Client.get(f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/SHARED_SCOPE", headers=tb_auth.auth_headers(), timeout=10)

        if not r.is_success:
            app.logger.error(f"Failed to retrieve Thingsboard device {device_id} collection dates. Response: {r.text}")
            return "HTTPS request failed", 500
        
        payload = r.json()

        date_iso = [attribute for attribute in payload if attribute.get("key", "") == "next_collection_iso"][0]
        bins = [attribute for attribute in payload if attribute.get("key", "") == "bins"][0]
        # Parse bins comma-seperated string into list
        bins_list = bins.get("value", "").split(",") if bins.get("value", "") else []

        date = datetime.fromisoformat(date_iso.get("value", "")) if date_iso.get("value", "") else None
        # Create date string: DD MMM YYYY
        date_str = date.strftime("%d %b %Y") if date else "Unknown"

        # Send email reminder to user
        app.logger.info(f"Sending email reminder to {user.email} for bins {bins.get('value', [])} on date {date_iso.get('value', '')}")
        send_email_reminder(user, bins_list, date_str)

    return jsonify({'message': f'Email reminder sent to {user.email}'}), 200
