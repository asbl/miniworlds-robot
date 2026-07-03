from __future__ import annotations

from miniworlds import Actor

import miniworlds_robot.visuals as visuals
from miniworlds_robot.config import RobotConfig
from miniworlds_robot.world import Leaf, Position, RobotWorld


class _RobotBody(Actor):
    def __init__(self, position: Position, *, world: RobotWorld, config: RobotConfig):
        super().__init__(position, world=world)
        self.is_robot_body = True
        self.robot_steps = 0
        self.robot_config = config
        self.size = (1, 1)
        self.direction = config.direction
        self.apply_robot_visual_mode(world.debug)

    def apply_robot_visual_mode(self, debug: bool) -> None:
        self.costume_manager.reset()
        if debug:
            self.add_costume(self.robot_config.costume)
            self.orientation = 0
            return
        costume = self.add_costume(
            visuals.make_robot_surface(self.robot_config.name, self.world.tile_size)
        )
        costume.is_scaled = True
        costume.is_rotatable = False
        self.orientation = 0


class Robot:
    """Restricted public facade for the internal miniworlds actor."""

    _ABILITY_METHODS: dict[str, str] = {
        "step": "_step",
        "turn_left": "_turn_left",
        "turn_right": "_turn_right",
        "on_leaf": "_on_leaf",
        "remove_leaf": "_remove_leaf",
    }

    def __init__(self, actor: _RobotBody, world: RobotWorld):
        self._actor = actor
        self._world = world

    def __getattr__(self, name: str):
        if name == "position" and self._has_ability("position"):
            return self._actor.position
        method_name = self._ABILITY_METHODS.get(name)
        if method_name and self._has_ability(name):
            return getattr(self, method_name)
        raise AttributeError(f"Robot has no ability {name!r} in this world")

    def _has_ability(self, name: str) -> bool:
        return name in self._world.robot_abilities

    def _step(self):
        destination = self._actor.sensor_manager.get_destination(
            self._actor.position, self._actor.direction, 1
        )
        if self._world.is_blocked(destination):
            return self._actor
        self._actor.robot_steps += 1
        return self._actor.move(1)

    def _turn_left(self):
        return self._actor.turn_left(90)

    def _turn_right(self):
        return self._actor.turn_right(90)

    def _on_leaf(self) -> bool:
        return any(
            isinstance(actor, Leaf)
            for actor in self._world.detect_actors(self._actor.position)
            if actor is not self._actor
        )

    def _remove_leaf(self) -> bool:
        for actor in self._world.detect_actors(self._actor.position):
            if isinstance(actor, Leaf):
                actor.remove()
                return True
        return False


def create_robot(config: RobotConfig, world: RobotWorld, position: Position = (0, 0)) -> Robot:
    return Robot(_RobotBody(position, world=world, config=config), world)
