import random

from cubes import Cube
from track import Pad, Track


class Race:
    def __init__(self, track: Track, cubes: list[Cube], laps: int = 1):
        self.track = track
        self.cubes = cubes
        self.laps = laps

        self.turn: int
        self.cubes_order_next_turn: list[Cube]
        self.cubes_order_this_turn: list[Cube]
        self.max_progress: int

        self._ranking_cache: list[Cube] | None = None
        self.reset()

    def __repr__(self):
        return "\n".join(p.__repr__() for p in self.track.pads)

    def reset(self):
        self.track.reset()

        for cube in self.cubes:
            cube.reset()

        for cube in self.cubes:
            self.push_cube(cube, cube.progress)

        self.turn = 0
        self.cubes_order_next_turn = self.decide_move_orders()
        self.cubes_order_this_turn = self.cubes_order_next_turn.copy()
        self.max_progress = self.track.length * self.laps

    # --- Cube Positioning --- #

    def move_cube_single_step_intermediate(self, cube: Cube, forward: bool = True):
        self._ranking_cache = None
        p, i = self.locate_cube(cube)

        steps = 1 if forward else -1
        destination = max(0, min(cube.progress + steps, self.max_progress))
        destination_p = destination % self.track.length
        steps = destination - cube.progress

        cubes_to_move = self.track.pads[p].cubes[i:]
        cubes_remaining = self.track.pads[p].cubes[:i]
        cubes_at_dest = self.track.pads[destination_p].cubes.copy()

        for c in cubes_to_move:
            c.progress += steps

        self.track.pads[p].cubes = cubes_remaining
        self.track.pads[destination_p].cubes += cubes_to_move

        for c_dest in cubes_at_dest:
            for c_move in cubes_to_move:
                c_move.on_encounter(self, c_dest)
                c_dest.on_encounter(self, c_move)

    def move_cube_with_steps(self, cube: Cube, steps: int):
        print(f"{cube.__class__.__name__} moves {steps}.")

        while steps > 0:
            self.move_cube_single_step_intermediate(cube, forward=True)
            cube.on_enter_pad(self, final_step=steps == 1)
            steps -= 1

        while steps < 0:
            self.move_cube_single_step_intermediate(cube, forward=False)
            cube.on_enter_pad(self, final_step=steps == -1)
            steps += 1

        p, i = self.locate_cube(cube)
        self.track.pads[p].on_land(cube, self)

    def move_cube(self, cube: Cube):
        self.move_cube_with_steps(cube, cube.steps)

    def push_cube(self, cube: Cube, position: int):
        self._ranking_cache = None
        self.track.pads[position % self.track.length].cubes.append(cube)
        cube.progress = position

    def remove_cube(self, cube: Cube, position: int):
        self._ranking_cache = None
        self.track.pads[position % self.track.length].cubes.remove(cube)
        cube.progress = 0

    def insert_cube(self, cube: Cube, position: int, index: int):
        self._ranking_cache = None
        self.track.pads[position % self.track.length].cubes.insert(index, cube)
        cube.progress = position

    # --- Race Logic --- #

    def decide_move_orders(self):
        # nb: The move order selection is not clearly defined in the game rules.
        #     However, based on Sigrika's in-game skill descriptions, it appears that
        #     dice roll values are used to select the move order for each turn.
        # nb: We add a random tiebraker to avoid biased orders towards cubes earlier in the list.
        for cube in self.cubes:
            cube.roll()

        return sorted(
            self.cubes, key=lambda c: (c.steps, random.random()), reverse=True
        )

    def find_winner(self) -> Cube | None:
        """
        The cube to reach the end of the track wins.
        If multiple cubes finish at the same time, the cube on the top of the stack wins.
        """

        for cube in self.track.pads[0].cubes[::-1]:
            if cube.rankable and cube.progress == self.max_progress:
                return cube

    def locate_cube(self, cube: Cube):
        """
        Get the cube's current position on the track as a tuple of (pad index, stack index)
        """
        p = cube.relative_position(self.track.length)
        return (p, self.track.pads[p].cubes.index(cube))

    def compute_rankings(self) -> list[Cube]:
        """
        Get the current ranks of all cubes in the race based on their progress.
        If multiple cubes have the same progress, the cube on the top of the stack ranks higher.
        """
        if self._ranking_cache is None:
            self._ranking_cache = sorted(
                [c for c in self.cubes if c.rankable],
                key=lambda c: (c.progress, self.locate_cube(c)[1]),
                reverse=True,
            )
        return self._ranking_cache

    def start_turn(self):
        """
        Start a turn. A turn consists of the following phases:
        1. Generate cubes' base roll values
        2. Trigger on_turn_start for all pads and cubes
        3. Move cubes in order, triggering on_before_move and on_after_move for each cube
        4. Trigger on_turn_end for all pads and cubes
        """

        self.turn += 1
        self.cubes_order_this_turn = self.cubes_order_next_turn
        self.cubes_order_next_turn = self.decide_move_orders()

        for cube in self.cubes_order_this_turn:
            cube.roll()

        for pad in self.track.pads:
            pad.on_turn_start(self)

        for cube in self.cubes_order_this_turn:
            cube.on_turn_start(self)

        for cube in self.cubes_order_this_turn:
            cube.on_before_move(self)
            self.move_cube(cube)
            cube.on_after_move(self)

            if winner := self.find_winner():
                return winner

        for cube in self.cubes_order_this_turn:
            cube.on_turn_end(self)

        for pad in self.track.pads:
            pad.on_turn_end(self)

    def start(self):
        """Start the race"""

        self.reset()

        while not (winner := self.start_turn()):
            pass
        return winner
