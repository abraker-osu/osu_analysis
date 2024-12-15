import math
import numpy as np
import pandas as pd

from osu_interfaces import IBeatmap
from osu_interfaces import IReplay
from osu_interfaces import IHitobject



class ManiaActionData(np.ndarray):

    IDX_STIME = 0
    IDX_ETIME = 1
    IDX_COL   = 2

    FREE    = 0  # Finger free to float
    PRESS   = 1  # Finger must impart force to press key
    HOLD    = 2  # Finger must keep imparting force to keep key down
    RELEASE = 3  # Finger must depart force to unpress key

    @staticmethod
    def get_action_data(data):
        if isinstance(data, IBeatmap):
            return ManiaActionData.__init_beatmap(data)

        if isinstance(data, IReplay):
            return ManiaActionData.__init_replay(data)

        raise TypeError(f'Unsupported data type: {type(data)}')

    
    @staticmethod
    def __init_beatmap(beatmap):
        hitobjects = beatmap.get_hitobjects()
        
        if len(hitobjects) < 1: 
            raise ValueError('Empty beatmap!')

        if not isinstance(hitobjects[0], IHitobject):
            raise TypeError(f'get_hitobject() returned a non IHitobject type: {type(hitobjects[0])}')

        map_data = np.empty((len(hitobjects), 3))
        max_col = 0
        
        for i in range(len(hitobjects)):
            # Extract note timings
            note_start = hitobjects[i].start_time()
            note_end   = hitobjects[i].end_time()
            col        = hitobjects[i].pos_x()

            max_col = max(col, max_col)
            map_data[i] = [ note_start, note_end, col ]
        
        return map_data


    @staticmethod
    def __init_replay(replay, cols=None):
        """
        [
            [ col1_state, col2_state, ..., colN_state ],
            [ col1_state, col2_state, ..., colN_state ],
            [ col1_state, col2_state, ..., colN_state ],
            ... 
        ]
        """
        if cols == None:
            cols = replay.get_mania_keys()
            if cols == None:
                raise TypeError('Not a mania replay!')

        # Keep track of timing
        timing = 0

        # Previous state of whether finger is holding key down
        hold_state = np.asarray([ None for _ in range(cols) ])

        replay_data = []

        data = zip(replay.get_time_data(), replay.get_xpos_data())
        for tdelta, key_press in data:
            timing += tdelta

            for col in range(cols):
                is_key_hold = (int(key_press) & (1 << col)) > 0
                
                if hold_state[col] != None and not is_key_hold:
                    replay_data.append([ hold_state[col], timing, col ])
                    hold_state[col] = None
                elif hold_state[col] == None and is_key_hold:
                    hold_state[col] = timing

        return np.asarray(replay_data)


    @staticmethod
    def num_keys(action_data):
        """
        Gets number of keys according to the given ``action_data``

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        int
        Number of keys
        """
        if action_data.shape[0] == 0:
            return 0

        return int(np.max(action_data[:, ManiaActionData.IDX_COL]) - np.min(action_data[:, ManiaActionData.IDX_COL])) + 1


    @staticmethod
    def press_times(action_data):
        """
        Gets list of press timings in ``action_data`` for column ``col``

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        Press timings
        """
        return action_data[:, ManiaActionData.IDX_STIME]


    @staticmethod
    def is_single_note(action_data):
        """
        Gets a mask of single notes ``action_data``

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        Press timings
        """
        return (action_data[:, ManiaActionData.IDX_ETIME] - action_data[:, ManiaActionData.IDX_STIME]) <= 1
        

    @staticmethod
    def release_times(action_data):
        """
        Gets list of release timings in ``action_data`` for column ``col``

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        col : int
            Column to get timings for

        Returns
        -------
        numpy.array
        Release timings
        """
        return action_data[:, ManiaActionData.IDX_ETIME]


    @staticmethod
    def split_by_hand(action_data, left_handed=True):
        """
        Splits ``action_data`` into left and right hands

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        left_handed : bool
            Whether to prefer spliting odd even keys for left hand or right hand.
            If ``True`` then left hand. If ``False`` then right hand.

        Returns
        -------
        (numpy.array, numpy.array)
        A tuple of ``action_data`` for left hand and right hand
        """
        keys = ManiaActionData.num_keys(action_data)
        left_half = math.ceil(keys/2) if left_handed else math.floor(keys/2)

        left_mask = action_data[:, ManiaActionData.IDX_COL] < left_half
        right_mask = action_data[:, ManiaActionData.IDX_COL] >= left_half

        return action_data[left_mask], action_data[right_mask]


    @staticmethod
    def get_actions_between(action_data, ms_start, ms_end):
        """
        Gets a slice of ``action_data`` between ``ms_start`` and ``ms_end``, inclusively

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        ms_start : int
            Starting time of milliseconds in action data in which to get actions for

        ms_end : int
            Ending time in milliseconds of data in action data in which to get actions for

        Returns
        -------
        numpy.array
        ``action_data`` slice of data between the times specified
        """
        timing_mask = (ms_start <= action_data[:, ManiaActionData.IDX_STIME]) & (action_data[:, ManiaActionData.IDX_STIME] <= ms_end)

        return action_data[timing_mask].shape[0]


    @staticmethod
    def get_idx_col_sort(action_data):
        """
        Returns a column-start time sorted index map

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        ``action_data`` slice of data between the times specified
        """
        idx_map = np.arange(action_data.shape[0])
        col_max = int(np.max(action_data[:, ManiaActionData.IDX_COL]))

        for c in range(col_max):
            map_col_mask = action_data[:, ManiaActionData.IDX_COL] == c
            idx_sort = action_data[map_col_mask][:, ManiaActionData.IDX_STIME].argsort()

            idx_map[map_col_mask] = idx_map[map_col_mask][idx_sort]

        return idx_map
            