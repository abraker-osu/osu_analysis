import unittest

from beatmap_reader import BeatmapIO

from osu_analysis.std.map_data import StdMapData
from osu_analysis.std.map_patterns import StdMapPatterns



class TestStdMapPatterns(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\osu\\test\\abraker - unknown (abraker) [250ms].osu')
        cls.map_data = StdMapData.get_map_data(cls.beatmap)


    @classmethod
    def tearDown(cls):  
        pass


    def test_detect_short_sliders_dist(self):
        short_sliders = StdMapPatterns.detect_short_sliders_dist(self.map_data, cs_px=4)


    def test_detect_short_sliders_time(self):
        short_sliders = StdMapPatterns.detect_short_sliders_time(self.map_data, min_time=100)


    def test_reinterpret_short_sliders(self):
        map_data = StdMapPatterns.reinterpret_short_sliders(self.map_data, min_time=100, cs_px=4)
