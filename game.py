from __future__ import annotations
import pickle
from dataclasses import dataclass

from tqdm import tqdm
from cubes import *


class Game:
    def __init__(self, start_position: list[Cube], start_move_order: list[int] | None = None, track_length: int = 20):
        self.__start_position: list[Cube] = start_position
        self.__start_move_order: list[int] | None = start_move_order

        self.cubes: list[Cube] = []
        self.positions: list[list[Cube]] = []
        self.track_length: int = track_length
        self.winner: Cube | None = None

    # --- Utilities --- #

    def show_positions(self):
        for i, position in enumerate(self.positions):
            print(f"Pad {i:<2}: ", end="")
            for c in position:
                print(c.name, end=" ")
            print()


    # --- Game Logic --- #

    def decide_move_orders(self):
        """
        During a match, dice rolls decide which Cube move first.
        """
        self.cubes.sort(key=lambda c: c.roll(), reverse=True)
    
    def initialize_state(self):
        self.winner = None
        self.positions = [[] for _ in range(self.track_length)]

        for c in self.__start_position:
            c.track_length = self.track_length
            c.reset()
            self.positions[c.position].append(c)

        if self.__start_move_order:
            move_orders = sorted(zip(self.__start_move_order, self.__start_position))
            self.cubes = [c for _, c in move_orders]
        else:
            self.cubes = self.__start_position.copy()
            self.decide_move_orders()

    def check_winner(self):
        """
        If multiple cubes finished at the same time, the cube on the top of the stack wins.
        """
        for cube in self.positions[0][::-1]:
            if cube.steps + cube.offset >= self.track_length:
                self.winner = cube
                break

    def start(self):
        rolls: dict[Cube, int] = {}
        self.initialize_state()

        while self.winner is None:
            # Prepare Phase
            for c in self.cubes:
                rolls[c] = c.roll()

            for c in self.cubes.copy():
                c.on_round_start(self.cubes, self.positions)

            # Move Phase
            for c in self.cubes.copy():
                rolls[c] = c.before_move(rolls[c], self.cubes, self.positions)
                c.on_move(rolls[c], self.cubes, self.positions)

                for cx in self.cubes:
                    cx.after_move(c, rolls[c], self.cubes, self.positions)

                self.check_winner()

                if self.winner:
                    break
            
            # Clean Up Phase
            self.decide_move_orders()

        return compute_ranks(self.cubes, self.positions)


@dataclass
class MatchSetup:
    match_name: str
    start_position: list[Cube]
    start_move_order: list[int] | None = None
    track_length: int = 24
    num_simulations: int = 100


def run_simulation(setup: MatchSetup):
    game = Game(setup.start_position, setup.start_move_order, setup.track_length)
    win_counts = {c: 0 for c in setup.start_position}
    sum_ranks = {c: 0 for c in setup.start_position}
    rank_history = {c.name: [] for c in setup.start_position}

    for _ in tqdm(range(setup.num_simulations)):
        ranks = game.start()

        winner = ranks[0][-1]
        win_counts[winner] += 1

        for pos, (_, _, cube) in enumerate(ranks):
            sum_ranks[cube] += pos + 1
            rank_history[cube.name].append(pos + 1)

    with open(f"{setup.match_name}_history.pkl", "wb") as fp:
        pickle.dump(rank_history, fp)


if __name__ == "__main__":

    # --- Match Configuration --- #

    setups = [
        # MatchSetup(
        #     match_name="group_a_gs1",
        #     start_position=[Jinhsi(), Calcharo(), Changli(), Shorekeeper(), Carlotta(), Camellya()],
        #     start_move_order=[5, 4, 3, 2, 1, 0],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_a_gs2",
        #     start_position=[Jinhsi(0), Carlotta(-1), Calcharo(-1), Shorekeeper(-2), Camellya(-2), Changli(-3)],
        #     start_move_order=None,
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_a_gs2_w_order",
        #     start_position=[Jinhsi(0), Carlotta(-1), Calcharo(-1), Shorekeeper(-2), Camellya(-2), Changli(-3)],
        #     start_move_order=[5, 1, 0, 2, 3, 4],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_b_gs1",
        #     start_position=[Cantarella(), Roccia(), Zani(), Cartethyia(), Phoebe(), Brant()],
        #     start_move_order=[5, 4, 3, 2, 1, 0],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_b_gs2",
        #     start_position=[Brant(0), Phoebe(-1), Zani(-1), Roccia(-2), Cartethyia(-2), Cantarella(-3)],
        #     start_move_order=None,
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_b_gs2_w_order",
        #     start_position=[Brant(0), Phoebe(-1), Zani(-1), Roccia(-2), Cartethyia(-2), Cantarella(-3)],
        #     start_move_order=[4, 1, 2, 3, 5, 0],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_a_qf1",
        #     start_position=[Calcharo(), Changli(), Shorekeeper(), Camellya()],
        #     start_move_order=None,
        #     track_length=24,
        #     num_simulations=1000000
        # ),
        # MatchSetup(
        #     match_name="group_a_qf1_w_order",
        #     start_position=[Calcharo(), Changli(), Shorekeeper(), Camellya()],
        #     start_move_order=[3, 1, 2, 0],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_a_qf2",
        #     start_position=[Calcharo(0), Changli(-1), Shorekeeper(-1), Camellya(-2)],
        #     start_move_order=None,
        #     track_length=24,
        #     num_simulations=1000000
        # ),
        # MatchSetup(
        #     match_name="group_a_qf2_w_order",
        #     start_position=[Calcharo(0), Changli(-1), Shorekeeper(-1), Camellya(-2)],
        #     start_move_order=[3, 1, 0, 2],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_b_qf1",
        #     start_position=[Phoebe(), Cartethyia(), Cantarella(), Zani()],
        #     start_move_order=None,
        #     track_length=24,
        #     num_simulations=1000000
        # ),
        # MatchSetup(
        #     match_name="group_b_qf1_w_order",
        #     start_position=[Phoebe(), Cantarella(), Zani(), Cartethyia(),],
        #     start_move_order=[3, 2, 1, 0],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        # MatchSetup(
        #     match_name="group_b_qf2",
        #     start_position=[Cantarella(-2), Cartethyia(-1), Zani(-1), Phoebe(0)],
        #     start_move_order=None,
        #     track_length=24,
        #     num_simulations=1000000
        # ),
        # MatchSetup(
        #     match_name="group_b_qf2_w_order",
        #     start_position=[Cantarella(-2), Cartethyia(-1), Zani(-1), Phoebe(0)],
        #     start_move_order=[2, 0, 1, 3],
        #     track_length=24,
        #     num_simulations=500000
        # ),
        MatchSetup(
            match_name="f1",
            start_position=[Shorekeeper(), Camellya(), Cartethyia(), Cantarella()],
            start_move_order=None,
            track_length=24,
            num_simulations=1000000
        )
    ]

    # --- Game Simulation --- #

    for setup in setups:
        run_simulation(setup)
    