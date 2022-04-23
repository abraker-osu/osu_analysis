import unittest
import pandas as pd

from analysis.std.map_data import StdMapData
from analysis.std.score_data import StdScoreData



class TestStdScoreDataPress(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        map_data = [ 
            pd.DataFrame(
            [
                [ 100, 0,   0, StdMapData.TYPE_PRESS, StdMapData.TYPE_SLIDER ],
                [ 350, 100, 0, StdMapData.TYPE_HOLD, StdMapData.TYPE_SLIDER ],
                [ 600, 200, 0, StdMapData.TYPE_HOLD, StdMapData.TYPE_SLIDER ],
                [ 750, 300, 0, StdMapData.TYPE_RELEASE, StdMapData.TYPE_SLIDER ],
            ],
            columns=['time', 'x', 'y', 'type', 'object']),
            pd.DataFrame(
            [ 
                [ 1000, 500, 500, StdMapData.TYPE_PRESS, StdMapData.TYPE_CIRCLE ],
                [ 1001, 500, 500, StdMapData.TYPE_RELEASE, StdMapData.TYPE_CIRCLE ],
            ],
            columns=['time', 'x', 'y', 'type', 'object']),
            pd.DataFrame(
            [ 
                [ 2000, 300, 300, StdMapData.TYPE_PRESS, StdMapData.TYPE_CIRCLE ],
                [ 2001, 300, 300, StdMapData.TYPE_RELEASE, StdMapData.TYPE_CIRCLE ],
            ],
            columns=['time', 'x', 'y', 'type', 'object']),
            pd.DataFrame(
            [
                [ 3100, 0,   0, StdMapData.TYPE_PRESS, StdMapData.TYPE_SLIDER ],
                [ 3350, 100, 0, StdMapData.TYPE_HOLD, StdMapData.TYPE_SLIDER ],
                [ 3600, 200, 0, StdMapData.TYPE_HOLD, StdMapData.TYPE_SLIDER ],
                [ 3750, 300, 0, StdMapData.TYPE_RELEASE, StdMapData.TYPE_SLIDER ],
            ],
            columns=['time', 'x', 'y', 'type', 'object']),
        ]
        cls.map_data = pd.concat(map_data, axis=0, keys=range(len(map_data)), names=[ 'hitobject', 'aimpoint' ])


    @classmethod
    def tearDown(cls):  
        pass


    def test_slider_start_press_misaim__noblank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = False

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: Blank area (1000, 1000)
        # Scoring:  Awaiting press at slider start (100 ms @ (0, 0))
        # Behavior:
        #   Scorepoint awaits PRESS -> NOP
        #   -> NOP
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.values, ms, 1000, 1000, [0, 0])
            
            offset = ms - self.map_data.iloc[0]['time']

            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
            self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')


    def test_slider_start_press_nomissaim__noblank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = False

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: At slider start (0, 0)
        # Scoring:  Awaiting press at slider start (100 ms @ (0, 0))
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.values, ms, 0, 0, [0, 0])
            
            offset = ms - self.map_data.iloc[0]['time']

            if offset <= -settings.neg_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            elif -settings.neg_hit_miss_range < offset <= -settings.neg_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif -settings.neg_hit_range < offset <= settings.pos_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_AIMP, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_HITP, f'Offset: {offset} ms')

            elif settings.pos_hit_range < offset <= settings.pos_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif settings.pos_hit_miss_range < offset:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            else:
                self.fail('Testing error!')


    def test_slider_aimpoint_press_misaim__noblank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = False

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: Blank area (1000, 1000)
        # Scoring:  Awaiting hold at scorepoint (350 ms @ (100, 0))
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.iloc[1:].values, ms, 1000, 1000, [0, 0])
            
            offset = ms - self.map_data.iloc[1]['time']

            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
            self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')


    def test_slider_aimpoint_press_nomissaim__noblank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = False

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: At scorepoint (100, 0)
        # Scoring:  Awaiting hold at scorepoint (350 ms @ (100, 0))
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.iloc[1:].values, ms, 100, 0, [0, 0])
            
            offset = ms - self.map_data.iloc[1]['time']

            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
            self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')


    def test_circle_press_missaim__noblank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = False

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: Blank area (1000, 1000)
        # Scoring:  Awaiting press at hitcircle (1000 ms @ (500, 500))
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.iloc[4:].values, ms, 1000, 1000, [0, 0])
            
            offset = ms - self.map_data.iloc[4]['time']

            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
            self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')


    def test_circle_press_missaim__noblank__100window(self):
        settings = StdScoreData.Settings()

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 100    # ms point of late hit window
        settings.neg_hit_range      = 100    # ms point of early hit window
        settings.pos_hit_miss_range = 100    # ms point of late miss window
        settings.neg_hit_miss_range = 100    # ms point of early miss window

        # Time:     -1000 ms -> 4000 ms
        # Location: On hit circle (500, 500)
        # Scoring:  Awaiting press at hitcircle (1000 ms @ (500, 500))
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.iloc[4:].values, ms, 500, 500, [0, 0])
            
            offset = ms - self.map_data.iloc[4]['time']

            if offset <= -settings.neg_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            elif -settings.neg_hit_miss_range < offset <= -settings.neg_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif -settings.neg_hit_range < offset <= settings.pos_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_HITP, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][0] - score_data[0][1], offset, f'Offset: {offset} ms')

            elif settings.pos_hit_range < offset <= settings.pos_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif settings.pos_hit_miss_range < offset:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            else:
                self.fail('Testing error!')


    def test_circle_press_missaim__blank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = True
        
        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: Blank area (1000, 1000)
        # Scoring:  Awaiting press at hitcircle (1000 ms @ (500, 500))
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.iloc[4:].values, ms, 1000, 1000, [0, 0])
            
            offset = ms - self.map_data.iloc[4]['time']

            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
            self.assertEqual(score_data[0][6], StdScoreData.TYPE_EMPTY)


    def test_circle_press_nomissaim__noblank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = False

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: At 1st hit circle (500, 500)
        # Scoring:  Awaiting press at hitcircle (1000 ms @ (500, 500))
        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.iloc[4:].values, ms, 500, 500, [0, 0])
            
            offset = ms - self.map_data.iloc[4]['time']

            if offset <= -settings.neg_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            elif -settings.neg_hit_miss_range < offset <= -settings.neg_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif -settings.neg_hit_range < offset <= settings.pos_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_HITP, f'Offset: {offset} ms')

            elif settings.pos_hit_range < offset <= settings.pos_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif settings.pos_hit_miss_range < offset:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            else:
                self.fail('Testing error!')


    def test_slider_press_nomissaim__noblank(self):
        settings = StdScoreData.Settings()
        settings.blank_miss = False

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     -1000 ms -> 4000 ms
        # Location: At 2st slider (500, 500)
        # Scoring:  Awaiting press at slider (3100 ms @ (0, 0))

        for ms in range(-1000, 4000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_press(settings, score_data, self.map_data.iloc[8:].values, ms, 0, 0, [0, 0])
            
            offset = ms - self.map_data.iloc[8]['time']

            if offset <= -settings.neg_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            elif -settings.neg_hit_miss_range < offset <= -settings.neg_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif -settings.neg_hit_range < offset <= settings.pos_hit_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_AIMP, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_HITP, f'Offset: {offset} ms')

            elif settings.pos_hit_range < offset <= settings.pos_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

            elif settings.pos_hit_miss_range < offset:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')

            else:
                self.fail('Testing error!')
