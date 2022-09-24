# osu_analysis

The osu_analysis package has *almost* everything you need for analyzing osu! beatmaps and replays. Features include
- Beatmap reading and writing
- Replay reading
- Analyzing beatmap data as a pandas data object
- Analyzing replay data as a pandas data object
- Score processing and analysis
- Support for osu and mania gamemodes (I'll add taiko and catch someday)

## Installing

```
pip install git+https://github.com/abraker-osu/osu_analysis.git#egg=osu_analysis
```

## Basic usage

### Replay loading
```py
from replay_reader import ReplayIO

if __name__ == '__main__':
    replay = ReplayIO.open_replay('LeaF - I (Maddy) [Terror] replay_0.osr')
    print(replay.get_name())
```
Output:
```
> py run.py
firebat9  - 21552280 (x1080, 99.68%) | 830/4/0/0
```

### Beatmap loading
```py
from beatmap_reader import BeatmapIO

if __name__ == '__main__':
    beatmap = BeatmapIO.open_beatmap('Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic].osu')
    print(beatmap.metadata.name)
```
Output:
```
> py run.py
Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic]
```

### Replay analysis
```py
from replay_reader import ReplayIO
from osu_analysis import StdReplayData

if __name__ == '__main__':
    replay = ReplayIO.open_replay('LeaF - I (Maddy) [Terror] replay_0.osr')
    replay_data = StdReplayData.get_replay_data(replay)

    print(replay_data)
```
Output:
```
> py run.py
           time         x         y   m1   m2   k1   k2  smoke
0       -1217.0  120.5313  168.5313  1.0  0.0  0.0  0.0    0.0
1       -1213.0  119.1250  168.5313  2.0  0.0  0.0  0.0    0.0
2       -1196.0  117.2500  169.0000  2.0  0.0  0.0  0.0    0.0
3       -1179.0  116.3125  169.0000  2.0  0.0  0.0  0.0    0.0
4       -1179.0  116.3125  169.0000  2.0  0.0  0.0  1.0    0.0
...         ...       ...       ...  ...  ...  ...  ...    ...
11435  153455.0  246.6250  185.4063  0.0  0.0  0.0  0.0    0.0
11436  153469.0  243.8125  185.4063  0.0  0.0  0.0  0.0    0.0
11437  153488.0  240.0625  191.5000  0.0  0.0  0.0  0.0    0.0
11438  153505.0  237.2500  193.8438  0.0  0.0  0.0  0.0    0.0
11439  153506.0  237.2500  193.8438  0.0  0.0  0.0  0.0    0.0

[11440 rows x 8 columns]
```

### Map analysis
```py
from beatmap_reader import BeatmapIO
from osu_analysis import StdMapData

if __name__ == '__main__':
    beatmap = BeatmapIO.open_beatmap('Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic].osu')
    map_data = StdMapData.get_map_data(beatmap)

    print(map_data)
```
Output:
```
> py run.py
                        time           x           y  type  object
hitobject aimpoint
0         0            799.0  320.000000  328.000000   1.0     2.0
          1           1099.0  398.419295  314.615346   2.0     2.0
          2           1399.0  460.620298  266.281664   2.0     2.0
          3           1699.0  483.120574  190.759944   2.0     2.0
          4           1999.0  459.844094  115.487250   2.0     2.0
...                      ...         ...         ...   ...     ...
99        3         113299.0  312.011455  172.984543   2.0     2.0
          4         113563.0  323.774576  242.074198   3.0     2.0
100       0         114049.0  316.000000  372.000000   1.0     2.0
          1         114349.0  236.000000  372.000000   2.0     2.0
          2         114463.0  205.600000  372.000000   3.0     2.0

[348 rows x 5 columns]
```

### Score analysis
```py
from replay_reader import ReplayIO
from beatmap_reader import BeatmapIO
from osu_analysis import StdMapData, StdReplayData, StdScoreData


if __name__ == '__main__':
    replay = ReplayIO.open_replay('LeaF - I (Maddy) [Terror] replay_0.osr')
    replay_data = StdReplayData.get_replay_data(replay)

    beatmap = BeatmapIO.open_beatmap('Mutsuhiko Izumi - Red Goose (nold_1702) [ERT Basic].osu')
    map_data = StdMapData.get_map_data(beatmap)

    score_data = StdScoreData.get_score_data(replay_data, map_data)
    print(score_data)
```
Output:
```
> py run.py
     replay_t     map_t   replay_x  replay_y  map_x  map_y  type  action
0      1005.0     799.0  346.93750  265.5625  320.0  328.0   3.0     1.0
1      3405.0    3199.0  116.78130  109.9375  236.0  192.0   3.0     1.0
2      5805.0    5599.0  358.18750  108.0625  318.0   55.0   3.0     1.0
3      8205.0    7999.0  154.75000  194.7813  236.0  192.0   3.0     1.0
4     11805.0   11599.0   61.93751  223.8438  300.0  124.0   3.0     1.0
..        ...       ...        ...       ...    ...    ...   ...     ...
103  107805.0  107599.0  138.34380  147.4375   88.0  268.0   3.0     1.0
104  109605.0  109399.0  112.56250  263.2188  256.0  308.0   3.0     1.0
105  110205.0  109999.0  310.84380  112.2813  403.0  245.0   3.0     1.0
106  112605.0  112399.0   98.50002  214.4688  188.0  256.0   3.0     1.0
107  114255.0  114049.0  166.46880  326.5000  316.0  372.0   3.0     1.0

[108 rows x 8 columns]
```
