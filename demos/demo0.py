"""
Replay loading demo

NOTE: If changes were made, run refresh.bat to apply replay_reader changes to venv
"""
from replay_reader import ReplayIO

if __name__ == '__main__':
    replay = ReplayIO.open_replay('tests/data/replays/osu/LeaF - I (Maddy) [Terror] replay_0.osr')
    print(replay.get_name())
