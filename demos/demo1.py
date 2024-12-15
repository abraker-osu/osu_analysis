"""
Beatmap loading demo

NOTE: If changes were made, run refresh.bat to apply replay_reader changes to venv
"""
from beatmap_reader import BeatmapIO

if __name__ == '__main__':
    beatmap = BeatmapIO.open_beatmap('tests/data/maps/osu/playable/Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic].osu')
    print(beatmap.metadata.name)
