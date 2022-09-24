import unittest
import pandas as pd

from osu_analysis.std.map_data import StdMapData
from osu_analysis.std.score_data import StdScoreData



class TestStdScoreDataFree(unittest.TestCase):

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
        ]
        cls.map_data = pd.concat(map_data, axis=0, keys=range(len(map_data)), names=[ 'hitobject', 'aimpoint' ])


    @classmethod
    def tearDown(cls):  
        pass


    def test_slider_start(self):
        settings = StdScoreData.Settings()

        for require_tap_press in [True, False]:
            for require_aim_press in [True, False]:
                for miss_aim in [True, False]:
                    cursor_xy = [500, 500] if miss_aim else [0, 0]

                    settings.require_tap_press = require_tap_press
                    settings.require_aim_press = require_aim_press
                    
                    # Set hitwindow ranges to what these tests have been written for
                    settings.neg_hit_miss_range = 450    # ms point of early miss window
                    settings.neg_hit_range      = 300    # ms point of early hit window
                    settings.pos_hit_range      = 300    # ms point of late hit window
                    settings.pos_hit_miss_range = 450    # ms point of late miss window

                    # Time:     0 ms -> 3000 ms
                    # Scoring:  Awaiting press at slider start (100 ms @ (0, 0))
                    for ms in range(0, 3000):
                        score_data = {}
                        
                        adv = StdScoreData._StdScoreData__process_free(settings, score_data, self.map_data.values, ms, cursor_xy[0], cursor_xy[1], [0, 0])
                        offset = ms - self.map_data.iloc[0]['time']

                        def proc_required():
                            # Regardless of whether aim is required, a tap is required and this got a free instead
                            if offset <= settings.pos_hit_miss_range:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')
                            else:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

                        def proc_required_non():
                            if offset < 0:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')
                            else:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                                self.assertEqual(score_data[0][6], StdScoreData.TYPE_HITP, f'Offset: {offset} ms')
 
                        if not require_aim_press and not require_tap_press:
                            # No need to tap or aim; Automatic freebie
                            proc_required_non()
                            continue

                        if not require_aim_press and require_tap_press:
                            proc_required()
                            continue
                        
                        if require_aim_press and not require_tap_press:
                            if miss_aim:
                                proc_required()
                            else:
                                proc_required_non()
                            continue
            
                        if require_aim_press and require_tap_press:
                            if miss_aim:
                                proc_required()
                            else:
                                proc_required()
                            continue


    def test_slider_hold(self):
        settings = StdScoreData.Settings()

        for require_tap_hold in [True, False]:
            for require_aim_hold in [True, False]:
                for recoverable_missaim in [True, False]:
                    for recoverable_release in [True, False]:
                        for slider_miss in [True, False]:
                            for miss_aim in [True, False]:
                                cursor_xy = [1000, 1000] if miss_aim else [0, 0]

                                settings.require_tap_hold    = require_tap_hold
                                settings.require_aim_hold    = require_aim_hold

                                settings.recoverable_missaim = recoverable_missaim
                                settings.recoverable_release = recoverable_release

                                settings.miss_slider         = slider_miss
                                
                                # Set hitwindow ranges to what these tests have been written for
                                self.neg_hld_range = 0  
                                self.pos_hld_range = 1000

                                # Time:     0 ms -> 3000 ms
                                # Scoring:  Awaiting hold at slider aimpoint (350 ms @ (100, 0))
                                for ms in range(0, 3000):
                                    score_data = {}

                                    adv = StdScoreData._StdScoreData__process_free(settings, score_data, self.map_data.iloc[1:].values, ms, cursor_xy[0], cursor_xy[1], [0, 0])
                                    offset = ms - self.map_data.iloc[1]['time']

                                    expected_miss_adv = StdScoreData._StdScoreData__ADV_NOTE if slider_miss else StdScoreData._StdScoreData__ADV_AIMP
                                    expected_late_timing = settings.pos_hld_range if recoverable_release else 0

                                    def proc_required():
                                        if offset <= expected_late_timing:
                                            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms  recoverable_missaim: {recoverable_missaim}  recoverable_release: {recoverable_release}   expected_late_timing: {expected_late_timing}')
                                            self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')
                                        else:
                                            self.assertEqual(adv, expected_miss_adv, f'Offset: {offset} ms  recoverable_missaim: {recoverable_missaim}  recoverable_release: {recoverable_release}   expected_late_timing: {expected_late_timing}')
                                            self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

                                    def proc_required_non():
                                        if offset < 0:
                                            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                                            self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')
                                        else:
                                            self.assertEqual(adv, StdScoreData._StdScoreData__ADV_AIMP, f'Offset: {offset} ms')
                                            self.assertEqual(score_data[0][6], StdScoreData.TYPE_AIMH, f'Offset: {offset} ms')

                                    if not require_aim_hold and not require_tap_hold:
                                        # No need to tap or aim; Automatic freebie
                                        proc_required_non()
                                        continue

                                    if not require_aim_hold and require_tap_hold:
                                        proc_required()
                                        continue
                                    
                                    if require_aim_hold and not require_tap_hold:
                                        if miss_aim:
                                            proc_required()
                                        else:
                                            proc_required_non()
                                        continue
                        
                                    if require_aim_hold and require_tap_hold:
                                        if miss_aim:
                                            proc_required()
                                        else:
                                            proc_required()
                                        continue


    def test_slider_release(self):
        settings = StdScoreData.Settings()

        for require_tap_release in [True, False]:
            for require_aim_release in [True, False]:
                for miss_aim in [True, False]:
                    cursor_xy = [1000, 1000] if miss_aim else [300, 0]

                    settings.require_tap_release = require_tap_release
                    settings.require_aim_release = require_aim_release
                    
                    # Set hitwindow ranges to what these tests have been written for
                    settings.neg_rel_miss_range = 450    # ms point of early miss window
                    settings.neg_rel_range      = 300    # ms point of early release window
                    settings.pos_rel_range      = 300    # ms point of late release window
                    settings.pos_rel_miss_range = 450    # ms point of late miss window
                    
                    # Time:     0 ms -> 3000 ms
                    # Scoring:  Awaiting release at slider end (750 ms @ (300, 0))
                    for ms in range(0, 3000):
                        score_data = {}

                        adv = StdScoreData._StdScoreData__process_free(settings, score_data, self.map_data.iloc[3:].values, ms, cursor_xy[0], cursor_xy[1], [0, 0])
                        offset = ms - self.map_data.iloc[3]['time']

                        def proc_required():
                            if offset <= settings.pos_rel_miss_range:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')
                            else:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')

                        def proc_required_non():
                            if offset < 0:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')    
                            else:
                                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                                self.assertEqual(score_data[0][6], StdScoreData.TYPE_HITR, f'Offset: {offset} ms') 

                        if not require_aim_release and not require_tap_release:
                            # No need to tap or aim; Automatic freebie
                            proc_required_non()
                            continue

                        if not require_aim_release and require_tap_release:
                            proc_required()
                            continue
                        
                        if require_aim_release and not require_tap_release:
                            if miss_aim:
                                proc_required()
                            else:
                                proc_required_non()
                            continue
            
                        if require_aim_release and require_tap_release:
                            if miss_aim:
                                proc_required()
                            else:
                                proc_required()
                            continue


    def test_circle_misaim(self):
        settings = StdScoreData.Settings()

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     0 ms -> 3000 ms
        # Location: Blank area (1000, 1000)
        # Scoring:  Awaiting press at 1st hitcircle (1000 ms @ (500, 500))
        for ms in range(0, 3000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_free(settings, score_data, self.map_data.iloc[4:].values, ms, 1000, 1000, [0, 0])
            
            offset = ms - self.map_data.iloc[4]['time']

            if offset <= settings.pos_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')
            else:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')


    def test_circle_nomisaim(self):
        settings = StdScoreData.Settings()

        # Set hitwindow ranges to what these tests have been written for
        settings.pos_hit_range      = 300    # ms point of late hit window
        settings.neg_hit_range      = 300    # ms point of early hit window
        settings.pos_hit_miss_range = 450    # ms point of late miss window
        settings.neg_hit_miss_range = 450    # ms point of early miss window
    
        settings.pos_rel_range       = 500   # ms point of late release window
        settings.neg_rel_range       = 500   # ms point of early release window
        settings.pos_rel_miss_range  = 1000  # ms point of late release window
        settings.neg_rel_miss_range  = 1000  # ms point of early release window

        # Time:     0 ms -> 3000 ms
        # Location: At 1st hitcircle (500, 500)
        # Scoring:  Awaiting press at 1st hitcircle (1000 ms @ (500, 500))
        for ms in range(0, 3000):
            score_data = {}
            adv = StdScoreData._StdScoreData__process_free(settings, score_data, self.map_data.iloc[4:].values, ms, 500, 500, [0, 0])
            
            offset = ms - self.map_data.iloc[4]['time']

            if offset <= settings.pos_hit_miss_range:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOP, f'Offset: {offset} ms')
                self.assertEqual(len(score_data), 0, f'Offset: {offset} ms')
            else:
                self.assertEqual(adv, StdScoreData._StdScoreData__ADV_NOTE, f'Offset: {offset} ms')
                self.assertEqual(score_data[0][6], StdScoreData.TYPE_MISS, f'Offset: {offset} ms')
