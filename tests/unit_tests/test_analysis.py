import unittest

from beatmap_reader import BeatmapIO
from replay_reader  import ReplayIO

from osu_analysis import ManiaActionData


class TestAnalysis(unittest.TestCase):

    def test_mania_map(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/Camellia - GHOST (qqqant) [Collab PHANTASM [MX]].osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        #print(action_data.action_data)


    def test_mania_replay(self):
        replay = ReplayIO.open_replay('tests/data/replays/mania/abraker - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2020-04-25) OsuMania.osr')
        action_data = ManiaActionData.get_action_data(replay)

        #print(action_data.action_data)
