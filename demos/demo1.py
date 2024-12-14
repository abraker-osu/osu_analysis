"""
Beatmap loading demo
"""
from beatmap_reader import BeatmapIO

if __name__ == '__main__':
    beatmap = BeatmapIO.open_beatmap('test/data/maps/osu/playable/Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic].osu')
    print(beatmap.metadata.name)
