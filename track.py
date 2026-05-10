from __future__ import annotations
from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from cubes import Cube
    from race import Race

# --- Pads --- #


class Pad:
    def __init__(self, index: int):
        self.id = index
        self.cubes: list[Cube] = []

    def __repr__(self):
        return f"[{self.id}]: " + " > ".join(c.__class__.__name__ for c in self.cubes)

    def clear(self):
        """Remove all cubes from this pad"""
        self.cubes.clear()

    def on_turn_start(self, race: Race):
        """Trigger: At the start of each turn"""
        pass

    def on_land(self, cube: Cube, race: Race):
        """Trigger: When a cube lands on this pad"""
        pass

    def on_turn_end(self, race: Race):
        """Trigger: At the end of each turn"""
        pass


class ThrusterPad(Pad):
    """
    A Cube that ends its move on this pad is propelled
    forward to the next pad.
    """

    def on_land(self, cube: Cube, race: Race):
        race.move_cube_with_steps(cube, 1)


class BlockerPad(Pad):
    """
    A Cube that ends its move on this pad is knocked back
    to the previous pad.
    """

    def on_land(self, cube: Cube, race: Race):
        race.move_cube_with_steps(cube, -1)


class SpatialRiftPad(Pad):
    """
    A Cube that ends its move on this pad will be sucked
    into a spatial rift, then fall down to this pad again,
    randomizing the stack order.
    """

    def on_land(self, cube: Cube, race: Race):
        random.shuffle(self.cubes)


# --- Track --- #


class Track:
    def __init__(self, pads: list[Pad]):
        self.pads: list[Pad] = pads

    @classmethod
    def create(cls, length: int, custom_pads: list[Pad] | None = None) -> Track:
        pads = [Pad(i) for i in range(length)]
        custom_pads = custom_pads or []

        for pad in custom_pads:
            pads[pad.id] = pad

        return cls(pads)

    @property
    def length(self) -> int:
        return len(self.pads)

    def reset(self):
        """Clear all cubes from the track and reset pad states"""
        for pad in self.pads:
            pad.clear()

    def validate(self):
        """Validate track configuration (e.g. no duplicate pad ids, all pad ids within track length)"""
        pass
