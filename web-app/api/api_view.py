from datetime import datetime, timezone, timedelta
from flask import Blueprint, current_app, jsonify, request
import httpx
import logging
from .collection_dates import BinCollection, BinType, fetch_new_collection_dates, get_collection_dates_for_device, parse_collection_dates, update_collection_dates_in_thingsboard
from users import Users


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

    if devices is None:
        return jsonify({'message': 'No devices found'}), 200

    for device in devices:
        device_id = device.device_id
        dates = get_collection_dates_for_device(device_id, current_app.extensions.get("thingsboard_auth"))
        for type, date_str in dates.items():
            try:
                collection_date = datetime.fromisoformat(date_str)
                if collection_date < datetime.now(timezone.utc):
                    devices_to_update.append(device_id)
                    break
            except ValueError:
                logging.error(f"Invalid date format for device {device_id} bin type {type}: {date_str}")
                continue

    # If collection date has passed, fetch new collection dates and update Thingsboard attributes
    if not devices_to_update:
        return jsonify({'message': 'No devices with past collection dates found'}), 200
    
    # Fetch new collection dates from Bin Collection API and update Thingsboard attributes

    for device in devices_to_update:
        # Fetch new collection dates from Bin Collection API
        user = Users.query.filter_by(device_id=device).first()

        if not user:
            logging.error(f"No user found for device {device}")
            continue

        dates = fetch_new_collection_dates(user)

        if not dates:
            logging.error(f"Failed to fetch new collection dates for device {device}")
            continue

        # Update Thingsboard attributes with new collection dates
        if not update_collection_dates_in_thingsboard(device, dates, current_app.extensions.get("thingsboard_auth")):
            logging.error(f"Failed to update Thingsboard collection dates for device {device}")
            continue

    return jsonify({'message': 'Bin collection dates updated successfully'}), 200
