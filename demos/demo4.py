"""
Score analysis demo

NOTE: If changes were made, run refresh.bat to apply replay_reader changes to venv
"""
from replay_reader import ReplayIO
from beatmap_reader import BeatmapIO
from osu_analysis import StdMapData, StdReplayData, StdScoreData


if __name__ == '__main__':
    replay = ReplayIO.open_replay('test/data/replays/osu/LeaF - I (Maddy) [Terror] replay_0.osr')
    replay_data = StdReplayData.get_replay_data(replay)

    beatmap = BeatmapIO.open_beatmap('test/data/maps/osu/playable/Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic].osu')
    map_data = StdMapData.get_map_data(beatmap)

    score_data = StdScoreData.get_score_data(replay_data, map_data)
    print(score_data)
