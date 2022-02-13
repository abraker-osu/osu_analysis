from enum import Enum
import numpy as np
import pandas as pd
import scipy.stats

from .map_data import StdMapData
from .replay_data import StdReplayData
from .replay_metrics import StdReplayMetrics

import time


class StdScoreDataEnums(Enum):

    TIME          = 0
    POS           = 1
    HIT_OFFSET    = 2
    POS_OFFSET    = 3
    HITOBJECT_IDX = 4


class StdScoreData():
    """
    Class used for analyzing score data pertaining to a specific play.
    """
    __ADV_NOP  = 0  # Used internal by scoring processor; Don't advance
    __ADV_AIMP = 1  # Used internal by scoring processor; Advance to next aimpoint
    __ADV_NOTE = 2  # Used internal by scoring processor; Advance to next note

    TYPE_HITP  = 0  # A hit press has a hitobject and offset associated with it
    TYPE_HITR  = 1  # A hit release has a hitobject and offset associated with it
    TYPE_AIMH  = 2  # A hold has an aimpoint and offset associated with it
    TYPE_MISS  = 3  # A miss has a hitobject associated with it, but not offset
    TYPE_EMPTY = 4  # An empty has neither hitobject nor offset associated with it

    ACTION_FREE    = StdReplayData.FREE
    ACTION_PRESS   = StdReplayData.PRESS
    ACTION_HOLD    = StdReplayData.HOLD
    ACTION_RELEASE = StdReplayData.RELEASE

    DATA_OFFSET  = 0 
    DATA_TYPE    = 1
    DATA_MAP_IDX = 2

    class Settings():

        def __setattr__(self, key, value):
            try:
                if not self.__is_frozen:
                    object.__setattr__(self, key, value)
                    return
            except AttributeError:
                object.__setattr__(self, '_Settings__is_frozen', False)
                object.__setattr__(self, key, value)
                return

            if not hasattr(self, key):
                raise KeyError( f'Setting {key} does not exist!')
            
            if key == '__is_frozen':
                raise KeyError( f'__is_frozen is value locked!')

            object.__setattr__(self, key, value)


        def __init__(self):
            self.__is_frozen = False

            '''
            The following must be true:
                0 < pos_hit_range < pos_hit_miss_range < inf
                0 < neg_hit_range < neg_hit_miss_range < inf

            Hit processing occurs:
                -neg_hit_range -> pos_hit_range

            Miss processing occurs:
                -neg_hit_miss_range -> neg_hit_range
                pos_hit_range -> pos_hit_miss_range

            No processing occurs:
                -inf -> -neg_hit_miss_range
                pos_hit_miss_range -> inf
            '''

            """
            Press window
            """
            self.neg_hit_miss_range = 200   # ms point of early miss window
            self.neg_hit_range      = 100   # ms point of early hit window
            self.pos_hit_range      = 100   # ms point of late hit window
            self.pos_hit_miss_range = 200   # ms point of late miss window
            
            """
            Release window
            """
            self.neg_rel_miss_range = 1000  # ms point of early release miss window
            self.neg_rel_range      = 500   # ms point of early release window
            self.pos_rel_range      = 500   # ms point of late release window
            self.pos_rel_miss_range = 1000  # ms point of late release miss window

            """
            Hold window
            """
            self.neg_hld_range      = 0     # ms range of early hold
            self.pos_hld_range      = 1000  # ms range of late hold (this MUST not be greater than pos_rel_miss_range)

            """
            Press aim window
            """
            self.hitobject_radius = 36.5    # Radius from hitobject for which cursor needs to be within for a tap to count

            """
            Release aim window
            """
            self.release_radius = 100       # Radius from release aimpoint for which cursor needs to be within for a release to count

            """
            Hold aim window
            """
            self.follow_radius = 100        # Radius from slider aimpoint for which cursor needs to be within for a hold to count
            

            self.ar_ms = 450                # Number of milliseconds back in time the hitobject first becomes visible

            """
            Disables hit processing if hit on a note is too early. If False, the neg_miss_range of the current note is 
            overridden to extend to the previous note's pos_hit_range boundary.

            TODO: implement
            """
            self.notelock = True

            """
            Overrides the miss and hit windows to correspond to spacing between notes. If True then all 
            the ranges are are overridden to be split up in 1/4th sections relative to the distance between 
            current and next notes

            TODO: implement
            """
            self.dynamic_window = False

            """
            Enables missing in blank space. If True, the Nothing window behaves like the miss window, but the 
            iterator does not go to the next note. Also allows missing when clicked in empty space.
            """
            self.blank_miss = False

            """
            If True, sliders can be released and then pressed again so long as player holds key down when an aimpoint
            is passed. If false, then upon release all aimpoints that follow are dropped and note's release timing is processed
            """
            self.recoverable_release = True

            """
            If True, release miss range is processed. Otherwise, it's impossible to miss a release
            """
            self.release_miss = True

            """
            If True, missing a slider aimpoint misses the rest of the slider
            """
            self.miss_slider = True

            """
            If True, press miss range is processed. Otherwise, it's impossible to miss a press
            """
            self.press_miss = True

            """
            If True, the cursor can wander off slider and come back so long as the cursor is there when it's time for the aimpoint
            to be processed. If False, then slider release timing is triggered as soon as the cursor is out of range 
            """
            self.recoverable_missaim = True

            """
            There are cases for which parts of the hitwindow of multiple notes may overlap. If True, all 
            overlapped miss hitwindow sections are all processed simultaniously for one key event. If 
            False, each overlapped miss part is processed for each individual key event.

            # TODO: implement
            """
            self.overlap_miss_handling = False

            """
            There are cases for which parts of the hitwindow of multiple notes may overlap. If True, all 
            overlapped non miss hitwindow parts are all processed simultaniously for one key event. If 
            False, each overlapped hit part is processed for each individual key event.

            # TODO: implement
            """
            self.overlap_hit_handling = False

            """
            If true then presses while holding another key will not register
            """
            self.press_block = False

            """
            If true then releases while holding another key will not register
            """
            self.release_block = False

            """
            If True: Press window is applied to key presses
            """
            self.require_tap_press = True

            """
            If True: Release window is applied to key releases
            """
            self.require_tap_release = True

            """
            If True: Hold window is applied to key holds
            """
            self.require_tap_hold = True

            """
            If True: The player is required to aim presses
            """
            self.require_aim_press = True

            """
            If True: The player is required to aim releases
            """
            self.require_aim_release = True

            """
            If True: The player is required to aim holds
            """
            self.require_aim_hold = True


            '''
            Settings combinations:
                Relax:
                    - require_press    = False
                    - require_releases = False
                    - require_holds    = False
                    - blank_miss       = False

                Autopilot:
                    - require_aim_presses  = False
                    - require_aim_releases = False
                    - require_aim_holds    = False
            '''

            self.__is_frozen = True


    @staticmethod
    def __adv(map_data, map_time, adv):
        if adv == StdScoreData.__ADV_NOP:
            return map_time

        if adv == StdScoreData.__ADV_AIMP:
            aimpoint = StdMapData.get_scorepoint_after(map_data, map_time)
            if type(aimpoint) == type(None): 
                return StdMapData.all_times(map_data)[-1] + 1
            
            return aimpoint['time']

        if adv == StdScoreData.__ADV_NOTE:
            note = StdMapData.get_note_after(map_data, map_time)
            if type(note) == type(None):
                return StdMapData.all_times(map_data)[-1] + 1
            return note['time'][0]

        return map_time


    @staticmethod
    def __process_free(settings, score_data, aimpoints, replay_time, replay_xpos, replay_ypos, last_tap_pos):
        # Note start and end params
        aimpoint_time = aimpoints[0][0]  # time
        aimpoint_xcor = aimpoints[0][1]  # x
        aimpoint_ycor = aimpoints[0][2]  # y
        aimpoint_type = aimpoints[0][3]  # type

        # Free only looks at timings that have passed
        if replay_time < aimpoint_time:
            return StdScoreData.__ADV_NOP

        time_offset = replay_time - aimpoint_time
        posx_offset = replay_xpos - aimpoint_xcor
        posy_offset = replay_ypos - aimpoint_ycor
        pos_offset  = (posx_offset**2 + posy_offset**2)**0.5

        def proc_press():
            is_late_timing = time_offset > settings.pos_hit_miss_range
            is_miss_aiming = pos_offset > settings.hitobject_radius

            if settings.require_aim_press and settings.require_tap_press:
                if is_miss_aiming:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, last_tap_pos[0], last_tap_pos[1], aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.PRESS ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP
                else:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, last_tap_pos[0], last_tap_pos[1], aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.PRESS ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP

            if settings.require_aim_press and not settings.require_tap_press:
                if is_miss_aiming:
                    if is_late_timing:
                        print(f'free miss | replay_time: {replay_time}    aimpoint_time: {aimpoint_time}   time_offset: {time_offset}')
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, replay_xpos, replay_ypos, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.PRESS ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP
                else:
                    if time_offset >= 0:
                        print(f'free hitp | replay_time: {replay_time}    aimpoint_time: {aimpoint_time}   time_offset: {time_offset}')
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, replay_xpos, replay_ypos, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_HITP, StdReplayData.PRESS ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP

            if not settings.require_aim_press and settings.require_tap_press:
                if is_late_timing:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, last_tap_pos[0], last_tap_pos[1], aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.PRESS ])
                    return StdScoreData.__ADV_NOTE
                else:
                    return StdScoreData.__ADV_NOP

            if not settings.require_aim_press and not settings.require_tap_press:
                if time_offset >= 0:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, aimpoint_xcor, aimpoint_ycor, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_HITP, StdReplayData.PRESS ])
                    return StdScoreData.__ADV_NOTE
                else:
                    return StdScoreData.__ADV_NOP

            return StdScoreData.__ADV_NOP
            
        def proc_release():
            rec_x, rec_y = (replay_xpos, replay_ypos) if settings.require_aim_release else ( \
                (aimpoint_xcor, aimpoint_ycor)
            )

            is_late_timing = time_offset > settings.pos_rel_miss_range
            is_miss_aiming = pos_offset > settings.release_radius

            if settings.require_aim_release and settings.require_tap_release:
                if is_miss_aiming:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.RELEASE ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP
                else:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.RELEASE ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP

            if settings.require_aim_release and not settings.require_tap_release:
                if is_miss_aiming:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.RELEASE ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP
                else:
                    if time_offset >= 0:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_HITR, StdReplayData.RELEASE ])
                        return StdScoreData.__ADV_NOTE
                    else:
                        return StdScoreData.__ADV_NOP

            if not settings.require_aim_release and settings.require_tap_release:
                if is_late_timing:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.RELEASE ])
                    return StdScoreData.__ADV_NOTE
                else:
                    return StdScoreData.__ADV_NOP

            if not settings.require_aim_release and not settings.require_tap_release:
                if time_offset >= 0:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_HITR, StdReplayData.RELEASE ])
                    return StdScoreData.__ADV_NOTE
                else:
                    return StdScoreData.__ADV_NOP

        def proc_hold():
            if settings.recoverable_release:
                is_late_timing = time_offset > settings.pos_hld_range
            else:
                is_late_timing = time_offset > 0

            is_miss_aiming = pos_offset > settings.release_radius

            rec_x, rec_y = (replay_xpos, replay_ypos) if settings.require_aim_hold else ( \
                (aimpoint_xcor, aimpoint_ycor)
            )

            if settings.require_aim_hold and settings.require_tap_hold:
                if is_miss_aiming:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.HOLD ])
                        return StdScoreData.__ADV_NOTE if settings.miss_slider else StdScoreData.__ADV_AIMP
                    else:
                        return StdScoreData.__ADV_NOP
                else:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.HOLD ])
                        return StdScoreData.__ADV_NOTE if settings.miss_slider else StdScoreData.__ADV_AIMP
                    else:
                        return StdScoreData.__ADV_NOP

            if settings.require_aim_hold and not settings.require_tap_hold:
                if is_miss_aiming:
                    if is_late_timing:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.HOLD ])
                        return StdScoreData.__ADV_NOTE if settings.miss_slider else StdScoreData.__ADV_AIMP
                    else:
                        return StdScoreData.__ADV_NOP
                else:
                    if time_offset >= 0:
                        score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_AIMH, StdReplayData.HOLD ])
                        return StdScoreData.__ADV_AIMP
                    else:
                        return StdScoreData.__ADV_NOP

            if not settings.require_aim_hold and settings.require_tap_hold:
                if is_late_timing:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.HOLD ])
                    return StdScoreData.__ADV_NOTE if settings.miss_slider else StdScoreData.__ADV_AIMP
                else:
                    return StdScoreData.__ADV_NOP

            if not settings.require_aim_hold and not settings.require_tap_hold:
                if time_offset >= 0:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_AIMH, StdReplayData.HOLD ])
                    return StdScoreData.__ADV_AIMP
                else:
                    return StdScoreData.__ADV_NOP

        if aimpoint_type == StdMapData.TYPE_PRESS:   return proc_press()
        if aimpoint_type == StdMapData.TYPE_RELEASE: return proc_release()
        if aimpoint_type == StdMapData.TYPE_HOLD:    return proc_hold()

        # Unknown aimpoint type; skip
        return StdScoreData.__ADV_NOTE


    @staticmethod
    def __process_press(settings, score_data, aimpoints, replay_time, replay_xpos, replay_ypos, last_tap_pos):
        # Note start and end params
        aimpoint_time = aimpoints[0][0]  # time
        aimpoint_xcor = aimpoints[0][1]  # x
        aimpoint_ycor = aimpoints[0][2]  # y
        aimpoint_type = aimpoints[0][3]  # type
        aimpoint_obj  = aimpoints[0][4]  # object

        # If it's not a press scorepoint, ignore
        if aimpoint_type != StdMapData.TYPE_PRESS:
            return StdScoreData.__ADV_NOP

        time_offset = replay_time - aimpoint_time
        posx_offset = replay_xpos - aimpoint_xcor
        posy_offset = replay_ypos - aimpoint_ycor
        pos_offset  = (posx_offset**2 + posy_offset**2)**0.5

        if settings.require_aim_press:
            is_miss_aim = pos_offset > settings.hitobject_radius
            rec_x, rec_y = replay_xpos, replay_ypos
        else:
            is_miss_aim = False
            rec_x, rec_y = aimpoint_xcor, aimpoint_ycor

        if settings.require_tap_press:
            is_in_neg_nothing_range =                                time_offset <= -settings.neg_hit_miss_range
            is_in_neg_miss_range    = -settings.neg_hit_miss_range < time_offset <= -settings.neg_hit_range
            is_in_hit_range         = -settings.neg_hit_range      < time_offset <=  settings.pos_hit_range
            is_in_pos_miss_range    =  settings.pos_hit_range      < time_offset <=  settings.pos_hit_miss_range
            is_in_pos_nothing_range =  settings.pos_hit_miss_range < time_offset
        else:
            is_in_neg_nothing_range = settings.blank_miss and (time_offset <= -settings.neg_hit_miss_range)
            is_in_neg_miss_range    = False
            is_in_hit_range         = time_offset >= 0
            is_in_pos_miss_range    = False
            is_in_pos_nothing_range = False

        if is_miss_aim:
            # If blank miss is on, then record misses due to pressing in empty space
            if settings.blank_miss:
                score_data[len(score_data)] = np.asarray([ replay_time, np.nan, replay_xpos, replay_ypos, np.nan, np.nan, StdScoreData.TYPE_EMPTY, StdReplayData.PRESS ])
            
            # Record the position in black area the player tapped at
            last_tap_pos[0] = replay_xpos
            last_tap_pos[1] = replay_ypos

            # No note was hit, so don't go to next
            return StdScoreData.__ADV_NOP

        if is_in_neg_nothing_range:
            if settings.blank_miss:
                score_data[len(score_data)] = np.asarray([ replay_time, np.nan, rec_x, rec_y, np.nan, np.nan, StdScoreData.TYPE_EMPTY, StdReplayData.PRESS ])
            return StdScoreData.__ADV_NOP

        if is_in_neg_miss_range:
            if settings.press_miss:
                score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.PRESS ])
                return StdScoreData.__ADV_NOTE
            else:
                return StdScoreData.__ADV_NOP

        if is_in_hit_range:            
            score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_HITP, StdReplayData.PRESS ])
            if aimpoint_obj == StdMapData.TYPE_SLIDER:
                return StdScoreData.__ADV_AIMP
            else:
                return StdScoreData.__ADV_NOTE

        if is_in_pos_miss_range:
            if settings.press_miss:
                score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.PRESS ])
                return StdScoreData.__ADV_NOTE
            else:
                return StdScoreData.__ADV_NOP

        if is_in_pos_nothing_range:
            # Way late taps, interpret as never pressed.
            # Ignore these and let FREE processing handle it.
            return StdScoreData.__ADV_NOP

        return StdScoreData.__ADV_NOP


    @staticmethod
    def __process_hold(settings, score_data, aimpoints, replay_time, replay_xpos, replay_ypos, last_tap_pos):
        # Note start and end params
        aimpoint_time = aimpoints[0][0]  # time
        aimpoint_xcor = aimpoints[0][1]  # x
        aimpoint_ycor = aimpoints[0][2]  # y
        aimpoint_type = aimpoints[0][3]  # type

        # If the scorepoint is not a HOLD, ignore
        if aimpoint_type != StdMapData.TYPE_HOLD:
            return StdScoreData.__ADV_NOP

        time_offset = replay_time - aimpoint_time
        posx_offset = replay_xpos - aimpoint_xcor
        posy_offset = replay_ypos - aimpoint_ycor
        pos_offset  = (posx_offset**2 + posy_offset**2)**0.5

        if settings.require_aim_hold:
            is_miss_aim = pos_offset > settings.follow_radius
            rec_x, rec_y = replay_xpos, replay_ypos
        else:
            is_miss_aim = False
            rec_x, rec_y = aimpoint_xcor, aimpoint_ycor

        if settings.require_tap_hold:
            is_in_neg_nothing_range =                           time_offset <= -settings.neg_hld_range
            is_in_hold_range        = -settings.neg_hld_range < time_offset <=  settings.pos_hld_range
            is_in_pos_nothing_range =  settings.pos_hld_range < time_offset
        else:
            is_in_neg_nothing_range = False
            is_in_hold_range        = time_offset >= 0
            is_in_pos_nothing_range = False

        if is_miss_aim:
            if settings.recoverable_missaim:
                is_late = settings.pos_hld_range < time_offset
                if is_late:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.HOLD ])
                    return StdScoreData.__ADV_NOTE if settings.miss_slider else StdScoreData.__ADV_AIMP
                else:
                    return StdScoreData.__ADV_NOP
            else:
                score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.HOLD ])
                return StdScoreData.__ADV_NOTE if settings.miss_slider else StdScoreData.__ADV_AIMP

        if is_in_neg_nothing_range:
            return StdScoreData.__ADV_NOP
        
        if is_in_hold_range:
            score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_AIMH, StdReplayData.HOLD ])
            return StdScoreData.__ADV_AIMP

        if is_in_pos_nothing_range:
            return StdScoreData.__ADV_NOP

        return StdScoreData.__ADV_NOP


    @staticmethod
    def __process_release(settings, score_data, aimpoints, replay_time, replay_xpos, replay_ypos, last_tap_pos):
        # Note start and end params
        aimpoint_time = aimpoints[0][0]  # time
        aimpoint_xcor = aimpoints[0][1]  # x
        aimpoint_ycor = aimpoints[0][2]  # y
        aimpoint_type = aimpoints[0][3]  # type

        # If the scorepoint expects a press, then ignore
        if aimpoint_type == StdMapData.TYPE_PRESS:
            return StdScoreData.__ADV_NOP

        time_offset = replay_time - aimpoint_time
        posx_offset = replay_xpos - aimpoint_xcor
        posy_offset = replay_ypos - aimpoint_ycor
        pos_offset  = (posx_offset**2 + posy_offset**2)**0.5

        if settings.require_aim_release:
            is_miss_aim = pos_offset > settings.release_radius
            rec_x, rec_y = replay_xpos, replay_ypos
        else:
            is_miss_aim = False
            rec_x, rec_y = aimpoint_xcor, aimpoint_ycor

        if settings.require_tap_release:
            is_in_neg_nothing_range =                                time_offset <= -settings.neg_rel_miss_range
            is_in_neg_miss_range    = -settings.neg_rel_miss_range < time_offset <= -settings.neg_rel_range
            is_in_rel_range         = -settings.neg_rel_range      < time_offset <=  settings.pos_rel_range
            is_in_pos_miss_range    =  settings.pos_rel_range      < time_offset <=  settings.pos_rel_miss_range
            is_in_pos_nothing_range =  settings.pos_rel_miss_range < time_offset
        else:
            is_in_neg_nothing_range = False
            is_in_neg_miss_range    = False
            is_in_rel_range         = time_offset >= 0
            is_in_pos_miss_range    = False
            is_in_pos_nothing_range = False

        if aimpoint_type == StdMapData.TYPE_HOLD:
            if settings.require_tap_hold:
                if settings.recoverable_release:
                    return StdScoreData.__ADV_NOP
                else:
                    score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.HOLD ])
                    return StdScoreData.__ADV_NOTE if settings.miss_slider else StdScoreData.__ADV_AIMP
            
            return StdScoreData.__ADV_NOP

        # If release range is enabled, releases must be within the release radius to count
        if is_miss_aim:
            score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.RELEASE ])
            return StdScoreData.__ADV_NOTE

        # Stuff after this requires tap processing

        if is_in_neg_nothing_range:
            return StdScoreData.__ADV_NOP

        if is_in_neg_miss_range:
            if settings.release_miss:
                score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.RELEASE ])
                return StdScoreData.__ADV_NOTE
            else:
                return StdScoreData.__ADV_NOP

        if is_in_rel_range:
            score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_HITR, StdReplayData.RELEASE ])
            return StdScoreData.__ADV_NOTE

        if is_in_pos_miss_range:
            if settings.release_miss:
                score_data[len(score_data)] = np.asarray([ replay_time, aimpoint_time, rec_x, rec_y, aimpoint_xcor, aimpoint_ycor, StdScoreData.TYPE_MISS, StdReplayData.RELEASE ])
                return StdScoreData.__ADV_NOTE
            else:
                return StdScoreData.__ADV_NOP

        if is_in_pos_nothing_range:
            # Way late release, interpret as never released.
            # Ignore these and let FREE processing handle it.
            return StdScoreData.__ADV_NOP

        return StdScoreData.__ADV_NOP


    @staticmethod
    def get_score_data(replay_data, map_data, settings=Settings()):
        # Score data that will be filled in and returned
        score_data = {}

        # replay pointer
        replay_idx = 0

        # Filter out single note release points
        filter_single_release = np.ones(map_data.shape[0], dtype=bool)
        filter_single_release[1:] = ~( \
            (map_data['type'].values[:-1] == StdMapData.TYPE_PRESS) &             \
            (map_data['type'].values[1:] == StdMapData.TYPE_RELEASE) &            \
            ((map_data['time'].values[1:] - map_data['time'].values[:-1]) == 1) & \
            ((map_data['x'].values[1:] - map_data['x'].values[:-1]) == 0) &       \
            ((map_data['y'].values[1:] - map_data['y'].values[:-1]) == 0)
        )

        map_data = map_data[filter_single_release]

        # map_time is the time at which hitobject processing logic is at
        map_times = map_data.values[:, StdMapData.IDX_TIME]
        map_time = map_times[0]
        map_time_max = map_times[-1]

        # Number of things to loop through
        replay_data = StdReplayData.get_reduced_replay_data(replay_data, press_block=settings.press_block, release_block=settings.release_block).values
        replay_idx_max = replay_data.shape[0]

        # Keeps track of the last position at which the player tapped a key
        # Resets for every new note
        last_tap_pos = [ np.nan, np.nan ]

        earliest_window_range = max(
            settings.neg_hit_miss_range,
            settings.neg_rel_miss_range, 
            settings.neg_hld_range
        )

        latest_window_range = max(
            settings.pos_hit_miss_range, 
            settings.pos_rel_miss_range, 
            settings.pos_hld_range
        )

        # Go through replay events
        while True:
            # Condition check whether all player actions in the column have been processed
            if replay_idx >= replay_idx_max:
                break

            # Data for this event frame
            replay_time = replay_data[replay_idx][0]  # time
            replay_xpos = replay_data[replay_idx][1]  # x
            replay_ypos = replay_data[replay_idx][2]  # y
            replay_key  = replay_data[replay_idx][3]  # keys

            # Got all info at current index, now advance it
            replay_idx += 1

            # Go through map
            while True:
                if map_time > map_time_max:
                    # Reached end of map
                    break

                if replay_time < map_time - earliest_window_range:
                    # Replay time needs to catch up to the current map time
                    # Unil within hit window processing range or notes are visible
                    break

                # In theory, should never be 0
                current_aimpoint_select = (map_time == map_times)
                current_aimpoint = map_data.values[current_aimpoint_select]

                # Check for any skipped notes (if replay has event gaps)
                adv = StdScoreData.__process_free(settings, score_data, current_aimpoint, replay_time, replay_xpos, replay_ypos, last_tap_pos)
                if adv == StdScoreData.__ADV_NOP:
                    break

                # Advancing to next note, reset last_tap_pos
                last_tap_pos = [ np.nan, np.nan ]

                # Process advancement
                map_time = StdScoreData.__adv(map_data, map_time, adv)

            # replay_time is considered to be the time experienced by the player
            # At this time the player will be able to `ar_ms` ahead of current time
            start_time = replay_time
            end_time   = replay_time + settings.ar_ms

            # Get visible notes at current time
            visible_notes_select = (start_time <= map_times) & (map_times <= end_time)
            if np.count_nonzero(visible_notes_select) == 0:
                # Nothing to process
                continue

            visible_notes = map_data.values[visible_notes_select]

            # Interpolate replay data
            #aimpoint_time = visible_notes[0, StdMapData.IDX_TIME]
            #replay_time, replay_xpos, replay_ypos = \
            #    StdScoreData.__interpolate_replay_data(aimpoint_time, replay_data, replay_idx - 1)

            # Process player actions
            if replay_key == StdReplayData.FREE:    adv = StdScoreData.__process_free(settings, score_data, visible_notes, replay_time, replay_xpos, replay_ypos, last_tap_pos)
            if replay_key == StdReplayData.PRESS:   adv = StdScoreData.__process_press(settings, score_data, visible_notes, replay_time, replay_xpos, replay_ypos, last_tap_pos)
            if replay_key == StdReplayData.HOLD:    adv = StdScoreData.__process_hold(settings, score_data, visible_notes, replay_time, replay_xpos, replay_ypos, last_tap_pos)
            if replay_key == StdReplayData.RELEASE: adv = StdScoreData.__process_release(settings, score_data, visible_notes, replay_time, replay_xpos, replay_ypos, last_tap_pos)

            # If advancing to next note, reset last_tap_pos
            if adv != StdScoreData.__ADV_NOP:
                last_tap_pos = [ np.nan, np.nan ]

            # Process advancement
            map_time = StdScoreData.__adv(map_data, map_time, adv)

        # Convert recorded timings and states into a pandas data
        score_data = list(score_data.values())
        return pd.DataFrame(score_data, columns=['replay_t', 'map_t', 'replay_x', 'replay_y', 'map_x', 'map_y', 'type', 'action' ])


    @staticmethod
    def __interpolate_replay_data(aimpoint_time, replay_data, replay_idx):
        replay_time_curr = replay_data[replay_idx][0]
        replay_xpos_curr = replay_data[replay_idx][1]
        replay_ypos_curr = replay_data[replay_idx][2]

        if replay_idx >= replay_data.shape[0] - 1:
            return replay_time_curr, replay_xpos_curr, replay_ypos_curr
        
        replay_time_next = replay_data[replay_idx + 1][0]
        replay_xpos_next = replay_data[replay_idx + 1][1]
        replay_ypos_next = replay_data[replay_idx + 1][2]

        print((replay_time_curr < aimpoint_time < replay_time_next), (replay_time_curr < aimpoint_time), (aimpoint_time < replay_time_next), replay_time_curr, aimpoint_time, replay_time_next)
        if not (replay_time_curr < aimpoint_time < replay_time_next):
            return replay_time_curr, replay_xpos_curr, replay_ypos_curr

        precent = (replay_time_curr - aimpoint_time) / (replay_time_next - replay_time_curr)
        
        replay_time = aimpoint_time
        replay_xpos = precent*(replay_xpos_next - replay_xpos_curr)
        replay_ypos = precent*(replay_ypos_next - replay_ypos_curr)

        print(replay_time)
        return replay_time, replay_xpos, replay_ypos
            


    '''
    @staticmethod
    def get_velocity_jump_frames(replay_data, map_data):
        """
        Extracts frames of replay data associated with jumps 
        A frame spans from halfway before the last note to halfway after current note

        Parameters
        ----------
        replay_data : numpy.array
            Replay data

        map_data : numpy.array
            Map data

        Returns
        -------
        numpy.array
        """
        vel_times, vel_data = StdReplayMetrics.cursor_velocity(replay_data)
        map_times = StdMapData.start_end_times(map_data)
        frames = []

        threshold_vel = vel_data[vel_data != np.inf][int(len(vel_data)*0.8)]
        #vel_data = np.convolve(vel_data, np.ones(3, dtype=float)/3, 'valid')

        for idx in range(1, len(map_times)):
            # Frame start and end
            time_start, time_end = map_times[idx - 1][-1], map_times[idx][0]

            # If it's a slider, expand the frame back a bit
            # Sliders have some leniency allowing the player to leave it before it's fully finished
            # There is a time when it's optimal to leave the slider based on OD (values are fudged for now,
            # but do approach circle OD calc later). 
            if map_times[idx - 1][0] != map_times[idx - 1][-1]:
                time_start -= min((map_times[idx - 1][-1] - map_times[idx - 1][0])*0.5, 50)

            # Get replay data mask spanning that time period
            frame_mask = np.where(np.logical_and(time_start <= vel_times, vel_times <= time_end))[0]

            vel_frame = vel_data[frame_mask]
            if np.all(vel_frame < threshold_vel):
                continue

            time_frame = vel_times[frame_mask]
            #time_frame = time_frame - time_frame[0]

            frames.append([ time_frame, vel_frame ])

        return np.asarray(frames)
    '''


    @staticmethod
    def tap_press_offsets(score_data):
        hit_presses = score_data[score_data['type'] == StdScoreData.TYPE_HITP]
        return hit_presses['replay_t'] - hit_presses['map_t']


    @staticmethod
    def tap_release_offsets(score_data):
        hit_releases = score_data[score_data['type'] == StdScoreData.TYPE_HITR]
        return hit_releases['replay_t'] - hit_releases['map_t']


    @staticmethod
    def aim_x_offsets(score_data):
        hit_presses = score_data[score_data['type'] == StdScoreData.TYPE_HITP]
        return hit_presses['replay_x'] - hit_presses['map_x']


    @staticmethod
    def aim_y_offsets(score_data):
        hit_presses = score_data[score_data['type'] == StdScoreData.TYPE_HITP]
        return hit_presses['replay_y'] - hit_presses['map_y']


    @staticmethod
    def aim_offsets(score_data):
        hit_presses = score_data[score_data['type'] != StdScoreData.TYPE_HITR]
        offset_x = hit_presses['replay_x'] - hit_presses['map_x']
        offset_y = hit_presses['replay_y'] - hit_presses['map_y']
        return (offset_x**2 + offset_y**2)**0.5


    @staticmethod
    def press_interval_mean(score_data):
        # TODO need to put in release offset into score_data
        # TODO need to go through hitobjects and filter out hold notes
        #  
        pass


    @staticmethod
    def tap_offset_mean(score_data):
        """
        Average of tap offsets

        Parameters
        ----------
        score_data : numpy.array
            Score data

        Returns
        -------
        float
        """
        return np.mean(StdScoreData.tap_press_offsets(score_data))


    @staticmethod
    def tap_offset_var(score_data):
        """
        Variance of tap offsets

        Parameters
        ----------
        score_data : numpy.array
            Score data

        Returns
        -------
        float
        """
        return np.var(StdScoreData.tap_press_offsets(score_data))


    @staticmethod
    def tap_offset_stdev(score_data):
        """
        Standard deviation of tap offsets

        Parameters
        ----------
        score_data : numpy.array
            Score data

        Returns
        -------
        float
        """
        return np.std(StdScoreData.tap_press_offsets(score_data))


    @staticmethod
    def cursor_pos_offset_mean(score_data):
        """
        Average of cursor position offsets at moments the player tapped notes

        Parameters
        ----------
        score_data : numpy.array
            Score data

        Returns
        -------
        float
        """
        return np.mean(StdScoreData.aim_offsets(score_data))


    @staticmethod
    def cursor_pos_offset_var(score_data):
        """
        Variance of cursor position offsets at moments the player tapped notes

        Parameters
        ----------
        score_data : numpy.array
            Score data

        Returns
        -------
        float
        """
        return np.var(StdScoreData.aim_offsets(score_data))


    @staticmethod
    def cursor_pos_offset_stdev(score_data):
        """
        Standard deviation of cursor position offsets at moments the player tapped notes

        Parameters
        ----------
        score_data : numpy.array
            Score data

        Returns
        -------
        float
        """
        return np.std(StdScoreData.aim_offsets(score_data))


    @staticmethod
    def odds_some_tap_within(score_data, offset):
        """
        Creates a gaussian distribution model using avg and var of tap offsets and calculates the odds that some hit
        is within the specified offset

        Parameters
        ----------
        score_data : numpy.array
            Score data

        offset : float
            Tap offset (ms) to determine odds for

        Returns
        -------
        float
            Probability one random value ``[X]`` is between ``-offset <= X <= offset``.
            In simpler terms, look at all the hits for scores; What are the odds 
            of you picking a random hit that is between ``-offset`` and ``offset``?
        """
        mean  = StdScoreData.tap_offset_mean(score_data)
        stdev = StdScoreData.tap_offset_stdev(score_data)

        # scipy cdf can't handle 0 stdev (div by 0)
        if stdev == 0:
            return 1.0 if -offset <= mean <= offset else 0.0

        prob_greater_than_neg = scipy.stats.norm.cdf(-offset, loc=mean, scale=stdev)
        prob_less_than_pos = scipy.stats.norm.cdf(offset, loc=mean, scale=stdev)

        return prob_less_than_pos - prob_greater_than_neg


    @staticmethod
    def odds_some_cursor_within(score_data, offset):
        """
        Creates a 2D gaussian distribution model using avg and var of cursor 2D position offsets and uses it to calculates the odds 
        that some cursor position is within the specified distance from the center of any hitobject

        Parameters
        ----------
        score_data : numpy.array
            Score data

        offset : float
            Tap offset (ms) to determine odds for

        Returns
        -------
        float
            Probability one random value ``[X, Y]`` is between ``(-offset, -offset) <= (X, Y) <= (offset, offset)``.
            In simpler terms, look at all the cursor positions for score; What are the odds of you picking a random hit that has 
            a cursor position between an area of ``(-offset, -offset)`` and ``(offset, offset)``?
        """ 
        aim_x_offsets = StdScoreData.aim_x_offsets(score_data)
        aim_y_offsets = StdScoreData.aim_y_offsets(score_data)

        mean_aim_x = np.mean(aim_x_offsets)
        mean_aim_y = np.mean(aim_y_offsets)

        mean = np.asarray([ mean_aim_x, mean_aim_y ])
        covariance = np.cov(np.asarray([ aim_x_offsets, aim_y_offsets ]))
        
        distribution = scipy.stats.multivariate_normal(mean, covariance, allow_singular=True)

        prob_less_than_neg = distribution.cdf(np.asarray([-offset, -offset]))
        prob_less_than_pos = distribution.cdf(np.asarray([offset, offset]))

        return prob_less_than_pos - prob_less_than_neg


    @staticmethod
    def odds_all_tap_within(score_data, offset):
        """
        Creates a gaussian distribution model using avg and var of tap offsets and calculates the odds that all hits
        are within the specified offset

        Parameters
        ----------
        score_data : numpy.array
            Score data

        offset : float
            Tap offset (ms) to determine odds for

        Returns
        ------- 
        float
            Probability all random values ``[X]`` are between ``-offset <= X <= offset``.
            In simpler terms, look at all the hits for scores; What are the odds all of them are between -offset and offset?
        """
        # TODO: handle misses

        hit_presses = score_data[score_data['type'] == StdScoreData.TYPE_HITP]
        return StdScoreData.odds_some_tap_within(score_data, offset)**len(hit_presses)


    @staticmethod
    def odds_all_cursor_within(score_data, offset):    
        """
        Creates a 2D gaussian distribution model using avg and var of cursor 2D position offsets and uses it to calculates the odds 
        that all cursor positions are within the specified distance from the center of all hitobject

        Parameters
        ----------
        score_data : numpy.array
            Score data

        offset : float
            Tap offset (ms) to determine odds for

        Returns
        -------
        float
            Probability all random values ``{[X, Y], ...}`` are between ``(-offset, -offset) <= (X, Y) <= (offset, offset)``
            In simpler terms, look at all the cursor positions for score; What are the odds all of them are between an area 
            of ``(-offset, -offset)`` and ``(offset, offset)``?
        """
        # TODO: handle misses

        hit_presses = score_data[score_data['type'] == StdScoreData.TYPE_HITP]
        return StdScoreData.odds_some_cursor_within(score_data, offset)**len(hit_presses)


    @staticmethod
    def odds_all_conditions_within(score_data, tap_offset, cursor_offset):
        """
        Creates gaussian distribution models using tap offsets and cursor offsets for hits. That is used to calculate the odds
        of the player consistently tapping and aiming within those boundaries for the entire play. Be weary of survivorship bias.

        Parameters
        ----------
        score_data : numpy.array
            Score data

        tap_offset : float
            Tap offset (ms) to determine odds for

        cursor_offset : float
            Cursor offset (ms) to determine odds for

        Returns
        -------
        float
        """
        odds_all_tap_within    = StdScoreData.odds_all_tap_within(score_data, tap_offset)
        odds_all_cursor_within = StdScoreData.odds_all_cursor_within(score_data, cursor_offset)

        return odds_all_tap_within*odds_all_cursor_within
