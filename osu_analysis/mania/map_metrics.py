import numpy as np
from scipy import signal

from ..utils import prob_trials
from .action_data import ManiaActionData



class ManiaMapMetrics():

    """
    Raw metrics
    """
    @staticmethod
    def calc_press_rate(action_data, col=None, window_ms=1000):
        """
        Calculates presses per second across all columns within indicated ``window_ms`` of time.
        Has a moving that shifts to next note occuring on new timing

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaMapData.get_action_data``

        col : int
            Column to calculated presses per second for

        window_ms : int
            Duration in milliseconds for which actions are counted up

        Returns
        -------
        (numpy.array, numpy.array)
        Tuple of ``(times, aps)``. ``times`` are timings corresponding to recorded actions per second. 
            ``aps`` are actions per second at indicated time.
        """
        times, aps = [], []

        if type(col) != type(None):
            action_data = action_data[action_data[:, ManiaActionData.IDX_COL] == col]

        aps = np.zeros((action_data.shape[0],))

        for i in range(action_data.shape[0]):
            timing = action_data[i, ManiaActionData.IDX_STIME]
            start_times = action_data[:, ManiaActionData.IDX_STIME]

            time_window_mask = (timing - window_ms <= start_times) & (start_times < timing)
            num_actions = time_window_mask.sum()
            
            aps[i] = 1000*num_actions/window_ms

        return np.arange(action_data.shape[0]), aps


    @staticmethod
    def calc_note_intervals(action_data, col):
        """
        Gets the duration (time interval) between each note in the specified ``col``

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        col : int
            Which column number to get note intervals for

        Returns
        -------
        (numpy.array, numpy.array)
            Tuple of ``(start_times, intervals)``. ``start_times`` are timings corresponding to start of notes. 
            ``intervals`` are the timings difference between current and previous notes' starting times. 
            Resultant array size is ``len(hitobject_data) - 1``.
        """
        if type(col) != type(None):
            action_data = action_data[action_data[:, ManiaActionData.IDX_COL] == col]

        return np.arange(1, action_data.shape[0]), np.diff(action_data[:, ManiaActionData.IDX_STIME])


    @staticmethod
    def calc_max_press_rate_per_col(action_data, window_ms=1000):
        """
        Takes which column has max presses per second within indicated ``window_ms`` of time

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaMapData.get_action_data``

        window_ms : int
            Duration in milliseconds for which actions are counted up

        Returns
        -------
        (numpy.array, numpy.array)
        Tuple of ``(times, max_aps_per_col)``. ``times`` are timings corresponding to recorded actions per second. 
            ``max_aps_per_col`` are max actions per second at indicated time.
        """
        aps = np.zeros((action_data.shape[0],))
        times = action_data[:, ManiaActionData.IDX_STIME]

        # iterate through timings
        for i in range(action_data.shape[0]):
            timing = action_data[i, ManiaActionData.IDX_STIME]
            
            max_col = int(max(action_data[:, ManiaActionData.IDX_COL]))
            aps_per_col = np.zeros((max_col, ))

            # iterate through columns
            for col in range(max_col):
                col_mask = action_data[:, ManiaActionData.IDX_COL] == col
                start_times = action_data[col_mask][:, ManiaActionData.IDX_STIME]

                time_window_mask = (timing - window_ms <= start_times) & (start_times < timing)
                num_actions = time_window_mask.sum()

                aps_per_col[col] = 1000*num_actions/window_ms
            
            aps[i] = max(aps_per_col)

        return times, aps


    @staticmethod
    def detect_presses_during_holds(action_data):
        """
        Masks presses that occur when there is at least one hold in one of the columns

        This is useful for determining which presses are harder due to finger independence.
        Holds have a tendency to make affected fingers slower or less accurate to press.

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        action_data mask of actions detected
        """
        ret = np.zeros((action_data.shape[0], ), dtype=bool)

        # If there are no hold notes present, then the entire mask should be 0
        hold_mask = (action_data[:, ManiaActionData.IDX_ETIME] - action_data[:, ManiaActionData.IDX_STIME]) > 1
        if not np.any(hold_mask):
            return ret

        # These indices will be uses as references as to where place data in ret
        idx_ref = np.arange(action_data.shape[0])
                
        # Convenience vars
        ts = action_data[:, ManiaActionData.IDX_STIME]  # Hold note start times
        te = action_data[:, ManiaActionData.IDX_ETIME]  # Hold note end times
        ky = action_data[:, ManiaActionData.IDX_COL]    # Hold note column

        # Operate on data in chunks to limit memory usage when using meshgrid
        for i in range(0, action_data.shape[0], 500):
            # Get a chunk of data to operate on
            idx_start = i
            idx_end   = min(action_data.shape[0], i+1000)
            idx = idx_ref[idx_start : idx_end]
            
            # Used to operate every note on every other note
            a, b = np.meshgrid(idx, idx)
            data = np.ones((idx.shape[0], idx.shape[0], ), dtype=bool)

            # Checks if note b's start time is between note a's start and end times 
            data &= (ts[a] < ts[b]) & (ts[b] < te[a])

            # Check if notes are neigboring and are not themselves
            data &= np.abs(ky[a] - ky[b]) == 1

            # Check if any of the notes satisfy these conditions
            ret[idx] |= np.any(data, axis=1)
        
        return ret


    @staticmethod
    def detect_holds_during_release(action_data):
        """
        Masks holds that occur when there is at least one release in one of the columns

        This is useful for determining which holds are harder due to finger independence.
        Releases have a tendency to make affected fingers release prematurely.

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        action_data mask of actions detected
        """
        ret = np.zeros((action_data.shape[0], ), dtype=bool)

        # If there are no hold notes present, then the entire mask should be 0
        hold_mask = (action_data[:, ManiaActionData.IDX_ETIME] - action_data[:, ManiaActionData.IDX_STIME]) > 1
        if not np.any(hold_mask):
            return ret

        # These indices will be uses as references as to where place data in ret
        idx_ref = np.arange(action_data.shape[0])

        # Filter out non holds
        idx_ref = idx_ref[hold_mask]

        # Convenience vars
        ts = action_data[:, ManiaActionData.IDX_STIME]  # Hold note start times
        te = action_data[:, ManiaActionData.IDX_ETIME]  # Hold note end times
        ky = action_data[:, ManiaActionData.IDX_COL]    # Hold note column

        # Operate on data in chunks to limit memory usage when using meshgrid
        for i in range(0, action_data.shape[0], 500):
            # Get a chunk of data to operate on
            idx_start = i
            idx_end   = min(action_data.shape[0], i+1000)
            idx = idx_ref[idx_start : idx_end]

            # Used to operate every note on every other note
            a, b = np.meshgrid(idx, idx)
            data = np.ones((idx.shape[0], idx.shape[0], ), dtype=bool)

            # Checks if note b's end time is between note a's start and end times 
            data &= (ts[a] < te[b]) & (te[b] < te[a])

            # Check if notes are neigboring and are not themselves
            data &= np.abs(ky[a] - ky[b]) == 1

            # Check if any of the notes satisfy these conditions
            # 0 and 1 axis are or'd to capture matches from both notes
            ret[idx] |= np.any(data, axis=0) | np.any(data, axis=1)

        return ret


    @staticmethod
    def detect_hold_notes(action_data):
        """
        Masks hold notes; removes single notes from data.

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        action_data An array consiting of 1 if note is hold note and 0 if note is single note
        """
        return (action_data[:, ManiaActionData.IDX_ETIME] - action_data[:, ManiaActionData.IDX_STIME]) > 1


    @staticmethod
    def detect_simultaneous_notes(action_data):
        """
        Masks hold notes; removes single notes from data.

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        action_data An array consiting of 1 if note is hold note and 0 if note is single note
        """
        ret = np.zeros((action_data.shape[0], ), dtype=bool)

        # These indices will be uses as references as to where place data in ret
        idx_ref = np.arange(action_data.shape[0])

        # Convenience vars
        ts = action_data[:, ManiaActionData.IDX_STIME]  # Hold note start times
        te = action_data[:, ManiaActionData.IDX_ETIME]  # Hold note end times
        ky = action_data[:, ManiaActionData.IDX_COL]    # Hold note column

        # Operate on data in chunks to limit memory usage when using meshgrid
        for i in range(0, action_data.shape[0], 500):
            # Get a chunk of data to operate on
            idx_start = i
            idx_end   = min(action_data.shape[0], i+1000)
            idx = idx_ref[idx_start : idx_end]

            # Used to operate every note on every other note
            a, b = np.meshgrid(idx, idx, sparse=True)
            data = np.ones((idx.shape[0], idx.shape[0], ), dtype=bool)

            # Check if note A ends before or at when note B ends
            data &= te[a] <= te[b]

            # Check if note A start after or at when note B starts
            data &= ts[a] >= ts[b]

            # Check if notes A and B are on different columns
            data &= ky[a] != ky[b]

            # Check if any of the notes satisfy these conditions
            ret[idx] |= np.any(data, axis=0) | np.any(data, axis=1)

        return ret


    @staticmethod
    def hold_durations(action_data):
        """
        Durations the notes are pressed for

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        action_data with hold note durations
        """
        return action_data[:, ManiaActionData.IDX_ETIME] - action_data[:, ManiaActionData.IDX_STIME]


    @staticmethod
    def anti_press_durations(action_data):
        """
        Takes action_data, and reduces them to durations of anti-presses. Anti-presses
        are associated with points in LN type patterns where there is a spot between 
        two holdnotes where the finger is released. 

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        action_data with hold note durations
        """
        ret = np.empty(action_data.shape[0])
        col_max = int(np.max(action_data[:, ManiaActionData.IDX_COL]))
        idx_sort = ManiaActionData.get_idx_col_sort(action_data)

        for c in range(col_max):
            map_col_mask = action_data[:, ManiaActionData.IDX_COL] == c
            map_col  = action_data[map_col_mask]
            col_sort = idx_sort[idx_sort < map_col.shape[0]]

            map_col = map_col[col_sort]

            intervals = np.zeros(map_col.shape[0])
            intervals[1:] = map_col[1:, ManiaActionData.IDX_STIME] - map_col[:-1, ManiaActionData.IDX_ETIME]

            ret[map_col_mask] = intervals[col_sort]

        return ret        


    @staticmethod
    def press_durations(action_data):
        """
        Time intervals since last press.
        
        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        action_data with intervals between presses
        """
        cols_unique = np.unique(action_data[:, ManiaActionData.IDX_COL])
        
        ret_dur = np.zeros((action_data.shape[0] - cols_unique.shape[0], ))
        ret_idx = np.zeros((action_data.shape[0] - cols_unique.shape[0], ))

        idx = 0

        for col_idx in cols_unique:
            map_col_filter = action_data[:, ManiaActionData.IDX_COL] == col_idx
            map_col = action_data[map_col_filter]

            col_sort = map_col[:, ManiaActionData.IDX_STIME].argsort(axis=0)
            map_col = map_col[col_sort]
            
            durations = map_col[1:, ManiaActionData.IDX_STIME] - map_col[:-1, ManiaActionData.IDX_STIME]
            cols_sort_mask = col_sort < col_sort.shape[0] - 1  # Filter out last idx since durations omit last one

            ret_dur[idx : idx + durations.shape[0]] = durations
            ret_idx[idx : idx + durations.shape[0]] = col_sort[cols_sort_mask] + idx

            idx += durations.shape[0]
        
        return ret_idx, ret_dur


    @staticmethod
    def detect_inverse(action_data):
        """
        Masks notes that are detected as or part of inverse patterns

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        mask_data mask of notes detected
        """
        ret = np.zeros((action_data.shape[0], ), dtype=bool)

        # Filter out non hold notes
        hold_mask = (action_data[:, ManiaActionData.IDX_ETIME] - action_data[:, ManiaActionData.IDX_STIME]) > 1
        if not np.any(hold_mask):
            return ret

        # Filter out notes where player doesn't need to press multiple notes
        simul_mask = ManiaMapMetrics.detect_simultaneous_notes(action_data)
        if not np.any(simul_mask):
            return ret

        # These indices will be uses as references as to where place data in ret
        idx_ref = np.arange(action_data.shape[0])

        # Convenience vars
        ts = action_data[:, ManiaActionData.IDX_STIME]  # Hold note start times
        te = action_data[:, ManiaActionData.IDX_ETIME]  # Hold note end times
        ky = action_data[:, ManiaActionData.IDX_COL]    # Hold note column

        # Operate on data in chunks to limit memory usage when using meshgrid
        # Each iteration processes a bit more than the chunk specified to have some
        # overlap between chunks. This all combination of notes are actually processed.
        # For example, if you take chunks (0 - 100) and (100 - 200), there could be notes
        # that make up the desired pattern spread between indices 99, 100, and 101, but if
        # there is no overlap, then 99 would never be processed together with 100 and 101.
        chunk = 300               # 1 chunk = 300 notes = 300x300x300x4 bytes = ~103 Mb
        chunk += int(chunk*0.5)   # + 50% overlap between chunks = ~348 Mb

        full_data = np.ones((chunk, chunk, chunk), dtype=bool)

        # Iterate though the chunks
        for i in range(0, action_data.shape[0], chunk):
            # Get a chunk of data to operate on
            idx_start = i
            idx_end   = min(action_data.shape[0], i+chunk)
            idx = idx_ref[idx_start : idx_end]

            # Prepare data
            data = full_data[:idx.shape[0], :idx.shape[0], :idx.shape[0]]
            data[:, :, :] = 1

            # Used to operate every note on every other note
            a, b, c = np.meshgrid(idx, idx, idx, sparse=True)
            
            # Checks if note B's end time is while note A is being held down
            data &= (ts[a] < te[b]) & (te[b] < te[a])

            # Checks if note C's start time is while note A is being held down
            data &= (ts[a] < ts[c]) & (ts[c] < te[a])

            # Checks if note B's end time is before note C's start time
            data &= (te[b] < ts[c])

            # Checks if note B is hold note
            data &= (te[b] - ts[b]) > 16

            # Checks if note C is hold note
            data &= (te[c] - ts[c]) > 16

            # Check if notes A and B are neigboring and are not themselves
            data &= np.abs(ky[a] - ky[b]) == 1

            # Check if notes A and C are neigboring and are not themselves
            data &= np.abs(ky[a] - ky[c]) == 1

            # Check if notes B and C are neigboring and on same column
            data &= ky[b] == ky[c]

            # Check if any of the notes satisfy these conditions
            # (1, 2), (0, 1), and (0, 2) are or'd to capture all reflexive matches (matches from perspective of each of the 3 notes)
            ret[idx] |= np.any(data, axis=(1, 2)) | np.any(data, axis=(0, 1)) | np.any(data, axis=(0, 2))

        return ret


    @staticmethod
    def detect_chords(action_data):
        """
        Masks notes that are detected as or part of chord patterns

        A chord must satisfy the following conditions:
        * notes composing the chord must all occur at same time
        * notes composing the chord must all occur at different columns
        * if notes prior to the chord exist, one of those notes must jack with at least one of the notes the chord is composed of
        * if notes later to the chord exist, one of those notes must jack with at least one of the notes the chord is composed of

        The last 2 requirements prevent parts of alternating patterns, trills, and rolls from being detected as chords

        Parameters
        ----------
        action_data : numpy.array
            Action data from ``ManiaActionData.get_action_data``

        Returns
        -------
        numpy.array
        mask_data mask of notes detected
        """
        ret = np.zeros((action_data.shape[0], ), dtype=bool)

        # Convenience vars
        ts = action_data[:, ManiaActionData.IDX_STIME]  # note start times
        te = action_data[:, ManiaActionData.IDX_ETIME]  # note end times
        ky = action_data[:, ManiaActionData.IDX_COL]    # note column

        for i in range(action_data.shape[0]):
            # Find notes that occur at same time as current note
            # but at different column (to prevent same note matching)
            chord = (ts == ts[i]) & (ky != ky[i])

            # If no notes occur at this time, continue
            if not np.any(chord): continue

            # Column data for notes composing the chord 
            # (excluding current note), rotated 90 deg for broadcasting
            key_chord = ky[chord].reshape((ky[chord].shape[0], 1))
    
            # If applicable, find closest preceding notes
            closest_prv = ts[ts[i] > ts]
            if closest_prv.shape[0] != 0:
                closest_prv = (ts == closest_prv[-1])

                # One of prev notes must jack with one of the notes the chord consists of
                if np.all(ky[closest_prv] != ky[i]) and np.all(ky[closest_prv] != key_chord): 
                    continue

            # If applicable, find closest leading notes
            closest_nxt = ts[ts[i] < ts]
            if closest_nxt.shape[0] != 0:
                closest_nxt = (ts == closest_nxt[0])

                # One of next notes must jack with one of the notes the chord consists of
                if np.all(ky[closest_nxt] != ky[i]) and np.all(ky[closest_nxt] != key_chord): 
                    continue
            
            ret[i] = 1

        return ret
