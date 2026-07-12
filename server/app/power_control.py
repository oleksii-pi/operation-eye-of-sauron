import socket
import time


class PowerControl:
    def __init__(self, on_ms: int):
        self.server_ip = ""
        self.udp_port = 0
        self.on_ms = on_ms
        self._enabled = False
        self._enabled_until = 0.0
        self._error = ""

    def info(self) -> dict[str, bool | str]:
        self._expire()
        return {
            "configured": bool(self.server_ip),
            "enabled": self._enabled,
            "error": self._error,
            "protocol": "udp",
            "address": self.address,
        }

    @property
    def address(self) -> str:
        if not self.server_ip or not self.udp_port:
            return ""
        return f"{self.server_ip}:{self.udp_port}"

    def set_enabled(self, enabled: bool, address: str) -> dict[str, bool | str]:
        if not self._set_address(address):
            return self.info()
        if not self.server_ip:
            self._error = "LED controller UDP address is not configured"
            return self.info()

        command = f"on:{self.on_ms}" if enabled else "off"
        try:
            self._send(command)
            self._enabled = enabled
            self._enabled_until = time.monotonic() + (self.on_ms / 1000) if enabled else 0.0
            self._error = ""
        except OSError as exc:
            self._error = str(exc)

        return self.info()

    def _set_address(self, address: str) -> bool:
        try:
            self.server_ip, self.udp_port = self._parse_address(address)
            self._error = ""
            return True
        except ValueError as exc:
            self.server_ip = ""
            self.udp_port = 0
            self._enabled = False
            self._enabled_until = 0.0
            self._error = str(exc)
            return False

    def _send(self, command: str) -> None:
        payload = command.encode("ascii")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.1)
            for _ in range(3):
                sock.sendto(payload, (self.server_ip, self.udp_port))

    def _expire(self) -> None:
        if self._enabled and time.monotonic() >= self._enabled_until:
            self._enabled = False
            self._enabled_until = 0.0

    @staticmethod
    def _parse_address(raw_address: str) -> tuple[str, int]:
        address = raw_address.strip()
        address = address.removeprefix("udp://").removeprefix("http://").removeprefix("https://").strip("/")
        if not address:
            raise ValueError("LED controller UDP address is required")
        if ":" not in address:
            raise ValueError("LED controller UDP must be host:port")

        host, port = address.rsplit(":", 1)
        host = host.strip()
        if not host:
            raise ValueError("LED controller UDP host is required")
        try:
            parsed_port = int(port)
        except ValueError:
            raise ValueError("LED controller UDP port must be a number")

        if parsed_port < 1 or parsed_port > 65535:
            raise ValueError("LED controller UDP port must be 1-65535")
        return host, parsed_port
