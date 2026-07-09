import io
import sys
import types
from unittest.mock import patch

import pytest

from miniworlds import Actor, TiledWorld
from miniworlds_robot import (
    Leaf,
    Loader,
    ObjectConfig,
    RobotConfig,
    TargetConfig,
    WorldConfig,
    load,
    load_robot,
    load_world,
    load_world_config_from_url,
    world_config_from_json,
    task,
)


REMOTE_WORLDS_BASE_URL = (
    "https://github.com/asbl/miniworlds-robot-worlds/blob/main/worlds"
)


def current_costume_source(actor):
    return actor.costume.image_manager.images_list[
        actor.costume.image_manager.image_index
    ]["source"]


def current_costume_type(actor):
    return actor.costume.image_manager.images_list[
        actor.costume.image_manager.image_index
    ]["type"]


def current_background_source(world):
    return world.background.image_manager.images_list[
        world.background.image_manager.image_index
    ]["source"]


def test_loader_creates_world_and_robot_with_restricted_default_api():
    world = load_world("basic")
    robot = load_robot("standard", world, position=(1, 1))

    robot.step()
    robot.turn_left()
    robot.turn_right()

    with pytest.raises(AttributeError):
        robot.position

    assert all(isinstance(actor, Actor) for actor in world.actors)


def test_loader_uses_explicit_empty_world_for_robot():
    world = load_world("loop_square")
    robot = load_robot(world=world, position=(1, 1))

    assert robot._actor in world.actors


def test_normal_mode_uses_graphical_robot_and_tiles():
    world = load_world("basic")
    robot = load_robot("blue", world, position=(1, 1))

    assert world.debug is False
    assert world.grid is False
    assert current_background_source(world) is None
    assert current_costume_source(robot._actor) is None
    assert current_costume_type(robot._actor) == 3


def test_debug_mode_keeps_original_block_visuals():
    world = load_world("basic", debug=True)
    robot = load_robot("standard", world, position=(1, 1))
    leaf = Leaf((2, 1), world=world)

    assert world.debug is True
    assert world.grid is True
    assert current_background_source(world) == world.robot_config.background
    assert current_costume_source(robot._actor) == robot._actor.robot_config.costume
    assert current_costume_source(leaf) == leaf.costume_color


def test_task_can_start_in_debug_mode():
    world, robot = task("sequence_path", debug=True)

    assert world.debug is True
    assert world.grid is True
    assert current_costume_source(robot._actor) == robot._actor.robot_config.costume


def test_task_accepts_explicit_position():
    world, robot = task("sequence_path", position=(2, 2))

    assert robot._actor.position == (2, 2)


def test_visual_mode_toggle_updates_existing_robot_objects():
    world = load_world("leaf_line")
    robot = load_robot("standard", world, position=(0, 1))
    leaf = next(
        actor
        for actor in world.actors
        if getattr(actor, "robot_object_kind", None) == "leaf"
    )

    world.debug = True

    assert world.grid is True
    assert current_costume_source(robot._actor) == robot._actor.robot_config.costume
    assert current_costume_source(leaf) == leaf.costume_color

    world.debug = False

    assert world.grid is False
    assert current_costume_source(robot._actor) is None
    assert current_costume_type(robot._actor) == 3
    assert current_costume_source(leaf) is None


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


def test_world_config_can_be_loaded_from_json():
    config = world_config_from_json(
        {
            "name": "json-world",
            "columns": 4,
            "rows": 3,
            "objects": [{"kind": "tree", "position": [2, 1]}],
            "target": {"robot_position": [1, 1], "robot_steps": 2},
            "robot_abilities": ["step", "position"],
        }
    )
    world = load_world(config)

    assert world.columns == 4
    assert world.rows == 3
    assert world.is_blocked((2, 1))
    assert world.robot_abilities == frozenset({"step", "position"})


def test_world_config_can_be_loaded_from_github_blob_url():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"name": "remote-world", "columns": 3, "rows": 2}'

    with patch("miniworlds_robot.loader.urlopen", return_value=Response()) as urlopen:
        config = load_world_config_from_url(
            "https://github.com/example/miniworlds-robot-worlds/blob/main/worlds/remote.json"
        )

    assert config.name == "remote-world"
    assert config.columns == 3
    urlopen.assert_called_once_with(
        "https://raw.githubusercontent.com/example/miniworlds-robot-worlds/main/worlds/remote.json",
        timeout=10,
    )


def test_world_config_url_loader_rejects_non_http_scheme():
    with pytest.raises(ValueError, match="http or https"):
        load_world_config_from_url("file:///etc/passwd")


def test_world_config_url_loader_uses_pyodide_open_url_when_available():
    calls = []
    pyodide = types.ModuleType("pyodide")
    http = types.ModuleType("pyodide.http")

    def open_url(url):
        calls.append(url)
        return io.StringIO('{"name": "pyodide-world", "columns": 4, "rows": 2}')

    http.open_url = open_url

    with patch.dict(sys.modules, {"pyodide": pyodide, "pyodide.http": http}):
        with patch("miniworlds_robot.loader.urlopen") as urlopen:
            config = load_world_config_from_url(
                "https://github.com/example/miniworlds-robot-worlds/blob/main/worlds/remote.json"
            )

    assert config.name == "pyodide-world"
    assert config.columns == 4
    assert calls == [
        "https://raw.githubusercontent.com/example/miniworlds-robot-worlds/main/worlds/remote.json"
    ]
    urlopen.assert_not_called()


@pytest.mark.network
def test_world_can_be_loaded_from_published_github_repository():
    world = load_world(f"{REMOTE_WORLDS_BASE_URL}/04-loops/loops_03_square.json")

    assert world.robot_config.name == "loops_03_square"
    assert world.columns == 6
    assert world.rows == 6
    assert world.robot_config.target.robot_steps == 8


@pytest.mark.network
def test_published_github_repository_contains_concept_worlds():
    samples = {
        "01-sequences/sequence_01_straight_line.json": "sequence_01_straight_line",
        "02-variables/variables_01_step_count.json": "variables_01_step_count",
        "03-functions/functions_01_double_step.json": "functions_01_double_step",
        "04-loops/loops_01_four_steps.json": "loops_01_four_steps",
        "05-nested-loops/nested_loops_01_two_rows.json": "nested_loops_01_two_rows",
        "06-if-statements/if_01_leaf_here.json": "if_01_leaf_here",
        "07-while-loops/while_01_until_x.json": "while_01_until_x",
        "08-boolean-logic/boolean_01_leaf_and_position.json": (
            "boolean_01_leaf_and_position"
        ),
    }

    for path, expected_name in samples.items():
        config = load_world_config_from_url(f"{REMOTE_WORLDS_BASE_URL}/{path}")
        assert config.name == expected_name


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


def test_can_move_is_blocked_by_a_blocking_object():
    world = load_world(
        WorldConfig(
            name="blocked",
            columns=5,
            rows=3,
            objects=(ObjectConfig("tree", (3, 1)),),
            robot_abilities=frozenset({"step", "can_move"}),
        )
    )
    robot = load_robot(world=world, position=(2, 1))

    assert robot.can_move() is False


def test_can_move_is_blocked_by_world_border():
    world = load_world(
        WorldConfig(
            name="small",
            columns=2,
            rows=2,
            robot_abilities=frozenset({"step", "can_move"}),
        )
    )
    robot = load_robot(
        RobotConfig(name="left", direction=-90),
        world,
        position=(0, 0),
    )

    assert robot.can_move() is False


def test_can_move_is_true_on_free_tile():
    world = load_world(
        WorldConfig(
            name="free",
            columns=5,
            rows=3,
            robot_abilities=frozenset({"step", "can_move"}),
        )
    )
    robot = load_robot(world=world, position=(0, 0))

    assert robot.can_move() is True


def test_can_move_requires_ability():
    config = WorldConfig(
        name="no-can-move",
        robot_abilities=frozenset({"step", "turn_left"}),
    )
    world = load_world(config)
    robot = load_robot(world=world, position=(0, 0))

    with pytest.raises(AttributeError, match="can_move"):
        robot.can_move()


def test_can_move_supports_writing_a_while_loop():
    config = WorldConfig(
        name="walk-to-wall",
        columns=5,
        rows=2,
        start_position=(0, 0),
        robot_abilities=frozenset({"step", "can_move"}),
    )
    world = load_world(config)
    robot = load_robot(world=world, position=(0, 0))

    steps_taken = 0
    while robot.can_move():
        robot.step()
        steps_taken += 1

    assert steps_taken == 4
    assert robot._actor.position == (4, 0)


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


def test_load_returns_world_and_robot_at_configured_start_position():
    world, robot = load("sequence_path")

    assert robot._actor in world.actors
    assert robot._actor.position == (1, 1)


def test_load_accepts_explicit_position_overriding_config():
    world, robot = load("sequence_path", position=(2, 2))

    assert robot._actor.position == (2, 2)


def test_load_defaults_to_origin_when_no_start_position():
    world, robot = load("basic")

    assert robot._actor.position == (0, 0)


def test_load_accepts_robot_config_and_debug_override():
    world, robot = load("basic", "blue", debug=True)

    assert world.debug is True
    assert robot._actor.robot_config.name == "blue"


@pytest.mark.network
def test_load_reads_start_position_from_json_url():
    world, robot = load(
        f"{REMOTE_WORLDS_BASE_URL}/01-sequences/sequence_01_straight_line.json"
    )

    assert robot._actor.position == (1, 1)


def test_is_solved_normalizes_float_positions_to_int():
    config = WorldConfig(
        name="float-pos",
        columns=4,
        rows=2,
        start_position=(0, 0),
        target=TargetConfig(robot_position=(3, 0), robot_steps=3),
        robot_abilities=frozenset({"step"}),
    )
    world = load_world(config)
    robot = load_robot(world=world, position=(0, 0))

    robot.step()
    robot.step()
    robot.step()

    assert robot._actor.position == (3, 0)
    assert isinstance(world._robot_positions()[0][0], int)
    assert world.is_solved() is True


def test_is_solved_compares_object_state_across_two_kinds():
    config = WorldConfig(
        name="two-kinds",
        columns=5,
        rows=2,
        start_position=(0, 0),
        objects=(
            ObjectConfig("tree", (2, 0)),
            ObjectConfig("leaf", (3, 0)),
        ),
        target=TargetConfig(
            objects=(
                ObjectConfig("tree", (2, 0)),
                ObjectConfig("leaf", (3, 0)),
            )
        ),
    )
    world = load_world(config)

    assert world.is_solved() is True


def test_is_solved_detects_missing_object_in_target():
    config = WorldConfig(
        name="missing-obj",
        columns=5,
        rows=2,
        start_position=(0, 0),
        objects=(
            ObjectConfig("tree", (2, 0)),
            ObjectConfig("leaf", (3, 0)),
        ),
        target=TargetConfig(
            objects=(
                ObjectConfig("tree", (2, 0)),
            )
        ),
    )
    world = load_world(config)

    assert world.is_solved() is False
