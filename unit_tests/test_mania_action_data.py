import unittest
import numpy as np

from beatmap_reader import BeatmapIO
from replay_reader import ReplayIO

from osu_analysis.mania.action_data import ManiaActionData



class TestManiaActionData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass


    @classmethod
    def tearDown(cls):  
        pass


    def test_get_map_data_crash(self):
        def test_map(map_path):
            beatmap = BeatmapIO.open_beatmap(map_path)
            map_data = ManiaActionData.get_action_data(beatmap)

            dt = np.diff(map_data[:, ManiaActionData.IDX_STIME])
            self.assertTrue(all(dt >= 0), 'Map data is not order by note starting times')

        test_map('unit_tests\\maps\\mania\\test\\1k_10x_0.25_chords.osu')
        test_map('unit_tests\\maps\\mania\\test\\2k_10x_0.25_chords.osu')
        test_map('unit_tests\\maps\\mania\\test\\3k_10x_0.25_chords.osu')
        test_map('unit_tests\\maps\\mania\\test\\4k_10x_0.25_chords.osu')
        test_map('unit_tests\\maps\\mania\\test\\5k_10x_0.25_chords.osu')
        test_map('unit_tests\\maps\\mania\\test\\7k_10x_0.25_chords.osu')
        test_map('unit_tests\\maps\\mania\\test\\8k_mixed_timing_jacks.osu')
        test_map('unit_tests\\maps\\mania\\test\\14k_test.osu')
        test_map('unit_tests\\maps\\mania\\test\\18k_test.osu')


    def test_num_keys(self):
        def test_keys(keys):
            beatmap = BeatmapIO.open_beatmap(f'unit_tests\\maps\\mania\\test\\{keys}k_10x_0.25_chords.osu')
            action_data = ManiaActionData.get_action_data(beatmap)
            self.assertEqual(ManiaActionData.num_keys(action_data), keys, 'Calculated wrong number of keys')

        for key in [ 1, 2, 3, 4, 5, 6, 7 ]: 
            test_keys(key)


    def test_press_times(self):
        # This map has notes every 250ms
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\1k_10x_0.25_chords.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # Notes occur every 500 ms
        press_times = ManiaActionData.press_times(action_data[ManiaActionData.IDX_COL == 0, :])
        for timing, i in zip(press_times, range(0, 500*10, 500)):
            self.assertEqual(timing, i, 'Timings do not match')


    def test_release_times(self):
        # This map has notes every 250ms
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\1k_10x_0.25_chords.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # Notes occur every 500 ms + 1 ms for release
        release_times = ManiaActionData.release_times(action_data[ManiaActionData.IDX_COL == 0, :])
        for timing, i in zip(release_times, range(0, 500*10, 500)):
            self.assertEqual(timing, i + 1, 'Timings do not match')


    def test_split_by_hand(self):
        def test_keys(keys, lh, rh):
            beatmap = BeatmapIO.open_beatmap(f'unit_tests\\maps\\mania\\test\\{keys}k_10x_0.25_chords.osu')
            action_data = ManiaActionData.get_action_data(beatmap)

            left_hand, right_hand = ManiaActionData.split_by_hand(action_data, left_handed=True)
            self.assertEqual(ManiaActionData.num_keys(left_hand),  lh, 'Left hand has wrong number of keys')
            self.assertEqual(ManiaActionData.num_keys(right_hand), rh, 'Right hand has wrong number of keys')

            lh, rh = rh, lh
            left_hand, right_hand = ManiaActionData.split_by_hand(action_data, left_handed=False)
            self.assertEqual(ManiaActionData.num_keys(left_hand),  lh, 'Left hand has wrong number of keys')
            self.assertEqual(ManiaActionData.num_keys(right_hand), rh, 'Right hand has wrong number of keys')

        test_keys(1, 1, 0)
        test_keys(2, 1, 1)
        test_keys(3, 2, 1)
        test_keys(4, 2, 2)
        test_keys(5, 3, 2)
        test_keys(6, 3, 3)
        test_keys(7, 4, 3)


    def test_get_actions_between(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\8k_mixed_timing_jacks.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        ManiaActionData.get_actions_between(action_data, 0, 100)


    def test_get_idx_sort(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\8k_mixed_timing_jacks.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        ManiaActionData.get_idx_col_sort(action_data)
