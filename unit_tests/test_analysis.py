import unittest

from osu_analysis.mania.action_data import ManiaActionData

from beatmap_reader import BeatmapIO
from replay_reader import ReplayIO


class TestAnalysis(unittest.TestCase):

    def test_mania_map(self):
        beatmap = BeatmapIO.open_beatmap('beatmap_reader\\beatmap_reader\\unit_tests\\maps\\mania\\Camellia - GHOST (qqqant) [Collab PHANTASM [MX]].osu')
        action_data = ManiaActionData.get_action_data(beatmap)


        #print(action_data.action_data)


    def test_mania_replay(self):
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\abraker - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2020-04-25) OsuMania.osr')
        action_data = ManiaActionData.get_action_data(replay)

        
        #print(action_data.action_data)
