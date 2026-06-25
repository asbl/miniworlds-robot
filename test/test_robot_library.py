from unittest.mock import patch

import pytest

from miniworlds import Actor, TiledWorld
from miniworlds_robot import Leaf, Loader, ObjectConfig, RobotConfig, WorldConfig, load_robot, load_world


def test_loader_creates_world_and_robot_with_restricted_default_api():
    world = load_world("basic")
    robot = load_robot("standard", world, position=(1, 1))

    robot.step()
    robot.turn_left()
    robot.turn_right()

    with pytest.raises(AttributeError):
        robot.position

    assert all(isinstance(actor, Actor) for actor in world.actors)


def test_world_config_can_expose_position():
    world = load_world("with_position")
    robot = load_robot("standard", world, position=(2, 3))

    assert robot.position == (2, 3)


def test_custom_world_config_controls_leaf_abilities():
    config = WorldConfig(
        name="leaf-world",
        robot_abilities=frozenset({"on_leaf", "remove_leaf"}),
    )
    world = Loader.load_world(config)
    robot = Loader.load_robot(RobotConfig(name="green", costume=(40, 160, 80, 255)), world, position=(1, 1))
    Leaf((1, 1), world=world)

    assert robot.on_leaf()
    assert robot.remove_leaf()
    assert not robot.on_leaf()


def test_loader_places_configured_world_objects():
    world = load_world(
        WorldConfig(
            name="configured-objects",
            objects=(
                ObjectConfig("tree", (1, 1)),
                ObjectConfig("mushroom", (2, 1)),
                ObjectConfig("leaf", (3, 1)),
            ),
        )
    )

    assert world.is_blocked((1, 1))
    assert world.is_blocked((2, 1))
    assert not world.is_blocked((3, 1))


def test_robot_cannot_step_onto_a_blocking_object_or_count_the_attempt():
    world = load_world("obstacle_garden")
    robot = load_robot(world=world, position=(2, 1))

    robot.step()

    assert robot._actor.position == (2, 1)
    assert robot._actor.robot_steps == 0


def test_robot_cannot_leave_the_world_or_count_the_attempt():
    world = load_world(WorldConfig(name="small", columns=2, rows=2))
    robot = load_robot(RobotConfig(name="left", direction=-90), world, position=(0, 0))

    robot.step()

    assert robot._actor.position == (0, 0)
    assert robot._actor.robot_steps == 0


def test_successful_step_moves_robot_and_counts_once():
    world = load_world("basic")
    robot = load_robot(world=world, position=(0, 0))

    robot.step()

    assert robot._actor.position == (1, 0)
    assert robot._actor.robot_steps == 1


def test_run_keeps_tiled_world_runtime_behavior():
    world = load_world("basic")

    with patch.object(TiledWorld, "run") as run:
        world.run(fullscreen=True)

    run.assert_called_once_with(fullscreen=True)


def test_unknown_configs_raise_clear_errors():
    with pytest.raises(ValueError, match="Unknown RobotWorld config"):
        load_world("missing")

    with pytest.raises(ValueError, match="Unknown Robot config"):
        load_robot("missing")
