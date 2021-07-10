from enum import Enum
import numpy as np
import pandas as pd
import scipy.stats
import math

from ..utils import prob_trials
from .action_data import ManiaActionData


class ManiaScoreDataError(Exception):
    pass


class ManiaScoreDataEnums(Enum):

    TIME          = 0
    COLUMN        = 1
    HIT_OFFSET    = 2
    HITOBJECT_IDX = 4


class ManiaScoreData():

    __ADV_NOP  = 0  # Used internal by scoring processor; Don't advance
    __ADV_MAP = 1  # Used internal by scoring processor; Advance timing

    TYPE_HITP  = 0  # A hit press has a hitobject and offset associated with it
    TYPE_HITR  = 1  # A hit release has a hitobject and offset associated with it
    TYPE_MISS  = 2  # A miss has a hitobject associated with it, but not offset
    TYPE_EMPTY = 3  # An empty has neither hitobject nor offset associated with it

    IDX_REPLAY_T = 0
    IDX_MAP_T    = 1
    IDX_TYPE     = 2
    IDX_MAP_IDX  = 3

    # TODO: deprecate
    DATA_OFFSET  = 0 
    DATA_TYPE    = 1
    DATA_MAP_IDX = 2

    pos_hit_range       = 100  # ms point of the late hit window
    neg_hit_range       = 100  # ms point of the early hit window
    pos_hit_miss_range  = 200  # ms point of the late miss window
    neg_hit_miss_range  = 200  # ms point of the early miss window

    pos_rel_range       = 300  # ms point of the late release window
    neg_rel_range       = 300  # ms point of the early release window
    pos_rel_miss_range  = 500  # ms point of the late release window
    neg_rel_miss_range  = 500  # ms point of the early release window

    # Disables hitting next note too early. If False, the neg_miss_range of the current note is 
    # overridden to extend to the previous note's pos_hit_range boundary.
    notelock = True

    # Overrides the miss and hit windows to correspond to spacing between notes. If True then all 
    # the ranges are are overridden to be split up in 1/4th sections relative to the distance between 
    # current and next notes
    dynamic_window = False

    # Enables missing in blank space. If True, the Nothing window behaves like the miss window, but the 
    # iterator does not go to the next note.
    blank_miss = False

    # If True, remove release miss window for sliders. This allows to hit sliders and release them whenever
    lazy_sliders = False

    # There are cases for which parts of the hitwindow of multiple notes may overlap. If True, all 
    # overlapped miss parts are processed for one key event. If False, each overlapped miss part is 
    # processed for each individual key event.
    overlap_miss_handling = False

    # There are cases for which parts of the hitwindow of multiple notes may overlap. If True, all 
    # overlapped hit parts are processed for one key event. If False, each overlapped hit part is 
    # processed for each individual key event.
    overlap_hit_handling  = False


    @staticmethod
    def __process_press(column_data, replay_time, map_times, map_idx):
        time_offset    = replay_time - map_times[map_idx]
        is_single_note = ((map_times[map_idx + 1] - map_times[map_idx]) <= 1)

        # Way early taps. Miss if blank miss is on -> record miss, otherwise ignore
        is_in_neg_nothing_range = time_offset <= -ManiaScoreData.neg_hit_miss_range
        if is_in_neg_nothing_range:
            if ManiaScoreData.blank_miss:
                column_data[len(column_data)] = np.asarray([ replay_time, np.nan, ManiaScoreData.TYPE_EMPTY, None ])
            return 0  # Don't advance to next note

        # Early miss tap
        is_in_neg_miss_range = -ManiaScoreData.neg_hit_miss_range < time_offset <= -ManiaScoreData.neg_hit_range
        if is_in_neg_miss_range:
            column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_MISS, map_idx ])
            return 2  # Advance to next note
        
        # Hit range
        is_in_hit_range = -ManiaScoreData.neg_hit_range < time_offset <= ManiaScoreData.pos_hit_range
        if is_in_hit_range:
            column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_HITP, map_idx ])

            # Go to next note if it's a single or releases don't matter
            return 2 if is_single_note or ManiaScoreData.lazy_sliders else 1
            
        # Late miss tap
        is_in_pos_miss_range = ManiaScoreData.pos_hit_range < time_offset <= ManiaScoreData.pos_hit_miss_range
        if is_in_pos_miss_range:
            column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_MISS, map_idx ])
            return 2  # Advance to next note

        # Way late taps. Doesn't matter where, ignore these
        is_in_pos_nothing_range = ManiaScoreData.pos_hit_miss_range < time_offset
        if is_in_pos_nothing_range:
            if ManiaScoreData.blank_miss:
                column_data[len(column_data)] = np.asarray([ replay_time, np.nan, ManiaScoreData.TYPE_EMPTY, None ])
            return 0  # Don't advance to next note

        raise ManiaScoreDataError('Press scoring processing error!')


    @staticmethod
    def __process_release(column_data, replay_time, map_times, map_idx):
        # If this is true, then release timings are ignored
        if ManiaScoreData.lazy_sliders:
            return 1  # Advance to next note; skip this

        time_offset    = replay_time - map_times[map_idx]
        is_single_note = ((map_times[map_idx] - map_times[map_idx - 1]) <= 1)

        # Single notes have no release timing
        if is_single_note:
            return 1  # Advance to next note; skip this

        # Way early taps. Miss if blank miss is on -> record miss, otherwise ignore
        is_in_neg_nothing_range = time_offset <= -ManiaScoreData.neg_rel_miss_range
        if is_in_neg_nothing_range:
            if ManiaScoreData.blank_miss:
                column_data[len(column_data)] = np.asarray([ replay_time, np.nan, ManiaScoreData.TYPE_EMPTY, None ])
            return 0  # Don't advance to next note

        # Early miss tap
        is_in_neg_miss_range = -ManiaScoreData.neg_rel_miss_range < time_offset <= -ManiaScoreData.neg_rel_range
        if is_in_neg_miss_range:
            column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_MISS, map_idx ])
            return 1  # Advance to next note
        
        # Hit range
        is_in_hit_range = -ManiaScoreData.neg_rel_range < time_offset <= ManiaScoreData.pos_rel_range
        if is_in_hit_range:
            column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_HITR, map_idx ])
            return 1  # Advance to next note
            
        # Late miss tap
        is_in_pos_miss_range = ManiaScoreData.pos_rel_range < time_offset <= ManiaScoreData.pos_rel_miss_range
        if is_in_pos_miss_range:
            column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_MISS, map_idx ])
            return 1  # Advance to next note

        # Way late taps. Doesn't matter where, ignore these
        is_in_pos_nothing_range = ManiaScoreData.pos_rel_miss_range < time_offset
        if is_in_pos_nothing_range:
            if ManiaScoreData.blank_miss:
                column_data[len(column_data)] = np.asarray([ replay_time, np.nan, ManiaScoreData.TYPE_EMPTY, None ])
            return 0  # Don't advance to next note

        raise ManiaScoreDataError('Release scoring processing error!')


    @staticmethod
    def __process_free(column_data, note_type, replay_time, map_times, map_idx):
        if map_idx >= len(map_times):
            return 0  # Don't advance to next note

        time_offset = replay_time - map_times[map_idx]

        if note_type == ManiaActionData.PRESS:
            is_in_pos_nothing_range = ManiaScoreData.pos_hit_miss_range < time_offset
            if is_in_pos_nothing_range:
                column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_MISS, map_idx ])
                return 2  # Advance to next note

            return 0  # Don't advance to next note

        elif note_type == ManiaActionData.RELEASE:
            is_in_pos_nothing_range = ManiaScoreData.pos_rel_miss_range < time_offset
            if is_in_pos_nothing_range:
                is_single_note = ((map_times[map_idx] - map_times[map_idx - 1]) <= 1)
                if not is_single_note and not ManiaScoreData.lazy_sliders:
                    column_data[len(column_data)] = np.asarray([ replay_time, map_times[map_idx], ManiaScoreData.TYPE_MISS, map_idx ])
                return 1  # Advance to next note

            return 0  # Don't advance to next note

        else:
            return 1  # Advance to next scorepoint


    @staticmethod
    def get_score_data(map_data, replay_data):
        """
        [
            [ offset, col, type, action_idx ],
            [ offset, col, type, action_idx ],
            ...
        """
        map_num_cols = ManiaActionData.num_keys(map_data)
        replay_num_cols = ManiaActionData.num_keys(replay_data)

        if map_num_cols != replay_num_cols:
            raise ValueError(f'Number of columns between map and replay do not match; map columns: {map_num_cols}   replay columns: {replay_num_cols}')

        score_data = []

        IDX_TIME = 0
        IDX_TYPE = 1

        # Go through each column
        for map_col_idx, replay_col_idx in zip(range(map_num_cols), range(replay_num_cols)):
            map_col_filter = map_data[:, ManiaActionData.IDX_COL] == map_col_idx
            replay_col_filter = replay_data[:, ManiaActionData.IDX_COL] == replay_col_idx

            map_idx_max = map_data[map_col_filter].shape[0]
            replay_idx_max = replay_data[replay_col_filter].shape[0]

            # Map column data
            map_col = np.empty((map_idx_max*2, 2))
            map_col[:map_idx_max, IDX_TIME] = map_data[map_col_filter][:, ManiaActionData.IDX_STIME]
            map_col[map_idx_max:, IDX_TIME] = map_data[map_col_filter][:, ManiaActionData.IDX_ETIME]
            map_col[:map_idx_max, IDX_TYPE] = ManiaActionData.PRESS
            map_col[map_idx_max:, IDX_TYPE] = ManiaActionData.RELEASE

            map_sort = map_col.argsort(axis=0)
            map_col = map_col[map_sort[:, IDX_TIME]]

            # Replay column data
            replay_col = np.empty((replay_idx_max*2, 2))
            replay_col[:replay_idx_max, IDX_TIME] = replay_data[replay_col_filter][:, ManiaActionData.IDX_STIME]
            replay_col[replay_idx_max:, IDX_TIME] = replay_data[replay_col_filter][:, ManiaActionData.IDX_ETIME]
            replay_col[:replay_idx_max, IDX_TYPE] = ManiaActionData.PRESS
            replay_col[replay_idx_max:, IDX_TYPE] = ManiaActionData.RELEASE
            
            replay_sort = replay_col.argsort(axis=0)
            replay_col = replay_col[replay_sort[:, IDX_TIME]]

            map_idx    = 0
            replay_idx = 0

            note_type = map_col[map_idx, IDX_TYPE]
            column_data = {}

            # Number of things to loop through
            replay_idx_max = replay_idx_max*2
            map_idx_max = map_idx_max*2

            # Go through replay events
            while True:
                # Condition check whether all player actions in the column have been processed
                # It's possible that the player never pressed any keys, so this may hit more
                # often than one may expect
                if replay_idx >= replay_idx_max:
                    # Fill in any empty misses at the end of the map
                    for _ in range(map_idx, map_idx_max):
                        column_data[len(column_data)] = np.asarray([ replay_time, map_col[map_idx, IDX_TIME], ManiaScoreData.TYPE_EMPTY, None ])
                    break

                # Time at which press or release occurs
                replay_time = replay_col[replay_idx, IDX_TIME]
                replay_type = replay_col[replay_idx, IDX_TYPE]
 
                # Go through map notes
                while True:
                    # Check for any skipped notes (if replay has event gaps)
                    adv = ManiaScoreData.__process_free(column_data, note_type, replay_time, map_col[:, IDX_TIME], map_idx)
                    if adv == 0: break
                    
                    map_idx += adv
                    note_type = map_col[map_idx, IDX_TYPE] if map_idx < map_idx_max else ManiaActionData.FREE

                # If a press occurs at this time and we expect it
                if replay_type == ManiaActionData.PRESS and note_type == ManiaActionData.PRESS:
                    map_idx += ManiaScoreData.__process_press(column_data, replay_time, map_col[:, IDX_TIME], map_idx)
                    note_type = map_col[map_idx, IDX_TYPE] if map_idx < map_idx_max else ManiaActionData.FREE

                    replay_idx += 1
                    continue

                # If a release occurs at this time and we expect it
                if replay_type == ManiaActionData.RELEASE and note_type == ManiaActionData.RELEASE:
                    map_idx += ManiaScoreData.__process_release(column_data, replay_time, map_col[:, IDX_TIME], map_idx)
                    note_type = map_col[map_idx, IDX_TYPE] if map_idx < map_idx_max else ManiaActionData.FREE

                    replay_idx += 1
                    continue                        

                # If we are here then it's a HOLD or FREE. Ignore.
                replay_idx += 1
                continue

            # Sort data by timings
            column_data = dict(sorted(column_data.items()))

            # Convert the dictionary of recorded timings and states into a pandas data
            column_data = pd.DataFrame.from_dict(column_data, orient='index', columns=['replay_t', 'map_t', 'type', 'map_idx'])
            score_data.append(column_data)

        # This turns out to be 3 dimensional data (indexed by columns, timings, and attributes)
        return pd.concat(score_data, axis=0, keys=range(len(map_data)))


    @staticmethod
    def filter_by_hit_type(score_data, hit_types, invert=False):
        if type(hit_types) != list: hit_types = [ hit_types ]
        
        mask = score_data['type'] == hit_types[0]
        if len(hit_types) > 1:
            for hit_type in hit_types[1:]:
                mask |= score_data[ManiaScoreData.DATA_TYPE] == hit_type

        return score_data[~mask] if invert else score_data[mask]


    @staticmethod
    def press_interval_mean(score_data):
        # TODO need to put in release offset into score_data
        # TODO need to go through hitobjects and filter out hold notes
        #  
        pass


    @staticmethod
    def tap_offset_mean(score_data):
        score_data = ManiaScoreData.filter_by_hit_type(score_data, [ManiaScoreData.TYPE_EMPTY], invert=True)
        offset = score_data['replay_t'] - score_data['map_t']
        return np.mean(offset)


    @staticmethod
    def tap_offset_var(score_data):
        score_data = ManiaScoreData.filter_by_hit_type(score_data, [ManiaScoreData.TYPE_EMPTY], invert=True)
        offset = score_data['replay_t'] - score_data['map_t']
        return np.var(offset)


    @staticmethod
    def tap_offset_stdev(score_data):
        score_data = ManiaScoreData.filter_by_hit_type(score_data, [ManiaScoreData.TYPE_EMPTY], invert=True)
        offset = score_data['replay_t'] - score_data['map_t']
        return np.std(offset)


    @staticmethod
    def model_offset_prob(mean, stdev, offset):
        prob_less_than_neg = scipy.stats.norm.cdf(-offset, loc=mean, scale=stdev)
        prob_less_than_pos = scipy.stats.norm.cdf(offset, loc=mean, scale=stdev)

        return prob_less_than_pos - prob_less_than_neg


    @staticmethod
    def odds_some_tap_within(score_data, offset):
        """
        Creates a gaussian distribution model using avg and var of tap offsets and calculates the odds that some hit
        is within the specified offset

        Returns: probability one random value [X] is between -offset <= X <= offset
                 TL;DR: look at all the hits for scores; What are the odds of you picking 
                        a random hit that is between -offset and offset?
        """
        mean  = ManiaScoreData.tap_offset_mean(score_data)
        stdev = ManiaScoreData.tap_offset_stdev(score_data)

        return ManiaScoreData.model_offset_prob(mean, stdev, offset)


    @staticmethod
    def odds_all_tap_within(score_data, offset):    
        """
        Creates a gaussian distribution model using avg and var of tap offsets and calculates the odds that all hits
        are within the specified offset

        Returns: probability all random values [X] are between -offset <= X <= offset
                TL;DR: look at all the hits for scores; What are the odds all of them are between -offset and offset?
        """
        score_data = ManiaScoreData.filter_by_hit_type(score_data, [ManiaScoreData.TYPE_EMPTY], invert=True)
        return ManiaScoreData.odds_some_tap_within(score_data, offset)**len(score_data)

    
    @staticmethod
    def odds_all_tap_within_trials(score_data, offset, trials):
        """
        Creates a gaussian distribution model using avg and var of tap offsets and calculates the odds that all hits
        are within the specified offset after the specified number of trials

        Returns: probability all random values [X] are between -offset <= X <= offset after trial N
                TL;DR: look at all the hits for scores; What are the odds all of them are between -offset and offset during any of the number
                        of attempts specified?
        """
        return prob_trials(ManiaScoreData.odds_all_tap_within(score_data, offset), trials)


    @staticmethod
    def model_ideal_acc(mean, stdev, num_notes, score_point_judgements=None):
        """
        Set for OD8
        """
        prob_less_than_max  = ManiaScoreData.model_offset_prob(mean, stdev, 16.5)
        prob_less_than_300  = ManiaScoreData.model_offset_prob(mean, stdev, 40.5)
        prob_less_than_200  = ManiaScoreData.model_offset_prob(mean, stdev, 73.5)
        prob_less_than_100  = ManiaScoreData.model_offset_prob(mean, stdev, 103.5)
        prob_less_than_50   = ManiaScoreData.model_offset_prob(mean, stdev, 127.5)

        prob_max  = prob_less_than_max
        prob_300  = prob_less_than_300 - prob_max
        prob_200  = prob_less_than_200 - prob_less_than_300
        prob_100  = prob_less_than_100 - prob_less_than_200
        prob_50   = prob_less_than_50 - prob_less_than_100
        prob_miss = 1 - prob_less_than_50

        total_points_of_hits = (prob_50*50 + prob_100*100 + prob_200*200 + prob_300*300 + prob_max*300)*(num_notes - num_notes*prob_miss)

        return total_points_of_hits / (num_notes * 300)


    @staticmethod
    def model_ideal_acc_data(score_data, score_point_judgements=None):
        """
        Set for OD8
        """
        mean      = ManiaScoreData.tap_offset_mean(score_data)
        stdev     = ManiaScoreData.tap_offset_stdev(score_data)
        num_taps  = len(score_data[ManiaScoreData.DATA_OFFSET])

        return ManiaScoreData.model_ideal_acc(mean, stdev, num_taps, score_point_judgements)


    @staticmethod
    def model_num_hits(mean, stdev, num_notes):
        # Calculate probabilities of hits being within offset of the resultant gaussian distribution
        prob_less_than_max  = ManiaScoreData.model_offset_prob(mean, stdev, 16.5)
        prob_less_than_300  = ManiaScoreData.model_offset_prob(mean, stdev, 40.5)
        prob_less_than_200  = ManiaScoreData.model_offset_prob(mean, stdev, 73.5)
        prob_less_than_100  = ManiaScoreData.model_offset_prob(mean, stdev, 103.5)
        prob_less_than_50   = ManiaScoreData.model_offset_prob(mean, stdev, 127.5)

        prob_max  = prob_less_than_max
        prob_300  = prob_less_than_300 - prob_max
        prob_200  = prob_less_than_200 - prob_less_than_300
        prob_100  = prob_less_than_100 - prob_less_than_200
        prob_50   = prob_less_than_50 - prob_less_than_100
        prob_miss = 1 - prob_less_than_50

        # Get num of hitobjects that ideally would occur based on the gaussian distribution
        num_max  = prob_max*num_notes
        num_300  = prob_300*num_notes
        num_200  = prob_200*num_notes
        num_100  = prob_100*num_notes
        num_50   = prob_50*num_notes
        num_miss = prob_miss*num_notes

        return num_max, num_300, num_200, num_100, num_50, num_miss


    @staticmethod
    def odds_acc(score_data, target_acc):
        num_notes = len(np.vstack(score_data))
        mean      = ManiaScoreData.tap_offset_mean(score_data)

        def get_stdev_from_acc(acc):
            stdev    = ManiaScoreData.tap_offset_stdev(score_data)
            curr_acc = ManiaScoreData.model_ideal_acc_data(score_data)

            cost = round(acc, 3) - round(curr_acc, 3)
            rate = 1

            while cost != 0:
                stdev -= cost*rate

                curr_acc = ManiaScoreData.model_ideal_acc(mean, stdev, num_notes)
                cost = round(acc, 3) - round(curr_acc, 3)

            return stdev

        # Fit a normal distribution to the desired acc
        stdev = get_stdev_from_acc(target_acc)

        # Get the number of resultant hits from that distribution
        num_max, num_300, num_200, num_100, num_50, num_miss = ManiaScoreData.model_num_hits(mean, stdev, num_notes)

        # Get the stdev of of the replay data
        stdev = ManiaScoreData.tap_offset_stdev(score_data)

        # Get probabilites the number of score points are within hit window based on replay
        prob_less_than_max = scipy.stats.binom.sf(num_max - 1, num_notes, ManiaScoreData.model_offset_prob(mean, stdev, 16.5))
        prob_less_than_300 = scipy.stats.binom.sf(num_max + num_300 - 1, num_notes, ManiaScoreData.model_offset_prob(mean, stdev, 40.5))
        prob_less_than_200 = scipy.stats.binom.sf(num_max + num_300 + num_200 - 1, num_notes, ManiaScoreData.model_offset_prob(mean, stdev, 73.5))
        prob_less_than_100 = scipy.stats.binom.sf(num_max + num_300 + num_200 + num_100 - 1, num_notes, ManiaScoreData.model_offset_prob(mean, stdev, 103.5))
        prob_less_than_50  = scipy.stats.binom.sf(num_max + num_300 + num_200 + num_100 + num_50 - 1, num_notes, ManiaScoreData.model_offset_prob(mean, stdev, 127.5))

        return prob_less_than_max*prob_less_than_300*prob_less_than_200*prob_less_than_100*prob_less_than_50