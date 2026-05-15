import pickle
from tqdm import tqdm

from race import Race
from track import Track, ThrusterPad, BlockerPad, SpatialRiftPad
from cubes import *

if __name__ == "__main__":
    num_simulation = 100000
    laps: int = 1

    track = Track.create(
        length=32,
        custom_pads=[
            ThrusterPad(4),
            SpatialRiftPad(6),
            ThrusterPad(10),
            SpatialRiftPad(14),
            BlockerPad(16),
            ThrusterPad(20),
            SpatialRiftPad(23),
            BlockerPad(26),
            BlockerPad(30),
        ],
    )
    cubes: list[Cube] = [
        Abbowser(track.length * laps),
        Chisa(1),
        Shorekeeper(1),
        Jinhsi(1),
        Phrolova(1),
        Aemeath(1),
        Hiyuki(1),
    ]
    race = Race(track, cubes, laps)

    # ---

    rank_history = {cube.__class__.__name__: [] for cube in cubes}

    for i in tqdm(range(num_simulation)):
        random.shuffle(race.cubes)
        race.reset()
        race.start()

        for i, cube in enumerate(race.compute_rankings()):
            rank_history[cube.__class__.__name__].append(i + 1)

    with open(f"history.pkl", "wb") as fp:
        pickle.dump(rank_history, fp)
