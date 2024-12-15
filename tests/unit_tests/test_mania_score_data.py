import unittest
import numpy as np

from beatmap_reader import BeatmapIO
from replay_reader  import ReplayIO

from osu_analysis import ManiaActionData
from osu_analysis import ManiaScoreData



class TestManiaScoreData(unittest.TestCase):

    @classmethod
    def setUp(cls):
        ManiaScoreData.pos_hit_range       = 100
        ManiaScoreData.neg_hit_range       = 100
        ManiaScoreData.pos_hit_miss_range  = 200
        ManiaScoreData.neg_hit_miss_range  = 200

        ManiaScoreData.pos_rel_range       = 300
        ManiaScoreData.neg_rel_range       = 300
        ManiaScoreData.pos_rel_miss_range  = 500
        ManiaScoreData.neg_rel_miss_range  = 500

        ManiaScoreData.notelock = True
        ManiaScoreData.dynamic_window = False
        ManiaScoreData.blank_miss = False
        ManiaScoreData.lazy_sliders = False
        ManiaScoreData.overlap_miss_handling = False
        ManiaScoreData.overlap_hit_handling  = False


    @classmethod
    def tearDown(cls):
        pass


    def test_perfect_score(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 offset)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        score_types = score_data['type'].values
        self.assertEqual(len(score_types[score_types == ManiaScoreData.TYPE_MISSP]), 0)
        self.assertEqual(len(score_types[score_types == ManiaScoreData.TYPE_MISSR]), 0)

        # Mania auto releases hold notes 1 ms early
        offsets = (score_data['replay_t'] - score_data['map_t']).values
        self.assertEqual(len(offsets[~((offsets == 0) | (offsets == -1))]), 0)


    def test_scoring_completeness(self):
        # Check if the score processor went through and recorded all of the timings
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/Various Artists - I Like This Chart, LOL vol. 2 (Fullereneshift) [LENK64 - Crazy Slav Dancers (HD) (Marathon)].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/abraker - Various Artists - I Like This Chart, LOL vol. 2 [LENK64 - Crazy Slav Dancers (HD) (Marathon)] (2021-07-10) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        map_score_xor = np.setxor1d(score_data['map_t'].values, ManiaActionData.press_times(map_data))  # Hits that are not present in either
        map_score_xor = np.intersect1d(map_score_xor, ManiaActionData.press_times(map_data))            # Hits that are present in map but not score
        self.assertEqual(len(map_score_xor), 0, f'Timings mising: {map_score_xor}')


    def test_scoring_integrity(self):
        # The number of hits + misses should match for all same maps
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/Goreshit - Satori De Pon! (SReisen) [Star Burst 2!].osu')

        def test(replay1_filename, replay2_filename, press_release):
            replay1 = ReplayIO.open_replay(replay1_filename)
            replay2 = ReplayIO.open_replay(replay2_filename)

            map_data = ManiaActionData.get_action_data(beatmap)
            score_data1 = ManiaScoreData.get_score_data(map_data, ManiaActionData.get_action_data(replay1))
            score_data2 = ManiaScoreData.get_score_data(map_data, ManiaActionData.get_action_data(replay2))

            hit_type  = ManiaScoreData.TYPE_HITP  if press_release == 1 else ManiaScoreData.TYPE_HITR
            miss_type = ManiaScoreData.TYPE_MISSP if press_release == 1 else ManiaScoreData.TYPE_MISSR

            for c in range(score_data1.shape[1]):
                score_col1 = score_data1.loc[c]
                score_col2 = score_data2.loc[c]

                num_hits1 = score_col1['type'].values[score_col1['type'].values == hit_type].shape[0]
                num_miss1 = score_col1['type'].values[score_col1['type'].values == miss_type].shape[0]

                num_hits2 = score_col2['type'].values[score_col2['type'].values == hit_type].shape[0]
                num_miss2 = score_col2['type'].values[score_col2['type'].values == miss_type].shape[0]

                hitp_t1 = score_col1['map_t'].values[score_col1['type'].values == hit_type]
                miss_t1 = score_col1['map_t'].values[score_col1['type'].values == miss_type]
                notes_t1 = np.concatenate((hitp_t1, miss_t1), axis=None).astype(int)  # All note timings in score 1
                notes_t1 = np.sort(notes_t1)

                hitp_t2 = score_col2['map_t'].values[score_col2['type'].values == hit_type]
                miss_t2 = score_col2['map_t'].values[score_col2['type'].values == miss_type]
                notes_t2 = np.concatenate((hitp_t2, miss_t2), axis=None).astype(int)  # All note timings in score 2
                notes_t2 = np.sort(notes_t2)

                notes_count1 = np.zeros(max(np.max(notes_t1), np.max(notes_t2)) + 1)
                notes_count2 = np.zeros(max(np.max(notes_t1), np.max(notes_t2)) + 1)

                notes_count1[:np.max(notes_t1)+1] = np.bincount(notes_t1)  # Integer histogram for timings of score 1
                notes_count2[:np.max(notes_t2)+1] = np.bincount(notes_t2)  # Integer histogram for timings of score 2
                notes_mismatch = np.arange(max(np.max(notes_t1), np.max(notes_t2)) + 1)[notes_count1 != notes_count2]

                replay1_name = replay1_filename[replay1_filename.rfind("/") + 1:]
                replay2_name = replay2_filename[replay2_filename.rfind("/") + 1:]

                self.assertEqual(num_hits1 + num_miss1, num_hits2 + num_miss2,
                    f'\n\tReplays: {replay1_name}    {replay2_name}\n'
                    f'\tTest for {"Press" if press_release == 1 else "Release"}\n'
                    f'\tOne of two maps have missing or extra scoring points at column {c}\n'
                    f'\tScore 1 hits & misses: {num_hits1} + {num_miss1} = {num_hits1 + num_miss1}    score 2 hits & misses: {num_hits2} + {num_miss2} = {num_hits2 + num_miss2}\n'
                    f'\tNote timings mismatched: {notes_mismatch}   score 1 occurences: {notes_count1[notes_count1 != notes_count2]}    score 2 occurences: {notes_count2[notes_count1 != notes_count2]}\n'
                )

        test(
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-24) OsuMania.osr',
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-24) OsuMania-1.osr',
            press_release=1
        )

        test(
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-24) OsuMania.osr',
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-24) OsuMania-1.osr',
            press_release=0
        )

        test(
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-24) OsuMania.osr',
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-31) OsuMania.osr',
            press_release=1
        )

        test(
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-24) OsuMania.osr',
            'tests/data/replays/mania/abraker - Goreshit - Satori De Pon! [Star Burst 2!] (2021-07-31) OsuMania.osr',
            press_release=0
        )

        test(
            'tests/data/replays/mania/abraker - Hyadain - Enemy Appearance! [NM] (2021-07-31) OsuMania-1.osr',
            'tests/data/replays/mania/abraker - Hyadain - Enemy Appearance! [NM] (2021-07-31) OsuMania.osr',
            press_release=1
        )

        test(
            'tests/data/replays/mania/abraker - Hyadain - Enemy Appearance! [NM] (2021-07-31) OsuMania-1.osr',
            'tests/data/replays/mania/abraker - Hyadain - Enemy Appearance! [NM] (2021-07-31) OsuMania.osr',
            press_release=0
        )


    def test_get_custom_score_data(self):
        # TODO: custom scoring parameters
        pass


    def test_filter_by_hit_type(self):
        # TODO
        pass


    def test_press_interval_mean(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (1 ms press intervals)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)
        # TODO: implementation


    def test_tap_offset_mean_0(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 mean)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        # Include only hits
        score_data = score_data[score_data['type'] == ManiaScoreData.TYPE_HITP]
        tap_offset_mean = ManiaScoreData.tap_offset_mean(score_data)
        self.assertEqual(tap_offset_mean, 0)


    def test_tap_offset_mean_100(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        timings = replay.get_time_data()
        timings[0] += 100

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 mean + 100 ms offset)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        # Include only hits
        score_data = score_data[score_data['type'] == ManiaScoreData.TYPE_HITP]
        tap_offset_mean = ManiaScoreData.tap_offset_mean(score_data)
        self.assertEqual(tap_offset_mean, 100)


    def test_tap_offset_mean_max(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        timings = replay.get_time_data()
        timings[0] += ManiaScoreData.pos_hit_range - 1

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 mean + 150 ms offset)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        # Include only hits
        score_data = score_data[score_data['type'] == ManiaScoreData.TYPE_HITP]
        tap_offset_mean = ManiaScoreData.tap_offset_mean(score_data)
        self.assertEqual(tap_offset_mean, ManiaScoreData.pos_hit_range - 1)


    def test_tap_offset_var(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 variance)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        # Include only hits
        score_data = score_data[score_data['type'] == ManiaScoreData.TYPE_HITP]
        tap_offset_var = ManiaScoreData.tap_offset_var(score_data)
        self.assertEqual(tap_offset_var, 0)


    def test_tap_offset_stdev(self):
        beatmap = BeatmapIO.open_beatmap('tests/data/maps/mania/playable/DJ Genericname - Dear You (Taiwan-NAK) [S.Star\'s 4K HD+].osu')
        replay = ReplayIO.open_replay('tests/data/replays/mania/osu!topus! - DJ Genericname - Dear You [S.Star\'s 4K HD+] (2019-05-29) OsuMania.osr')

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)

        # osu!topus should have played all notes perfectly (0 std dev)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        # Include only hits
        score_data = score_data[score_data['type'] == ManiaScoreData.TYPE_HITP]
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
