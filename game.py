from __future__ import annotations
import random
import pickle


class Cube:
    def __init__(self):
        self.name = self.__class__.__name__
        self.position: int = 0

    def reset(self):
        self.position = 0

    def roll(self) -> int:
        """ Base roll value of cube before any skill is triggered """
        return random.randint(1, 3)

    def on_round_start(self, move_orders: list[Cube], positions: list[list[Cube]]):
        """ Trigger: When a new round starts """
        pass

    def before_move(self, steps: int, move_orders: list[Cube], positions: list[list[Cube]]) -> int:
        """ Trigger: Before current cube moves """
        return steps

    def post_move(self, cube: Cube, steps: int,  move_orders: list[Cube], positions: list[list[Cube]]):
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

    def __init__(self):
        super().__init__()
        self.skill_triggered = False

    def reset(self):
        super().reset()
        self.skill_triggered = False

    def post_move(self, cube, steps, move_orders, positions):
        carry_forward: list[Cube] = []

        if cube == self:
            for i in range(steps):
                pi = self.position - i - 1

                if positions[pi]:
                    self.skill_triggered = True
                    carry_forward += positions[pi]
                    positions[pi].clear()
                
            for c in carry_forward:
                c.position = self.position
            
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

    def __init__(self):
        super().__init__()
        self.skill_triggered = False

    def reset(self):
        super().reset()
        self.skill_triggered = False

    def before_move(self, steps, move_orders, positions):
        if self.skill_triggered:
            steps += 2
        return steps
    
    def post_move(self, cube, steps, move_orders, positions):
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

    def post_move(self, cube, steps, move_orders, positions):
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

    def __init__(self):
        super().__init__()
        self.trigger_skill = False

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
    
    def post_move(self, cube, steps, move_orders, positions):
        if self == cube and positions[cube.position][-1] != self and random.random() <= 0.4:
            self.trigger_skill = True

class Game:
    def __init__(self, cubes: list[Cube]):
        self.cubes: list[Cube] = cubes
        self.positions: list[list[Cube]] = []
        self.winner: Cube | None = None

    def shuffle_move_orders(self):
        random.shuffle(self.cubes)
    
    def initialize_state(self, track_length: int = 20):
        """
        At turn 1, the move is ordered based on the reversed cube stack.
        """
        self.winner = None
        self.shuffle_move_orders()
        self.positions = [[] for _ in range(track_length)]
        self.positions[0] = [c for c in self.cubes[::-1]]

        for c in self.cubes:
            c.reset()

    def check_winner(self):
        """
        If multiple cubes finished at the same time, the cube on the top of the stack wins.
        """
        if self.positions[-1]:
            self.winner = self.positions[-1][-1]

    def move(self, cube: Cube, steps: int):
        cube_idx = self.positions[cube.position].index(cube)
        cubes_to_move = self.positions[cube.position][cube_idx:]
        cubes_remaining = self.positions[cube.position][:cube_idx]

        final_pad = len(self.positions) - 1
        destination = max(final_pad, cube.position + steps)

        self.positions[destination] += cubes_to_move
        self.positions[cube.position] = cubes_remaining

        for c in cubes_to_move:
            c.position = destination

    def start(self, track_length: int = 20):
        self.initialize_state(track_length)

        while self.winner is None:
            self.shuffle_move_orders()

            for c in self.cubes:
                c.on_round_start(self.cubes, self.positions)

            for c in self.cubes:
                steps = c.roll()
                steps = c.before_move(steps, self.cubes, self.positions)
                self.move(c, steps)

                for cx in self.cubes:
                    cx.post_move(c, steps, self.cubes, self.positions)

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
    track_length = 20

    # match_name = "group_a_gs1"
    # cubes: list[Cube] = [Calcharo(), Camellya(), Carlotta(), Changli(), Jinhsi(), Shorekeeper()]

    # match_name = "group_a_qf1"
    # cubes: list[Cube] = [Calcharo(), Camellya(), Changli(), Shorekeeper()]

    match_name = "group_b_gs1"
    cubes: list[Cube] = [Brant(), Cantarella(), Cartethyia(), Phoebe(), Roccia(), Zani()]

    game = Game(cubes)
    win_counts = {c: 0 for c in cubes}
    sum_ranks = {c: 0 for c in cubes}
    rank_history = {c.name: [] for c in cubes}

    num_rounds = 5000000

    for _ in range(num_rounds):
        ranks = game.start(track_length)

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
