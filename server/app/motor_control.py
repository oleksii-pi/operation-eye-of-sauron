import requests


class MotorControl:
    def __init__(self, server_ip: str):
        self.server_ip = server_ip.removeprefix("http://").removeprefix("https://").strip("/")
        self._enabled = False
        self._error = ""

    def info(self) -> dict[str, bool | str]:
        return {
            "configured": bool(self.server_ip),
            "enabled": self._enabled,
            "error": self._error,
        }

    def set_enabled(self, enabled: bool) -> dict[str, bool | str]:
        if not self.server_ip:
            self._error = "motor_server_ip is not configured"
            return self.info()

        path = "on" if enabled else "off"
        try:
            response = requests.get(f"http://{self.server_ip}/{path}", timeout=2)
            response.raise_for_status()
            self._enabled = enabled
            self._error = ""
        except requests.RequestException as exc:
            self._error = str(exc)

        return self.info()
