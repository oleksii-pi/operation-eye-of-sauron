import time

from app.camera_direction import CameraDirection, clamp
from app.motion_detector import MotionDetector


class FollowController:
    def __init__(self, direction: CameraDirection, detector: MotionDetector, width: int, height: int):
        self.direction = direction
        self.detector = detector
        self.width = width
        self.height = height

    def follow(
        self,
        lag_seconds: float,
        max_adjustments: int = 3,
        min_h: int = -100,
        max_h: int = 100,
        min_v: int = -100,
        max_v: int = 100,
    ) -> dict[str, object]:
        delay = min(4.0, max(1.2, lag_seconds))
        bounds = self._bounds(min_h, max_h, min_v, max_v)
        result: dict[str, object] = {
            "status": "no_motion",
            "lag_seconds": round(delay, 2),
            "adjustments": [],
        }
        adjustments: list[dict[str, object]] = []
        try:
            for index in range(max_adjustments):
                target = self._wait_target(delay)
                if not target:
                    result["status"] = "motion_lost" if adjustments else "no_motion"
                    break
                adjustment = self._adjustment(target, index + 1, bounds)
                if adjustment["centered"]:
                    result["status"] = "centered"
                    break
                self.detector.set_enabled(False)
                move = self.direction.move(int(adjustment["horizontal"]), int(adjustment["vertical"]))
                adjustment["error"] = move.get("last_error", "")
                adjustments.append(adjustment)
                result["status"] = "move_error" if adjustment["error"] else "adjusting"
                adjustment["scene_settled"] = self._wait_scene_settled(delay, adjustment["move_distance"])
                self.detector.set_enabled(True)
                if adjustment["error"]:
                    break
        finally:
            self.detector.set_enabled(True)
        if len(adjustments) == max_adjustments and result["status"] == "adjusting":
            result["status"] = "max_adjustments"
        result["adjustments"] = adjustments
        result["target"] = self.detector.target()
        result["direction"] = self.direction.info()
        return result

    def _wait_target(self, timeout: float) -> dict[str, float | int] | None:
        deadline = time.monotonic() + timeout
        while True:
            target = self.detector.target()
            if not target:
                if time.monotonic() >= deadline:
                    return None
                time.sleep(0.05)
                continue
            return target

    def _wait_scene_settled(self, fallback: float, move_distance: int) -> dict[str, float | bool]:
        started_at = time.monotonic()
        timeout = min(8.0, max(fallback, 1.2 + move_distance * 0.18))
        minimum = min(timeout * 0.75, max(0.6, 0.6 + move_distance * 0.04))
        deadline = started_at + timeout
        saw_move = False
        state = self.detector.scene_state()
        while time.monotonic() < deadline:
            state = self.detector.scene_state()
            saw_move = saw_move or float(state["motion"]) > 0.025
            elapsed = time.monotonic() - started_at
            fallback_elapsed = elapsed >= fallback
            if elapsed >= minimum and (saw_move or fallback_elapsed) and state["settled"]:
                return {"ok": True, "seconds": round(elapsed, 2), "motion": round(float(state["motion"]), 4)}
            time.sleep(0.05)
        return {"ok": False, "seconds": round(time.monotonic() - started_at, 2), "motion": state["motion"]}

    def _adjustment(
        self,
        target: dict[str, float | int],
        step: int,
        bounds: tuple[int, int, int, int],
    ) -> dict[str, object]:
        direction = self.direction.info()
        horizontal = int(direction["horizontal"])
        vertical = int(direction["vertical"])
        x_error = (float(target["x"]) - self.width / 2) / (self.width / 2)
        y_error = (float(target["y"]) - self.height / 2) / (self.height / 2)
        next_horizontal = clamp_to(horizontal + round(x_error * 30), bounds[0], bounds[1])
        next_vertical = clamp_to(vertical - round(y_error * 85), bounds[2], bounds[3])
        centered = abs(x_error) < 0.10 and abs(y_error) < 0.10
        move_distance = abs(next_horizontal - horizontal) + abs(next_vertical - vertical)
        return {
            "step": step,
            "x_error": round(x_error, 3),
            "y_error": round(y_error, 3),
            "horizontal": next_horizontal,
            "vertical": next_vertical,
            "move_distance": move_distance,
            "centered": centered or (next_horizontal == horizontal and next_vertical == vertical),
        }

    def _bounds(self, min_h: int, max_h: int, min_v: int, max_v: int) -> tuple[int, int, int, int]:
        min_h = clamp(min_h)
        max_h = clamp(max_h)
        min_v = clamp(min_v)
        max_v = clamp(max_v)
        return min(min_h, max_h), max(min_h, max_h), min(min_v, max_v), max(min_v, max_v)


def clamp_to(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, clamp(value)))
