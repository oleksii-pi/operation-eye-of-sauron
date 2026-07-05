import base64
import hashlib
import os
import threading
from datetime import UTC, datetime
from urllib.parse import unquote, urlsplit

import requests


class CameraDirection:
    def __init__(self, rtsp_url: str, onvif_port: int = 2020):
        parts = urlsplit(rtsp_url)
        self.host = parts.hostname or ""
        self.user = unquote(parts.username or "")
        self.password = unquote(parts.password or "")
        self.service_url = f"http://{self.host}:{onvif_port}/onvif/service"
        self._lock = threading.Lock()
        self._horizontal = 0
        self._vertical = 0
        self._last_error = ""

    def info(self) -> dict[str, int | str | bool]:
        with self._lock:
            return {
                "horizontal": self._horizontal,
                "vertical": self._vertical,
                "configured": bool(self.host and self.user and self.password),
                "last_error": self._last_error,
            }

    def move(self, horizontal: int, vertical: int) -> dict[str, int | str | bool]:
        horizontal = clamp(horizontal)
        vertical = clamp(vertical)
        error = self._absolute_move(-horizontal / 100, -vertical / 100)
        with self._lock:
            self._horizontal = horizontal
            self._vertical = vertical
            self._last_error = error
        return self.info()

    def _absolute_move(self, x: float, y: float) -> str:
        if not self.host or not self.user or not self.password:
            return "ONVIF needs host, username, and password from RTSP_URL"
        action = (
            "<tptz:AbsoluteMove>"
            "<tptz:ProfileToken>profile_1</tptz:ProfileToken>"
            f"<tptz:Position><tt:PanTilt x=\"{x:.2f}\" y=\"{y:.2f}\"/></tptz:Position>"
            "<tptz:Speed><tt:PanTilt x=\"0.50\" y=\"0.50\"/></tptz:Speed>"
            "</tptz:AbsoluteMove>"
        )
        try:
            response = requests.post(
                self.service_url,
                data=self._envelope(action),
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                timeout=5,
            )
            response.raise_for_status()
            if "Fault" in response.text:
                return response.text
            return ""
        except requests.RequestException as exc:
            return str(exc)

    def _envelope(self, action: str) -> str:
        nonce = os.urandom(16)
        created = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        digest = base64.b64encode(hashlib.sha1(nonce + created.encode() + self.password.encode()).digest()).decode()
        nonce64 = base64.b64encode(nonce).decode()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
  xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"
  xmlns:tt="http://www.onvif.org/ver10/schema"
  xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
  xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
  <s:Header><wsse:Security><wsse:UsernameToken>
    <wsse:Username>{self.user}</wsse:Username>
    <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">{digest}</wsse:Password>
    <wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">{nonce64}</wsse:Nonce>
    <wsu:Created>{created}</wsu:Created>
  </wsse:UsernameToken></wsse:Security></s:Header>
  <s:Body>{action}</s:Body>
</s:Envelope>"""


def clamp(value: int) -> int:
    return max(-100, min(100, value))
