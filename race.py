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

    def move_cube_with_steps(self, cube: Cube, steps: int):
        print(f"{cube.__class__.__name__} moves {steps}.")
        p = cube.relative_position(self.track.length)
        i = self.track.pads[p].cubes.index(cube)

        destination = max(0, min(cube.progress + steps, self.max_progress))
        destination_p = destination % self.track.length
        steps = destination - cube.progress

        cubes_to_move = self.track.pads[p].cubes[i:]
        cubes_remaining = self.track.pads[p].cubes[:i]

        for c in cubes_to_move:
            c.progress += steps

        self.track.pads[p].cubes = cubes_remaining
        self.track.pads[destination_p].cubes += cubes_to_move
        self.track.pads[destination_p].on_land(cube, self)

    def move_cube(self, cube: Cube):
        self.move_cube_with_steps(cube, cube.steps)

    def push_cube(self, cube: Cube, position: int):
        self.track.pads[position].push(cube)

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
            if cube.progress == self.max_progress:
                return cube

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
