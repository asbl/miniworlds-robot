# miniworlds-robot

`miniworlds-robot` is a small extension library for miniworlds. It provides
robot worlds with a restricted, configuration-driven API for learners.

The library builds everything from miniworlds worlds and actors. It does not
load pygame sprites or expose pygame primitives.

The package is intentionally kept separate from the miniworlds core package so
it can later live in its own repository and be published on PyPI.

## Example

```python
from miniworlds_robot import Loader

world = Loader.load_world("basic")
robot = Loader.load_robot("standard", world, position=(1, 1))

robot.step()
robot.turn_left()

print(world.is_solved())
world.run()
```

Worlds can also be loaded from JSON URLs, including GitHub `blob` links:

```python
from miniworlds_robot import load_robot, load_world

world = load_world(
    "https://github.com/USER/miniworlds-robot-worlds/blob/main/worlds/loop_square.json"
)
robot = load_robot(world=world, position=(1, 1))
```
