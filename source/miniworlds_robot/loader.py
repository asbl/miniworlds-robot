from __future__ import annotations

import json
from dataclasses import replace
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from miniworlds_robot.config import ROBOT_CONFIGS, WORLD_CONFIGS, RobotConfig, WorldConfig
from miniworlds_robot.config import ObjectConfig, TargetConfig
from miniworlds_robot.robot import Robot, create_robot
from miniworlds_robot.world import Leaf, Mushroom, Position, RobotWorld, Tree


OBJECT_TYPES = {
    "leaf": Leaf,
    "mushroom": Mushroom,
    "tree": Tree,
}


def _is_url(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https"}


def _github_blob_to_raw_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "github.com":
        return url
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "blob":
        return url
    owner, repo, _, ref, *path = parts
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{'/'.join(path)}"


def _position_from_json(value: Any, field_name: str) -> tuple[int, int]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or not all(isinstance(item, int) for item in value)
    ):
        raise ValueError(f"{field_name} must be a two-item integer position")
    return (value[0], value[1])


def _color_from_json(value: Any, field_name: str):
    if (
        not isinstance(value, (list, tuple))
        or len(value) not in {3, 4}
        or not all(isinstance(item, int) for item in value)
    ):
        raise ValueError(f"{field_name} must be an RGB or RGBA integer color")
    return tuple(value)


def _objects_from_json(value: Any, field_name: str) -> tuple[ObjectConfig, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    objects: list[ObjectConfig] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{field_name}[{index}] must be an object")
        kind = item.get("kind")
        if not isinstance(kind, str):
            raise ValueError(f"{field_name}[{index}].kind must be a string")
        objects.append(
            ObjectConfig(
                kind,
                _position_from_json(item.get("position"), f"{field_name}[{index}].position"),
            )
        )
    return tuple(objects)


def _target_from_json(value: Any) -> TargetConfig:
    if value is None:
        return TargetConfig()
    if not isinstance(value, dict):
        raise ValueError("target must be an object")
    kwargs: dict[str, Any] = {}
    if "robot_position" in value and value["robot_position"] is not None:
        kwargs["robot_position"] = _position_from_json(
            value["robot_position"], "target.robot_position"
        )
    if "robot_direction" in value:
        robot_direction = value["robot_direction"]
        if robot_direction is not None and not isinstance(robot_direction, int):
            raise ValueError("target.robot_direction must be an integer")
        kwargs["robot_direction"] = robot_direction
    if "robot_steps" in value:
        robot_steps = value["robot_steps"]
        if robot_steps is not None and not isinstance(robot_steps, int):
            raise ValueError("target.robot_steps must be an integer")
        kwargs["robot_steps"] = robot_steps
    if "objects" in value:
        kwargs["objects"] = None if value["objects"] is None else _objects_from_json(
            value["objects"], "target.objects"
        )
    return TargetConfig(**kwargs)


def world_config_from_json(data: str | bytes | dict[str, Any]) -> WorldConfig:
    """Create a :class:`WorldConfig` from the JSON world format."""
    if isinstance(data, (str, bytes)):
        data = json.loads(data)
    if not isinstance(data, dict):
        raise ValueError("RobotWorld JSON must contain an object")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")

    config = WorldConfig(name=name)
    changes: dict[str, Any] = {}
    for field_name in ("columns", "rows", "tile_size"):
        if field_name in data:
            value = data[field_name]
            if not isinstance(value, int):
                raise ValueError(f"{field_name} must be an integer")
            changes[field_name] = value
    if "background" in data:
        changes["background"] = _color_from_json(data["background"], "background")
    if "debug" in data:
        if not isinstance(data["debug"], bool):
            raise ValueError("debug must be a boolean")
        changes["debug"] = data["debug"]
    if "objects" in data:
        changes["objects"] = _objects_from_json(data["objects"], "objects")
    if "target" in data:
        changes["target"] = _target_from_json(data["target"])
    if "robot_abilities" in data:
        robot_abilities = data["robot_abilities"]
        if not isinstance(robot_abilities, list) or not all(
            isinstance(item, str) for item in robot_abilities
        ):
            raise ValueError("robot_abilities must be a list of strings")
        changes["robot_abilities"] = frozenset(robot_abilities)
    return replace(config, **changes)


def _read_url_text(url: str) -> str:
    try:
        from pyodide.http import open_url
    except ImportError:
        with urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8")

    with open_url(url) as response:
        return response.read()


def load_world_config_from_url(url: str) -> WorldConfig:
    """Load a RobotWorld JSON config from an HTTP(S) URL.

    GitHub ``/blob/`` URLs are accepted and converted to their raw equivalent.
    """
    raw_url = _github_blob_to_raw_url(url)
    return world_config_from_json(_read_url_text(raw_url))


def _resolve_world_config(config: str | WorldConfig) -> WorldConfig:
    if isinstance(config, WorldConfig):
        return config
    if _is_url(config):
        return load_world_config_from_url(config)
    try:
        return WORLD_CONFIGS[config]
    except KeyError:
        raise ValueError(f"Unknown RobotWorld config: {config!r}") from None


def _resolve_robot_config(config: str | RobotConfig) -> RobotConfig:
    if isinstance(config, RobotConfig):
        return config
    try:
        return ROBOT_CONFIGS[config]
    except KeyError:
        raise ValueError(f"Unknown Robot config: {config!r}") from None


def load_world(config: str | WorldConfig = "basic", **overrides) -> RobotWorld:
    world_config = _resolve_world_config(config)
    world = RobotWorld(world_config, **overrides)
    for obj in world_config.objects:
        try:
            object_cls = OBJECT_TYPES[obj.kind]
        except KeyError:
            raise ValueError(f"Unknown RobotWorld object kind: {obj.kind!r}") from None
        world.add_object(object_cls, obj.position)
    return world


def load_robot(
    config: str | RobotConfig = "standard",
    world: RobotWorld | None = None,
    *,
    position: Position = (0, 0),
) -> Robot:
    if world is None:
        world = load_world()
    return create_robot(_resolve_robot_config(config), world, position)


class Loader:
    load_world = staticmethod(load_world)
    load_robot = staticmethod(load_robot)
    load_world_config_from_url = staticmethod(load_world_config_from_url)
