"""
Replay loading demo
"""
from replay_reader import ReplayIO

if __name__ == '__main__':
    replay = ReplayIO.open_replay('test/data/replays/osu/LeaF - I (Maddy) [Terror] replay_0.osr')
    print(replay.get_name())
