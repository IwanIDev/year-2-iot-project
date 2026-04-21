from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Dict, List, Optional
from flask import current_app as app
import httpx
from users.Users import Users
import sys
from bin_lookup.council_bins import wales_bins

def format_date(date_str):
    """
    Format a date string from dd/mm/yyyy to '13th April' format.
    """
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        day = dt.day
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10 if day % 10 < 4 and day // 10 != 1 else 0, 'th')
        month = dt.strftime("%B")
        return f"{day}{suffix} {month}"
    except ValueError:
        return date_str  # fallback

def parse_collection_dates(data, council):
    """
    Parse collection dates data and format into human-readable format.
    Assumes all bins have the same collection date.
    Returns a dict with 'collection_date' and 'bins'.
    """
    bins_data = data.get("bins", [])
    if not bins_data:
        return {}

    # Assume all dates are the same, take the first
    collection_date_str = bins_data[0].get("collectionDate", "")
    formatted_date = format_date(collection_date_str)
    
    # Also get ISO format for checking
    try:
        dt = datetime.strptime(collection_date_str, "%d/%m/%Y")
        dt = dt.replace(tzinfo=timezone.utc)
        iso_date = dt.isoformat().replace("+00:00", "Z")
    except ValueError:
        iso_date = collection_date_str

    bin_names = set()  # to avoid duplicates
    for bin_item in bins_data:
        bin_type = bin_item.get("type", "").lower().replace(" ", "_")
        if bin_type == "recycling":
            for waste_type in ["paper", "plastic", "metal"]:
                bin_name = wales_bins.get(council.lower(), {}).get(waste_type, waste_type)
                bin_names.add(bin_name)
        else:
            bin_name = wales_bins.get(council.lower(), {}).get(bin_type, bin_type)
            bin_names.add(bin_name)

    bins_str = ", ".join(sorted(bin_names))
    return {"collection_date": formatted_date, "bins": bins_str, "next_collection_iso": iso_date}

def update_collection_dates_in_thingsboard(device_id: str, parsed_data: Dict[str, str], tb_auth) -> bool:
    """
    Update the collection dates for a device in ThingsBoard as shared attributes.
    Expects parsed_data with 'collection_date' and 'bins' keys.
    Returns True if the update was successful, False otherwise.
    """
    thingsboard_payload = parsed_data
    
    def _post_attributes(force_refresh=False):
        return httpx.post(
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/SHARED_SCOPE",
            json=thingsboard_payload,
            headers=tb_auth.auth_headers(force_refresh=force_refresh),
            timeout=10,
        )
    try:
        r = _post_attributes()
        if not r.is_success:
            app.logger.error(f"Failed to update Thingsboard device {device_id} with collection dates. Response: {r.text}")
            return False
        return True
    except Exception as exc:
        app.logger.error(f"ThingsBoard request failed for device {device_id}: {exc}")
        return False

def get_collection_dates_for_device(device_id: str, tb_auth) -> Dict[str, str]:
    """
    Retrieve the collection dates for a device from ThingsBoard shared attributes.
    Returns a dictionary with 'collection_date' and 'bins'.
    """
    try:
        r = httpx.get(
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/SHARED_SCOPE",
            headers=tb_auth.auth_headers(),
            timeout=10,
        )
        if r.is_success:
            data = r.json()
            return data[0].get("value", {})
        else:
            app.logger.error(f"Failed to retrieve Thingsboard device {device_id} collection dates. Response: {r.text}")
            return {}
    except Exception as exc:
        app.logger.error(f"ThingsBoard request failed for device {device_id}: {exc}")
        return {}

def fetch_new_collection_dates(user: Users) -> Dict[str, str]:
    """
    Get new collection dates from the Bin Collection API for a user.
    Returns parsed data in human-readable format.
    """
    council = user.council
    uprn = user.UPRN
    api_url = council.url
    council_name = council.collectionName
    url = app.config["BIN_COLLECTION_API"]
    
    if not api_url:
        app.logger.warning(f"No API URL configured for council {council_name}")

    if not council_name:
        app.logger.warning(f"No collection name configured for council {council_name}")

    bin_collection_api_url = f"{url}/api/bin_collection/{council_name}"
    api_params = {
        "uprn": uprn if uprn else None,
        "url": api_url if api_url else None
    }

    cert_file = Path(__file__).resolve().parent.parent / "cert.pem"
    data = []

    with httpx.Client(verify=cert_file.as_posix()) as client:
        r = client.get(
            bin_collection_api_url,
            params=api_params,
            timeout=10,
        )

        if not r.is_success:
            app.logger.error(f"Failed to fetch collection dates for user {user.id} from Bin Collection API. Response: {r.text}")
            return []

        # Parse the response for collection dates
        """
        Expected response format:
            "bins": [
                {"type": "Food", "collectionDate": "23/04/2026"},
                {"type": "Recycling", "collectionDate": "23/04/2026"},
                {"type": "General", "collectionDate": "30/04/2026"},
                {"type": "Glass", "collectionDate": "30/04/2026"},
                {"type": "Food", "collectionDate": "30/04/2026"},
                {"type": "Recycling", "collectionDate": "30/04/2026"}
            ]
        """
        data_str = r.json()
        # Note: the API seems to double-encode the JSON response (annoyingly)
        data = json.loads(data_str) if isinstance(data_str, str) else data_str

    # Parse into human-readable format
    parsed_data = parse_collection_dates(data, council_name)
    return parsed_data



            

