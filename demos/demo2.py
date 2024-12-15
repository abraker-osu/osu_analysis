"""
Replay analysis demo

NOTE: If changes were made, run refresh.bat to apply replay_reader changes to venv
"""

from replay_reader import ReplayIO
from osu_analysis import StdReplayData

if __name__ == '__main__':
    replay = ReplayIO.open_replay('test/data/replays/osu/LeaF - I (Maddy) [Terror] replay_0.osr')
    replay_data = StdReplayData.get_replay_data(replay)

    print(replay_data)
