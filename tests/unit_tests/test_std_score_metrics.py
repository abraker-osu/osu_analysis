import unittest

from beatmap_reader import BeatmapIO
from replay_reader  import ReplayIO

from osu_analysis import StdMapData
from osu_analysis import StdReplayData
from osu_analysis import StdScoreData
from osu_analysis import StdScoreMetrics



class TestStdScoreMetrics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.beatmap = BeatmapIO.open_beatmap('tests/data/maps/osu/test/abraker - unknown (abraker) [250ms].osu')


    @classmethod
    def tearDown(cls):
        pass


    def test_get_per_hitobject_score_data(self):
        # TODO
        pass


    def test_get_percent_below_offset_one(self):
        # TODO
        pass


    def test_percent_players_taps_all(self):
        # TODO
        pass


    def test_solve_for_hit_offset_one(self):
        # TODO
        pass


    def test_solve_for_hit_offset_all(self):
        # TODO
        pass
