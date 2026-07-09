# miniworlds-robot

`miniworlds-robot` is a small extension library for miniworlds. It provides
robot worlds with a restricted, configuration-driven API for learners.

The library builds everything from miniworlds worlds and actors. It does not
load pygame sprites or expose pygame primitives.

The package is intentionally kept separate from the miniworlds core package so
it can later live in its own repository and be published on PyPI.

## Robot abilities

Each world activates a subset of the robot API via `robot_abilities`. A robot
only exposes methods that are enabled in its world; calling anything else raises
a clear `AttributeError`.

| Ability       | Method          | Description |
|---------------|-----------------|-------------|
| `step`        | `robot.step()`        | Move one tile forward if the destination is free |
| `turn_left`   | `robot.turn_left()`   | Rotate 90° counter-clockwise |
| `turn_right`  | `robot.turn_right()`  | Rotate 90° clockwise |
| `on_leaf`     | `robot.on_leaf()`     | `True` if the robot shares its tile with a leaf |
| `remove_leaf` | `robot.remove_leaf()` | Remove a leaf on the robot's tile; returns `bool` |
| `can_move`    | `robot.can_move()`    | `True` if the next `step()` would succeed |
| `position`    | `robot.position`      | Current tile as `(column, row)` |

`can_move` lets learners write conditional loops without peeking into the
robot's internals:

```python
while robot.can_move():
    robot.step()
```

## Example

```python
from miniworlds_robot import load

world, robot = load("basic", position=(1, 1))

robot.step()
robot.turn_left()

print(world.is_solved())
world.run()
```

Worlds can also be loaded from JSON URLs, including GitHub `blob` links:

```python
from miniworlds_robot import load

world, robot = load(
    "https://github.com/asbl/miniworlds-robot-worlds/blob/main/worlds/01-sequences/sequence_01_straight_line.json"
)
```
