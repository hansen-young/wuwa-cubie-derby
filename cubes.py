from __future__ import annotations
import random


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
    
    def on_move(self, steps: int, move_orders: list[Cube], positions: list[list[Cube]]):
        """ Trigger: When current cube moves """
        
        cube_idx = positions[self.position].index(self)
        cubes_to_move = positions[self.position][cube_idx:]
        cubes_remaining = positions[self.position][:cube_idx]
        destination = min(self.track_length, self.position + steps) % self.track_length

        positions[destination] += cubes_to_move
        positions[self.position] = cubes_remaining

        for c in cubes_to_move:
            c_steps = (destination - c.position) % self.track_length
            c.forward(c_steps)

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

    # nb: last to move means, ranked last in position not move orders
    #     (shown in group_a_gs2)

    def before_move(self, steps, move_orders, positions):
        ranks = compute_ranks(move_orders, positions)

        if ranks[-1][2] == self:
            steps += 3        
        return steps
    

class Camellya(Cube):
    """
    There is a 50% chance of triggering this effect on Camellya's turn. For every other Cube
    on the same pad besides Camellya, she advances 1 extra pad, while other Cubes stay in place.
    """

    def reset(self):
        super().reset()
        self.p = 0.5

    def before_move(self, steps, move_orders, positions):
        if random.random() <= self.p:
            extra_steps = len(positions[self.position]) - 1
            steps += extra_steps

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

    def on_move(self, steps, move_orders, positions):
        super().on_move(steps, move_orders, positions)

        if not self.skill_triggered:
            carry_forward: list[Cube] = []
            original_position = (self.position - steps) % self.track_length
            
            for p in range(original_position, self.position):
                if positions[p]:
                    self.skill_triggered = True
                    carry_forward += positions[p]
                    positions[p].clear()
                    break
            
            for c in carry_forward:
                c_steps = (self.position - c.position) % self.track_length
                c.forward(c_steps)
            
            idx = positions[self.position].index(self)
            positions[self.position][idx:idx] = carry_forward


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
        self.p = 0.6

    def before_move(self, steps, move_orders, positions):
        if self.skill_triggered:
            steps += 2
        return steps
    
    def after_move(self, cube, steps, move_orders, positions):
        if cube == self and not self.skill_triggered:
            ranks = compute_ranks(move_orders, positions)

            if ranks[-1][2] == self and random.random() <= self.p:
                self.skill_triggered = True
        

class Changli(Cube):
    """
    If other Cubes are stacked below Changli, there is a 65% chance she will be the last to
    move in the next turn.
    """

    def reset(self):
        super().reset()
        self.p = 0.65

    def on_round_start(self, move_orders: list[Cube], positions: list[list[Cube]]):
        has_cube_below = positions[self.position][0] != self

        if has_cube_below and random.random() <= self.p:
            move_orders.remove(self)
            move_orders.append(self)


class Jinhsi(Cube):
    """
    If other Cubes are stacked on top of Jinhsi, there is a 40% chance she will move to the
    top of the stack.
    """

    def reset(self):
        super().reset()
        self.p = 0.4

    def after_move(self, cube, steps, move_orders, positions):
        if cube.position == self.position and random.random() <= self.p:
            positions[self.position].remove(self)
            positions[self.position].append(self)


class Phoebe(Cube):
    """
    There is a 50% chance to advance an extra pad
    """

    def reset(self):
        super().reset()
        self.p = 0.5

    def before_move(self, steps, move_orders, positions):
        if random.random() <= self.p:
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
        self.p = 0.4
        self.extra_steps = 0

    def roll(self):
        return random.choice([1, 3])
    
    def on_move(self, steps, move_orders, positions):
        steps += self.extra_steps
        self.extra_steps = 0
        super().on_move(steps, move_orders, positions)
    
    def after_move(self, cube, steps, move_orders, positions):
        is_stacking = (
            cube.position == self.position and
            positions[cube.position].index(cube) < positions[cube.position].index(self)
        )

        if is_stacking and random.random() <= self.p:
            self.extra_steps += 2


def compute_ranks(cubes: list[Cube], positions: list[list[Cube]]):
    ranks: list[tuple[int, int, Cube]] = []

    for cube in cubes:
        ranks.append((cube.steps + cube.offset, positions[cube.position].index(cube), cube))
    
    ranks.sort(reverse=True)
    return ranks
