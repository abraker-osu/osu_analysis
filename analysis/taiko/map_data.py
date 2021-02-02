import numpy as np

from osu.local.beatmap.beatmap_utility import BeatmapUtil
from misc.numpy_utils import NumpyUtils



class MapData():

    TIME = 0
    TYPE = 1

    @staticmethod
    def get_data_before(hitobject_data, time):
        idx_time = hitobject_data.get_idx_start_time(time)

        if not idx_time: return None
        if idx_time < 1: return None

        return hitobject_data.hitobject_data[idx_time - 1][-1]


    @staticmethod
    def get_data_after(hitobject_data, time):
        idx_time = hitobject_data.get_idx_end_time(time)
        
        if not idx_time:                       return None
        if idx_time > len(hitobject_data) - 2: return None
            
        return hitobject_data.hitobject_data[idx_time + 1][0]


    @staticmethod
    def time_slice(hitobject_data, start_time, end_time):
        start_idx = hitobject_data.get_idx_start_time(start_time)
        end_idx   = hitobject_data.get_idx_end_time(end_time)

        return hitobject_data.hitobject_data[start_idx:end_idx]


    '''
    [
        [ 
            [ time, type ],
            [ time, type ],
            ... N score points
        ],
        [ 
            [ time, type ],
            [ time, type ],
            ... N score points
        ],
        ...  N hitobjects
    ]
    '''
    def __init__(self):
        self.set_data_raw([])


    def __len__(self):
        return len(self.hitobject_data)


    def set_data_hitobjects(self, hitobjects):
        self.hitobject_data = [ hitobject.raw_data() for hitobject in hitobjects ]
        return self


    def set_data_raw(self, raw_data):
        self.hitobject_data = raw_data
        return self


    def append_to_end(self, raw_data, is_part_of_hitobject=False):
        if raw_data == None:   return
        if len(raw_data) == 0: return
    
        if is_part_of_hitobject: self.hitobject_data[-1].append(raw_data)
        else:                    self.hitobject_data.append([ raw_data ])


    def append_to_start(self, raw_data, is_part_of_hitobject=False):
        if raw_data == None:   return
        if len(raw_data) == 0: return
        
        if is_part_of_hitobject: self.hitobject_data[0].insert(0, raw_data)
        else:                    self.hitobject_data.insert(0, [ raw_data ])


    def start_times(self):
        return np.array([ note[0][MapData.TIME] for note in self.hitobject_data ])


    def end_times(self):
        return np.array([ note[-1][MapData.TIME] for note in self.hitobject_data ])


    def start_positions(self):
        return np.array([ note[0][MapData.POS] for note in self.hitobject_data ])

    
    def end_positions(self):
        return np.array([ note[-1][MapData.POS] for note in self.hitobject_data ])

    
    def all_positions(self, flat=True):
        if flat: return np.array([ data[MapData.POS] for note in self.hitobject_data for data in note ])
        else:    return [[data[MapData.POS] for data in note] for note in self.hitobject_data]


    def all_times(self, flat=True):
        if flat: return np.array([ data[MapData.TIME] for note in self.hitobject_data for data in note ])
        else:    return [[data[MapData.TIME] for data in note] for note in self.hitobject_data]


    def start_end_times(self):
        all_times = self.all_times(flat=False)
        return [ (hitobject_times[0], hitobject_times[-1]) for hitobject_times in all_times ]


    def get_idx_start_time(self, time):
        if not time: return None

        times = np.array(self.start_times())
        return min(max(0, np.searchsorted(times, [time], side='right')[0] - 1), len(times))


    def get_idx_end_time(self, time):
        if not time: return None
            
        times = np.array(self.end_times())
        return min(max(0, np.searchsorted(times, [time], side='right')[0] - 1), len(times))


MapData.full_hitobject_data = MapData()