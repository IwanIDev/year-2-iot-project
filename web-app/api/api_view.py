from flask import Blueprint, current_app, jsonify, request
import httpx
import logging


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

