from __future__ import annotations
import random
import pickle

from tqdm import tqdm


class Cube:
    def __init__(self, offset: int = 0, track_length: int = 20):
        self.name = self.__class__.__name__
        self.steps: int = 0
        self.position: int = 0
        self.offset: int = offset
        self.track_length: int = track_length

    def forward(self, steps: int):
        self.steps += steps
        self.position = (self.position + steps) % self.track_length

    def reset(self):
        self.steps = 0
        self.position = self.offset % self.track_length

    def roll(self) -> int:
        """ Base roll value of cube before any skill is triggered """
        return random.randint(1, 3)

    def on_round_start(self, move_orders: list[Cube], positions: list[list[Cube]]):
        """ Trigger: When a new round starts """
        pass

    def before_move(self, steps: int, move_orders: list[Cube], positions: list[list[Cube]]) -> int:
        """ Trigger: Before current cube moves """
        return steps

    def after_move(self, cube: Cube, steps: int,  move_orders: list[Cube], positions: list[list[Cube]]):
        """ Trigger: After each cube moves """
        pass


class Brant(Cube):
    """
    If Brant is the first to move, he advances 2 extra
    pads.
    """

    def before_move(self, steps, move_orders, positions):
        if move_orders[0] == self:
            steps += 2
        return steps


class Calcharo(Cube):
    """
    If Calcharo is the last to move, he advances 3 extra pads.
    """

    def before_move(self, steps, move_orders, positions):
        if move_orders[-1] == self:
            steps += 3
        return steps
    

class Camellya(Cube):
    """
    There is a 50% chance of triggering this effect on Camellya's turn. For every other Cube
    on the same pad besides Camellya, she advances 1 extra pad, while other Cubes stay in place.
    """

    def before_move(self, steps, move_orders, positions):
        if random.random() <= 0.5:
            extra_steps = len(positions[self.position]) - 1
            steps += extra_steps

            # Move Camellya to the top of stack
            positions[self.position].remove(self)
            positions[self.position].append(self)
        
        return steps
    

class Cantarella(Cube):
    """
    The first time Cantarella passes by other Cubes, she stacks with them
    and carries them forward. This can only be triggered once per match.
    """

    def reset(self):
        super().reset()
        self.skill_triggered = False

    def after_move(self, cube, steps, move_orders, positions):
        carry_forward: list[Cube] = []

        if cube == self and not self.skill_triggered:
            for i in range(steps):
                pi = self.position - i - 1

                if positions[pi]:
                    self.skill_triggered = True
                    carry_forward += positions[pi]
                    positions[pi].clear()
                
            for c in carry_forward:
                c_steps = (self.position - c.position) % len(positions)
                c.forward(c_steps)
            
            self_posidx = positions[self.position].index(self)
            carry_forward += positions[self.position][self_posidx:]
            del positions[self.position][self_posidx:]
            positions[self.position] += carry_forward


class Carlotta(Cube):
    """
    There is a 28% chance to advance twice with the rolled number.
    """

    def before_move(self, steps, move_orders, positions):
        if random.random() <= 0.28:
            steps *= 2
        return steps


class Cartethyia(Cube):
    """
    If ranked last after own action, there is a 60% chance to advance 2 extra
    pads in all remaining turns. This can only be triggered once in each 
    match.
    """

    def reset(self):
        super().reset()
        self.skill_triggered = False

    def before_move(self, steps, move_orders, positions):
        if self.skill_triggered:
            steps += 2
        return steps
    
    def after_move(self, cube, steps, move_orders, positions):
        ranks = compute_ranks(move_orders, positions)

        if cube == self and ranks[-1][2] == self and random.random() <= 0.6:
            self.skill_triggered = True
        

class Changli(Cube):
    """
    If other Cubes are stacked below Changli, there is a 65% chance she will be the last to
    move in the next turn.
    """

    def on_round_start(self, move_orders: list[Cube], positions: list[list[Cube]]):
        has_cube_below = positions[self.position][0] != self

        if has_cube_below and random.random() <= 0.65:
            move_orders.remove(self)
            move_orders.append(self)


class Jinhsi(Cube):
    """
    If other Cubes are stacked on top of Jinhsi, there is a 40% chance she will move to the
    top of the stack.
    """

    def after_move(self, cube, steps, move_orders, positions):
        if cube.position == self.position and random.random() <= 0.4:
            positions[self.position].remove(self)
            positions[self.position].append(self)


class Phoebe(Cube):
    """
    There is a 50% chance to advance an extra pad
    """

    def before_move(self, steps, move_orders, positions):
        if random.random() <= 0.5:
            steps += 1
        return steps


class Roccia(Cube):
    """
    If Roccia is the last to move, she advances 2 extra 
    pads.
    """

    def before_move(self, steps, move_orders, positions):
        if move_orders[-1] == self:
            steps += 2
        return steps
    

class Shorekeeper(Cube):
    """
    The dice will only roll 2 or 3.
    """

    def roll(self):
        return random.randint(2, 3)


class Zani(Cube):
    """
    The dice will only roll a 1 or 3. When moving with other Cubes stacking
    above, there is a 40% chance to advance 2 extra pads next turn.
    """

    def reset(self):
        super().reset()
        self.trigger_skill = False

    def roll(self):
        return random.choice([1, 3])

    def before_move(self, steps, move_orders, positions):
        if self.trigger_skill:
            steps += 2
            self.trigger_skill = False
        return steps
    
    def after_move(self, cube, steps, move_orders, positions):
        if self == cube and positions[cube.position][-1] != self and random.random() <= 0.4:
            self.trigger_skill = True



class Game:
    def __init__(self, cubes: list[Cube], track_length: int = 20):
        self.cubes: list[Cube] = cubes
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

    def shuffle_move_orders(self):
        random.shuffle(self.cubes)
    
    def initialize_state(self):
        self.winner = None
        self.positions = [[] for _ in range(self.track_length)]

        for c in self.cubes:
            c.track_length = self.track_length
            c.reset()
            self.positions[c.position].append(c)

    def check_winner(self):
        """
        If multiple cubes finished at the same time, the cube on the top of the stack wins.
        """
        for cube in self.positions[0][::-1]:
            if cube.steps + cube.offset >= self.track_length:
                self.winner = cube
                break

    def move(self, cube: Cube, steps: int):
        cube_idx = self.positions[cube.position].index(cube)
        cubes_to_move = self.positions[cube.position][cube_idx:]
        cubes_remaining = self.positions[cube.position][:cube_idx]
        destination = min(self.track_length, cube.position + steps) % self.track_length

        self.positions[destination] += cubes_to_move
        self.positions[cube.position] = cubes_remaining

        for c in cubes_to_move:
            c_steps = (destination - c.position) % self.track_length
            c.forward(c_steps)

    def start(self):
        self.initialize_state()

        while self.winner is None:
            self.shuffle_move_orders()

            for c in self.cubes:
                c.on_round_start(self.cubes, self.positions)

            for c in self.cubes:
                steps = c.roll()
                steps = c.before_move(steps, self.cubes, self.positions)
                self.move(c, steps)

                for cx in self.cubes:
                    cx.after_move(c, steps, self.cubes, self.positions)

                self.check_winner()

                if self.winner:
                    break

        return compute_ranks(self.cubes, self.positions)


def compute_ranks(cubes: list[Cube], positions: list[list[Cube]]):
    ranks: list[tuple[int, int, Cube]] = []

    for cube in cubes:
        ranks.append((cube.position, positions[cube.position].index(cube), cube))
    
    ranks.sort(reverse=True)
    return ranks


if __name__ == "__main__":

    # --- Match Configuration --- #

    track_length = 24

    # match_name = "group_a_gs1"
    # cubes: list[Cube] = [Calcharo(), Camellya(), Carlotta(), Changli(), Jinhsi(), Shorekeeper()]

    # match_name = "group_a_qf1"
    # cubes: list[Cube] = [Calcharo(), Camellya(), Changli(), Shorekeeper()]

    match_name = "group_b_gs1"
    cubes: list[Cube] = [Brant(), Cantarella(), Cartethyia(), Phoebe(), Roccia(), Zani()]

    # --- Game Simulation --- #

    game = Game(cubes, track_length)
    win_counts = {c: 0 for c in cubes}
    sum_ranks = {c: 0 for c in cubes}
    rank_history = {c.name: [] for c in cubes}

    num_rounds = 100000

    for _ in tqdm(range(num_rounds)):
        ranks = game.start()

        winner = ranks[0][-1]
        win_counts[winner] += 1

        for pos, (_, _, cube) in enumerate(ranks):
            sum_ranks[cube] += pos + 1
            rank_history[cube.name].append(pos + 1)

    print("Win Probability:")
    for c, win in win_counts.items():
        print(f"{c.name}: {win/num_rounds:.3f}")

    print("\nAverage Rank:")
    for c, ranks in sum_ranks.items():
        print(f"{c.name}: {ranks/num_rounds:.3f}")

    with open(f"{match_name}_history.pkl", "wb") as fp:
        pickle.dump(rank_history, fp)
