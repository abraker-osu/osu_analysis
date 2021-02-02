import unittest

from beatmap_reader import BeatmapIO
from replay_reader import ReplayIO

from analysis.mania.action_data import ManiaActionData
from analysis.mania.score_data import ManiaScoreData



class TestManiaScoreData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass


    @classmethod
    def tearDown(cls):  
        pass


    def test_get_score_data(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 offset)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        self.assertTrue(all((score_data['replay_t'] - score_data['map_t']).values == 0))


    def test_get_custom_score_data(self):
        # TODO: custom scoring parameters
        pass


    def test_filter_by_hit_type(self):
        # TODO
        pass


    def test_press_interval_mean(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (1 ms press intervals)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        # TODO: implementation


    def test_tap_offset_mean_0(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 mean)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        tap_offset_mean = ManiaScoreData.tap_offset_mean(score_data)
        self.assertEqual(tap_offset_mean, 0)


    def test_tap_offset_mean_100(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        timings = replay.get_time_data()
        timings[0] += 100

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 mean + 100 ms offset)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        tap_offset_mean = ManiaScoreData.tap_offset_mean(score_data)
        self.assertEqual(tap_offset_mean, 100)


    def test_tap_offset_mean_150(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        timings = replay.get_time_data()
        timings[0] += 150

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 mean + 150 ms offset)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        tap_offset_mean = ManiaScoreData.tap_offset_mean(score_data)
        self.assertEqual(tap_offset_mean, 150)


    def test_tap_offset_var(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 variance)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        tap_offset_var = ManiaScoreData.tap_offset_var(score_data)
        self.assertEqual(tap_offset_var, 0)


    def test_tap_offset_stdev(self):
        beatmap = BeatmapIO.open_beatmap('unit_tests\\maps\\mania\\playable\\DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('unit_tests\\replays\\mania\\osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 std dev)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        tap_offset_stdev = ManiaScoreData.tap_offset_stdev(score_data)
        self.assertEqual(tap_offset_stdev, 0)


    def test_model_offset_prob(self):
        # TODO
        pass


    def test_odds_some_tap_within(self):
        # TODO
        pass


    def test_odds_all_tap_within(self):
        # TODO
        pass


    def test_model_ideal_acc(self):
        # TODO
        pass


    def test_model_num_hits(self):
        # TODO
        pass


    def test_odds_acc(self):
        # TODO
        pass