"""
Map analysis demo
"""
from beatmap_reader import BeatmapIO
from osu_analysis import StdMapData

if __name__ == '__main__':
    beatmap = BeatmapIO.open_beatmap('test/data/maps/osu/playable/Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic].osu')
    map_data = StdMapData.get_map_data(beatmap)

    print(map_data)
