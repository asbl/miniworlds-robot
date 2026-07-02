from __future__ import annotations

from typing import Tuple, Type

from miniworlds import Actor, TiledWorld

from miniworlds.appearances.managers.image_manager import ImageManager
import miniworlds_robot.visuals as visuals
from miniworlds_robot.config import WorldConfig


Position = Tuple[float, float]


class RobotWorld(TiledWorld):
    """A miniworlds tiled world with a configuration-driven Robot API."""

    def __init__(self, config: WorldConfig | None = None, **overrides):
        config = config or WorldConfig(name="custom")
        self.robot_config = config
        columns = overrides.pop("columns", config.columns)
        rows = overrides.pop("rows", config.rows)
        tile_size = overrides.pop("tile_size", config.tile_size)
        debug = overrides.pop("debug", config.debug)
        super().__init__(columns, rows, tile_size=tile_size, **overrides)
        self.tile_size = tile_size
        self._robot_debug = False
        self.debug = debug

    @property
    def debug(self) -> bool:
        return self._robot_debug

    @debug.setter
    def debug(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"debug must be bool, got {type(value).__name__}: {value!r}")
        self._robot_debug = value
        self._apply_visual_mode()

    def _apply_visual_mode(self) -> None:
        if self.debug:
            self.background = self.robot_config.background
            self.grid = True
        else:
            self.grid = False
            self.background.image_manager.replace_image(
                visuals.make_world_background(
                    self.width, self.height, self.tile_size
                ),
                ImageManager.SURFACE,
                None,
            )
            self.background.is_scaled = True
            self.background.set_dirty("all", self.background.LOAD_NEW_IMAGE)
        for actor in self.actors:
            apply_visual_mode = getattr(actor, "apply_robot_visual_mode", None)
            if apply_visual_mode:
                apply_visual_mode(self.debug)

    @property
    def robot_abilities(self) -> frozenset[str]:
        return self.robot_config.robot_abilities

    def is_blocked(self, position: Position) -> bool:
        if not self.is_tile(position):
            return True
        return any(getattr(actor, "blocks_robot", False) for actor in self.detect_actors(position))

    def add_object(self, actor_cls: Type[Actor], position: Position) -> Actor:
        return actor_cls(position, world=self)

    def is_solved(self) -> bool:
        """Return whether the current world state matches the task target."""
        target = self.robot_config.target
        if target.robot_position is not None and self._robot_positions() != (target.robot_position,):
            return False
        if target.robot_direction is not None and self._robot_directions() != (target.robot_direction,):
            return False
        if target.robot_steps is not None and self._robot_steps() != (target.robot_steps,):
            return False
        if target.objects is not None and self._object_state() != self._object_target_state(target.objects):
            return False
        return True

    def _robot_positions(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            sorted(
                actor.position
                for actor in self.actors
                if getattr(actor, "is_robot_body", False)
            )
        )

    def _robot_directions(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                actor.direction
                for actor in self.actors
                if getattr(actor, "is_robot_body", False)
            )
        )

    def _robot_steps(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                actor.robot_steps
                for actor in self.actors
                if getattr(actor, "is_robot_body", False)
            )
        )

    def _object_state(self) -> tuple[tuple[str, tuple[int, int]], ...]:
        return tuple(
            sorted(
                (actor.robot_object_kind, actor.position)
                for actor in self.actors
                if hasattr(actor, "robot_object_kind")
            )
        )

    @staticmethod
    def _object_target_state(objects) -> tuple[tuple[str, tuple[int, int]], ...]:
        return tuple(sorted((obj.kind, obj.position) for obj in objects))


class RobotObject(Actor):
    blocks_robot = False
    collectable = False
    costume_color = (255, 255, 255, 255)
    robot_object_kind = "object"
    normal_costume_factory = None

    def __init__(self, position: Position = (0, 0), *, world=None):
        super().__init__(position, world=world)
        self.size = (1, 1)
        self.is_blocking = self.blocks_robot
        self.apply_robot_visual_mode(getattr(world, "debug", False))

    def apply_robot_visual_mode(self, debug: bool) -> None:
        self.costume_manager.reset()
        if debug or self.normal_costume_factory is None:
            self.add_costume(self.costume_color)
            return
        costume = self.add_costume(self.normal_costume_factory(self.world.tile_size))
        costume.is_scaled = True


class Tree(RobotObject):
    blocks_robot = True
    costume_color = (33, 120, 58, 255)
    robot_object_kind = "tree"
    normal_costume_factory = staticmethod(visuals.make_tree_surface)


class Mushroom(RobotObject):
    blocks_robot = True
    costume_color = (192, 43, 48, 255)
    robot_object_kind = "mushroom"
    normal_costume_factory = staticmethod(visuals.make_mushroom_surface)


class Leaf(RobotObject):
    collectable = True
    costume_color = (74, 159, 65, 255)
    robot_object_kind = "leaf"
    normal_costume_factory = staticmethod(visuals.make_leaf_surface)
