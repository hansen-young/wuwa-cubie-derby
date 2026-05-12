from __future__ import annotations
from typing import TYPE_CHECKING
import itertools
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

    rankable: bool = True

    def __init__(self, offset: int = 0):
        self.offset: int = offset
        self.base_roll: int = 0
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
        self.base_roll = random.randint(1, 3)
        self.steps = self.base_roll

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
        """Trigger: When this cube lands on a pad"""
        pass

    def on_encounter(self, race: Race, other: Cube):
        """Trigger: When this cube newly shares a pad with another cube during movement."""
        pass


class Abbowser(Cube):
    """
    In the 3rd turn, Abbowser Cube starts moving from the finish line to the starting
    line. Abbowser Cube does not stack with other Cubes before it starts moving. Once
    it's moving, it is also affected by all mechanisms along the course. Abbowser Cube
    rolls from 1-6, always ends up at the bottom of the stack. If Abbowser is separated
    from all other Cubes at the end of each turn, it teleports back to the finish line.
    """

    rankable: bool = False

    def roll(self):
        self.base_roll = -random.randint(1, 6)
        self.steps = self.base_roll

    def on_turn_start(self, race: Race):
        if race.turn < 3:
            self.steps = 0

    def on_enter_pad(self, race: Race, final_step: bool = False):
        p, i = race.locate_cube(self)
        race.track.pads[p].cubes.pop(i)
        race.track.pads[p].cubes.insert(0, self)

    def on_turn_end(self, race: Race):
        p, i = race.locate_cube(self)

        if len(race.track.pads[p].cubes) > 1:
            return

        relative_rankings = sorted(
            race.cubes,
            key=lambda c: c.relative_position(race.track.length),
            reverse=True,
        )

        if relative_rankings[-1] == self:
            race.remove_cube(self, p)
            race.insert_cube(self, self.offset, 0)


class Aemeath(Cube):
    """
    When this Cube reaches the course's midpoint, it teleports on top of the closest
    Cube (if that Cube is not Abbowser). This can be triggered only once per match.
    """

    def reset(self):
        super().reset()
        self.skill_triggered: bool = False

    # nb: CN translation "if there is non-Abbowser Cube in front of it"
    def on_turn_end(self, race: Race):
        if self.skill_triggered:
            return

        p = self.relative_position(race.track.length)

        if p > race.track.length / 2 - 1:
            rankings = race.compute_rankings()
            i = rankings.index(self)

            for o in range(i - 1, -1, -1):
                if not isinstance(rankings[o], Abbowser):
                    race.remove_cube(self, p)
                    race.push_cube(self, rankings[o].progress)
                    self.skill_triggered = True
                    break


class Augusta(Cube):
    """
    When at the top of a stack at the start of the turn, this Cube stays still this
    turn and becomes the last to move next turn.
    """

    def on_turn_start(self, race: Race):
        p = self.relative_position(race.track.length)

        if race.track.pads[p].cubes[-1] == self:
            self.steps = 0
            race.cubes_order_next_turn.remove(self)
            race.cubes_order_next_turn.append(self)


class Brant(Cube):
    """
    If Brant is the first to move, he advances 2 extra pads.
    """


class Calcharo(Cube):
    """
    If Calcharo is in last place when he starts moving, he advances 3 extra pads.
    """

    def on_before_move(self, race: Race):
        rankings = race.compute_rankings()

        if rankings[-1] == self:
            self.steps += 3


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

    p: float = 0.28

    def on_before_move(self, race: Race):
        if random.random() < self.p:
            self.steps *= 2


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


class Chisa(Cube):
    """
    If this turn's roll is the lowest among all Cubes, this Cube advances 2 extra pads.
    """

    def on_turn_start(self, race: Race):
        # nb: CN translation "if roll is one of the smallest value in this round"
        lowest = min(c.base_roll for c in race.cubes)

        if self.base_roll == lowest:
            self.steps += 2


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

    def reset(self):
        super().reset()
        self.extra_step = 0

    def on_before_move(self, race: Race):
        self.steps += self.extra_step

    def on_encounter(self, race: Race, other: Cube):
        if isinstance(other, Abbowser):
            self.extra_step += 1


class Jinhsi(Cube):
    """
    If other Cubes are stacked on top of Jinhsi, there is a 40% chance she will move to the
    top of the stack.
    """

    p: float = 0.4

    def on_before_move(self, race: Race):
        # nb: trigger is unclear whether on_encounter / on_turn_start / on_before_move
        p, i = race.locate_cube(self)

        if race.track.pads[p].cubes[-1] != self:
            if random.random() < self.p:
                race._ranking_cache = None
                race.track.pads[p].cubes.pop(i)
                race.track.pads[p].cubes.append(self)


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


class Lynae(Cube):
    """
    For each turn, there is a 60% chance to advance by a doubled number,
    but also a 20% chance to stay still.
    """

    p_double: float = 0.6
    p_stop: float = 0.2

    def on_turn_start(self, race: Race):
        if random.random() < self.p_double:
            self.steps *= 2
        elif random.random() < self.p_double + self.p_stop:
            self.steps = 0


class Mornye(Cube):
    """
    The dice is set to roll 3, 2, and 1 in succession.
    """

    def reset(self):
        super().reset()
        self.dice_generator = itertools.cycle([1, 2, 3])

    def roll(self):
        # nb: we assume dice roll for deciding move order consumes the generator
        #     3 (roll) -> 1 (move order) -> 2 (roll) -> 3 (move order) -> 1 (roll)
        self.base_roll = next(self.dice_generator)
        self.steps = self.base_roll


class Phoebe(Cube):
    """
    There is a 50% chance to advance an extra pad
    """

    p: float = 0.5

    def on_before_move(self, race: Race):
        self.steps += int(random.random() < self.p)


class Phrolova(Cube):
    """
    When stacked at the bottom at the start of the turn, this Cube advances 3 pad.
    """

    def on_turn_start(self, race: Race):
        p, i = race.locate_cube(self)

        if i == 0:
            self.steps += 3


class Roccia(Cube):
    """
    If Roccia is the last to move, she advances 2 extra pads.
    """

    def on_turn_start(self, race: Race):
        if race.cubes_order_this_turn[-1] == self:
            self.steps += 2


class Shorekeeper(Cube):
    """
    The dice will only roll 2 or 3.
    """

    def roll(self):
        self.base_roll = random.randint(2, 3)
        self.steps = self.base_roll


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
