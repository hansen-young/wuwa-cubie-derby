from __future__ import annotations
from typing import TYPE_CHECKING
import random

from track import BlockerPad, Pad, ThrusterPad

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
        self.steps = random.randint(1, 3)

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

    def on_enter_pad(self, race: Race, final_step: bool = False):
        """Trigger: When current cube lands on a pad"""
        pass


class Abbowser(Cube):
    """
    In the 3rd turn, Abbowser Cube starts moving from the finish line to the starting
    line. Abbowser Cube does not stack with other Cubes before it starts moving. Once
    it's moving, it is also affected by all mechanisms along the course. Abbowser Cube
    rolls from 1-6, always ends up at the bottom of the stack. If Abbowser is separated
    from all other Cubes at the end of each turn, it teleports back to the finish line.
    """


class Brant(Cube):
    """
    If Brant is the first to move, he advances 2 extra pads.
    """


class Calcharo(Cube):
    """
    If Calcharo is the last to move, he advances 3 extra pads.
    """


class Camellya(Cube):
    """
    There is a 50% chance of triggering this effect on Camellya's turn. For every other Cube
    on the same pad besides Camellya, she advances 1 extra pad, while other Cubes stay in place.
    """


class Cantarella(Cube):
    """
    The first time Cantarella passes by other Cubes, she stacks with them and carries them forward.
    This can only be triggered once per match.
    """


class Carlotta(Cube):
    """
    There is a 28% chance to advance twice with the rolled number.
    """


class Cartethyia(Cube):
    """
    If ranked last after own action, there is a 60% chance to advance 2 extra pads in all
    remaining turns. This can only be triggered once in each match.
    """

    p: float = 0.6

    def reset(self):
        super().reset()
        self.skill_triggered: bool = False

    def on_before_move(self, race: Race):
        if self.skill_triggered and random.random() < self.p:
            self.steps += 2

    def on_after_move(self, race: Race):
        if not self.skill_triggered:
            rankings = race.compute_rankings()

            if rankings and rankings[-1] == self:
                self.skill_triggered = True


class Changli(Cube):
    """
    If other Cubes are stacked below Changli, there is a 65% chance she will be the last to
    move in the next turn.
    """


class Denia(Cube):
    """
    If the number rolled matches the previous roll, this Cube advances 2 extra pads.
    """

    def reset(self):
        super().reset()
        self.prev_roll: int = -1

    def on_before_move(self, race: Race):
        extras = 2 if self.steps == self.prev_roll else 0
        self.prev_roll = self.steps
        self.steps += extras


class Hiyuki(Cube):
    """
    Encountering Abbowser Cube causes this Cube to advance by 1 extra pad each turn afterward.
    """


class Jinhsi(Cube):
    """
    If other Cubes are stacked on top of Jinhsi, there is a 40% chance she will move to the
    top of the stack.
    """


class Luuk(Cube):
    """
    Triggering the Thruster pushes this Cube forward by 3 extra pads.
    Triggering the Blocker knocks this Cube back by 1 extra pad.
    """

    def on_enter_pad(self, race: Race, final_step: bool = False):
        if final_step:
            p = race.locate_cube(self)[0]
            pad = race.track.pads[p]

            if isinstance(pad, ThrusterPad):
                race.move_cube_with_steps(self, 4)

            elif isinstance(pad, BlockerPad):
                race.move_cube_with_steps(self, -2)


class Phoebe(Cube):
    """
    There is a 50% chance to advance an extra pad
    """

    p: float = 0.5

    def on_before_move(self, race: Race):
        self.steps += int(random.random() < self.p)


class Roccia(Cube):
    """
    If Roccia is the last to move, she advances 2 extra pads.
    """


class Shorekeeper(Cube):
    """
    The dice will only roll 2 or 3.
    """

    def roll(self):
        self.steps = random.randint(2, 3)


class Sigrika(Cube):
    """
    Up to 2 Cubes right ahead of this Cube at the start of the turn advance
    1 fewer pad this turn (the first roll at the start of the match only
    determines turn order). This effect does not freeze Cubes in place or
    make them go backwards.
    """

    def on_turn_start(self, race: Race):
        # nb: "right ahead" is ambiguous, we assume it is by progress not by relative position.
        rankings = race.compute_rankings()
        i = rankings.index(self)

        for c in rankings[max(0, i - 2) : i]:
            c.steps = max(1, c.steps - 1)


class Zani(Cube):
    """
    The dice will only roll a 1 or 3. When moving with other Cubes stacking
    above, there is a 40% chance to advance 2 extra pads next turn.
    """
