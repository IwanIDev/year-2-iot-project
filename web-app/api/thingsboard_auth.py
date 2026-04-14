"""
Stores ThingsBoard credentials and manages Bearer token authentication.
Provides authentication headers for API requests and handles token refresh.
"""

import base64
import json
import logging
import threading
import time
import httpx


class ThingsBoardAuth:
    def __init__(self, base_url, username, password, timeout=10):
        self.base_url = (base_url or "").rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self._token = None
        self._token_expiry = 0
        self._lock = threading.Lock()

    def is_configured(self):
        return bool(self.base_url and self.username and self.password)

    def _decode_token_exp(self, token):
        """Decode the 'exp' claim from a JWT token without verifying the signature."""
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8")).decode("utf-8")
        claims = json.loads(decoded)
        return int(claims["exp"])

    def _login(self):
        """Perform login to ThingsBoard and store the token and its expiry."""
        if not self.is_configured():
            raise RuntimeError("ThingsBoard auth is not configured")

        response = httpx.post(
            f"{self.base_url}/api/auth/login",
            json={"username": self.username, "password": self.password},
            timeout=self.timeout,
        )
        response.raise_for_status()

        token = response.json().get("token")
        if not token:
            raise RuntimeError("ThingsBoard login response did not include token")

        self._token = token
        # Refresh shortly before expiry to reduce request-time failures.
        self._token_expiry = self._decode_token_exp(token) - 30

    def invalidate(self):
        """Invalidate the current token, forcing a refresh on next use."""
        with self._lock:
            self._token = None
            self._token_expiry = 0

    def get_token(self, force_refresh=False):
        """Get the current token, refreshing if necessary or if force_refresh is True."""
        now = int(time.time())
        if not force_refresh and self._token and now < self._token_expiry:
            return self._token

        with self._lock:
            now = int(time.time())
            if force_refresh or (not self._token) or (now >= self._token_expiry):
                self._login()
            return self._token

    def auth_headers(self, force_refresh=False):
        """Get the authorization headers for ThingsBoard API requests."""
        return {"Authorization": f"Bearer {self.get_token(force_refresh=force_refresh)}"}

    def warmup(self):
        """Perform initial login to ThingsBoard"""
        if not self.is_configured():
            logging.warning(
                "ThingsBoard auth not configured. Set THINGSBOARD_URL, THINGSBOARD_USERNAME, THINGSBOARD_PASSWORD"
            )
            return
        self.get_token(force_refresh=True)
