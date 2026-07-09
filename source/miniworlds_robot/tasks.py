from __future__ import annotations

from typing import Tuple

from miniworlds_robot.loader import load


def task(
    name: str,
    robot: str = "standard",
    *,
    position: Tuple[int, int] | None = None,
    debug: bool = False,
):
    return load(name, robot, position=position, debug=debug)
