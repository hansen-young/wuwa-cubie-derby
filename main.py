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
            ThrusterPad(3),
            SpatialRiftPad(6),
            BlockerPad(10),
            ThrusterPad(11),
            ThrusterPad(16),
            SpatialRiftPad(20),
            ThrusterPad(23),
            BlockerPad(28),
        ],
    )
    cubes: list[Cube] = [
        Abbowser(track.length * laps),
        Sigrika(1),
        Luuk(1),
        Lynae(1),
        Carlotta(1),
        Iuno(1),
        Changli(1),
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
