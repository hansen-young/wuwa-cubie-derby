from __future__ import annotations
from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from race import Race


class Cube:
    """
    Attributes:
        offset: Starting position of the cube on the track. Default is 0.
        steps: Number of steps the cube will move in the current turn.
        progress: Total number of steps the cube has moved from the track's starting line.
    """

    def __init__(self, offset: int = 0):
        self.offset: int = offset
        self.steps: int = 0
        self.progress: int = 0

    def relative_position(self, track_length: int) -> int:
        """Get the cube's current position on the track relative to the starting line."""
        return self.progress % track_length

    def reset(self):
        self.steps = 0
        self.progress = self.offset

    def roll(self):
        """Base roll value of cube before any skill is triggered"""
        pass

    def on_turn_start(self, race: Race):
        """Trigger: At the start of each turn"""
        pass

    def on_before_move(self, race: Race):
        """Trigger: Before current cube moves"""
        pass

    def on_after_move(self, race: Race):
        """Trigger: After current cube moves"""
        pass

    def on_turn_end(self, race: Race):
        """Trigger: At the end of each turn"""
        pass


class Phoebe(Cube):
    """
    There is a 50% chance to advance an extra pad
    """

    p: float = 0.5

    def on_before_move(self, race: Race):
        self.steps += int(random.random() < self.p)


class Shorekeeper(Cube):
    """
    The dice will only roll 2 or 3.
    """

    def roll(self):
        self.steps = random.randint(2, 3)
