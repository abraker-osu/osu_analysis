import unittest
import numpy as np

from beatmap_reader import BeatmapIO
from osu_analysis import ManiaActionData
from osu_analysis import ManiaMapMetrics



class TestManiaMetricData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass


    @classmethod
    def tearDown(cls):
        pass


    def test_calc_press_rate(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        press_rate = ManiaMapMetrics.calc_press_rate(action_data, col=0)


    def test_calc_note_intervals(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        note_intervals = ManiaMapMetrics.calc_note_intervals(action_data, 0)


    def test_max_press_rate_per_col(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        press_rate = ManiaMapMetrics.calc_max_press_rate_per_col(action_data)


    def test_detect_presses_during_holds(self):
        # Two long notes that are pressed and released at mutually exclusive times
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 300, 400, 1 ],
        ])

        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes that are pressed and released at mutually exclusive times,
        # but press of one happens when the other is released
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 200, 300, 1 ],
        ])

        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes that are pressed and release at same time
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 100, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes, where one is pressed before the other, but released at same time
        action_data = np.asarray([
            [ 50,  200, 0 ],
            [ 100, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)
        self.assertFalse(np.all(mask == 0))

        # Two long notes that are pressed at same time, but one is released before another
        action_data = np.asarray([
            [ 100, 150, 0 ],
            [ 100, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes where one is pressed and released before another
        action_data = np.asarray([
            [ 100, 150, 0 ],
            [ 120, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)
        self.assertFalse(np.all(mask == 0))

        # Two long notes where one is pressed and released while holding another
        action_data = np.asarray([
            [ 100, 300, 0 ],
            [ 150, 250, 1 ],
        ])

        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)
        self.assertFalse(np.all(mask == 0))

        # Crash test
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)
        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)

        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        action_data = ManiaActionData.get_action_data(beatmap)
        mask = ManiaMapMetrics.detect_presses_during_holds(action_data)


    def test_detect_holds_during_release(self):
        # Two long notes that are pressed and released at mutually exclusive times
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 300, 400, 1 ],
        ])

        mask = ManiaMapMetrics.detect_holds_during_release(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes that are pressed and released at mutually exclusive times,
        # but press of one happens when the other is released
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 200, 300, 1 ],
        ])

        mask = ManiaMapMetrics.detect_holds_during_release(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes that are pressed and release at same time
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 100, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_holds_during_release(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes, where one is pressed before the other, but released at same time
        action_data = np.asarray([
            [ 50, 200, 0 ],
            [ 100, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_holds_during_release(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes that are pressed at same time, but one is released before another
        action_data = np.asarray([
            [ 100, 150, 0 ],
            [ 100, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_holds_during_release(action_data)
        self.assertFalse(np.all(mask == 0))

        # Two long notes where one is pressed and released before another
        action_data = np.asarray([
            [ 100, 150, 0 ],
            [ 120, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_holds_during_release(action_data)
        self.assertFalse(np.all(mask == 0))

        # Two long notes where one is pressed and released while holding another
        action_data = np.asarray([
            [ 100, 300, 0 ],
            [ 150, 250, 1 ],
        ])

        mask = ManiaMapMetrics.detect_holds_during_release(action_data)
        self.assertFalse(np.all(mask == 0))

        # Crash test
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)
        mask = ManiaMapMetrics.detect_holds_during_release(action_data)

        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        action_data = ManiaActionData.get_action_data(beatmap)
        mask = ManiaMapMetrics.detect_holds_during_release(action_data)


    def test_detect_simultaneous_notes(self):
        # Two long notes that are pressed and released at mutually exclusive times
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 300, 400, 1 ],
        ])

        mask = ManiaMapMetrics.detect_simultaneous_notes(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes that are pressed and released at mutually exclusive times,
        # but press of one happens when the other is released
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 200, 300, 1 ],
        ])

        mask = ManiaMapMetrics.detect_simultaneous_notes(action_data)
        self.assertTrue(np.all(mask == 0))

        # Two long notes that are pressed and release at same time
        action_data = np.asarray([
            [ 100, 200, 0 ],
            [ 100, 200, 1 ],
        ])

        mask = ManiaMapMetrics.detect_simultaneous_notes(action_data)
        self.assertTrue(np.all(mask == 1))


    def test_detect_hold_notes(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        mask = ManiaMapMetrics.detect_hold_notes(action_data)
        self.assertTrue(np.all(mask == 0))

        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality more thourouly
        mask = ManiaMapMetrics.detect_hold_notes(action_data)
        self.assertTrue(np.any(mask == 1))  # There are definitely hold notes in that map


    def test_data_to_anti_press_durations(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        anti_press_durations = ManiaMapMetrics.anti_press_durations(action_data)


    def test_detect_inverse(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        inverse_mask = ManiaMapMetrics.detect_inverse(action_data)
        self.assertTrue(np.all(inverse_mask == 0))

        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\inverse_test.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        inverse_mask = ManiaMapMetrics.detect_inverse(action_data)
        self.assertFalse(np.all(inverse_mask == 0))

        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\sr_testing\\high_sr_low_diff_norm_hp\\3L - Endless Night x1.25 (Skorer) [Endless Longs Notes !!].osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        inverse_mask = ManiaMapMetrics.detect_inverse(action_data)
        self.assertFalse(np.all(inverse_mask == 0))


    def test_detect_chords(self):
        # Two single notes, one occuring after another
        action_data = np.asarray([
            [ 100, 101, 0 ],
            [ 200, 201, 1 ],
        ])

        mask = ManiaMapMetrics.detect_chords(action_data)
        self.assertTrue(np.all((mask == [0, 0]) == 1))

        # Two single notes, both occuring at same time
        action_data = np.asarray([
            [ 100, 101, 0 ],
            [ 100, 101, 1 ],
        ])

        mask = ManiaMapMetrics.detect_chords(action_data)
        self.assertTrue(np.all((mask == [1, 1]) == 1))

        # Two single notes occuring at same time + a jack after
        action_data = np.asarray([
            [ 100, 101, 0 ],
            [ 100, 101, 1 ],
            [ 200, 201, 1 ],
        ])

        mask = ManiaMapMetrics.detect_chords(action_data)
        self.assertTrue(np.all((mask == [1, 1, 0]) == 1))

        # Two single notes occuring at same time + a jack before
        action_data = np.asarray([
            [ 200, 201, 0 ],
            [ 200, 201, 1 ],
            [ 100, 101, 1 ],
        ])

        mask = ManiaMapMetrics.detect_chords(action_data)
        self.assertTrue(np.all((mask == [1, 1, 0]) == 1))

        # Stair case
        action_data = np.asarray([
            [ 100, 101, 0 ],
            [ 200, 201, 1 ],
            [ 300, 301, 2 ],
        ])

        mask = ManiaMapMetrics.detect_chords(action_data)
        self.assertTrue(np.all((mask == [0, 0, 0]) == 1))

        # 3 note chord
        action_data = np.asarray([
            [ 100, 101, 0 ],
            [ 100, 101, 1 ],
            [ 100, 101, 3 ],
        ])

        mask = ManiaMapMetrics.detect_chords(action_data)
        self.assertTrue(np.all((mask == [1, 1, 1]) == 1))

        # Alternation
        action_data = np.asarray([
            [ 100, 101, 0 ],
            [ 100, 101, 2 ],
            [ 200, 201, 1 ],
            [ 200, 201, 3 ],
            [ 300, 301, 0 ],
            [ 300, 301, 2 ],
        ])

        mask = ManiaMapMetrics.detect_chords(action_data)
        self.assertTrue(np.all((mask == [0, 0, 0, 0, 0, 0]) == 1))

        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        chord_mask = ManiaMapMetrics.detect_chords(action_data)
        print(action_data[chord_mask])

    '''
    def test_data_to_press_durations(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        press_intervals = ManiaMapMetrics.press_durations(action_data)
        print(press_intervals)

        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality more thourouly
        press_intervals = ManiaMapMetrics.press_durations(action_data)

        print(action_data)
        print(press_intervals)


    def test_data_to_hold_durations(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        hold_note_durations = ManiaMapMetrics.hold_durations(action_data)


    def test_detect_jacks(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\test\\chords_250ms.osu')
        action_data = ManiaActionData.get_action_data(beatmap)

        # TODO: test functionality
        jack_mask = ManiaMapMetrics.detect_jacks(action_data)
    '''
