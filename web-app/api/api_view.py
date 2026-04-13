from flask import Blueprint, jsonify, request
import httpx
import logging


api_view = Blueprint('api_view', __name__, url_prefix='/api')

@api_view.route('/setLocalAuthority', methods=['POST'])
def set_local_authority():
    """
    Set the local authority for a device. Expects a JSON payload with 'device_id' and 'local_authority' fields.
    """
    device_id = request.json.get('device_id', None)
    if not device_id:
        return jsonify({'error': 'Device ID is required'}), 400

    local_authority = request.json.get('local_authority', None)
    if not local_authority:
        return jsonify({'error': 'Local authority is required'}), 400
    
    thingsboard_payload = {
            "local_authority": local_authority
    }
    
    r = httpx.post(
            f"https://thingsboard.cs.cf.ac.uk/api/plugins/telemetry/DEVICE/{device_id}/attributes/SHARED_SCOPE",
            data=thingsboard_payload,
    )

    if not r.is_success:
        logging.error(f"Failed to update Thingsboard device {device_id} with local authority {local_authority}. Response: {r.text}")
        return jsonify({'error': 'Failed to update Thingsboard device', 'details': f"{r.text}"}), 500

    return jsonify({'message': 'Local authority updated successfully'}), 200

