# Blocksworld (Sequential, Satisficing)

## Domain Description

Blocksworld is the canonical STRIPS benchmark.
A single-arm robot manipulates a set of uniquely-named blocks resting on a table.
Each block can be clear or covered by exactly one block, the arm can be empty or holding one block, and blocks can sit on the table or on top of another block.
Four actions — `pickup`, `putdown`, `stack`, `unstack` — rearrange the towers; the goal is expressed as a partial configuration of `on` / `on-table` facts.

Instances are generated for tower sizes ranging from 4 to 10 blocks, with roughly 20 randomised problems per size (plus one additional 8-block instance).

## Authors

Derived from the AI-Planning community generators (`https://github.com/AI-Planning/pddl-generators/tree/main/blocksworld`).

## Original File Names

| file             | original name   |
|------------------|-----------------|
| problem_001.pddl | pddl_4_1.pddl   |
| problem_002.pddl | pddl_4_2.pddl   |
| problem_003.pddl | pddl_4_3.pddl   |
| problem_004.pddl | pddl_4_4.pddl   |
| problem_005.pddl | pddl_4_5.pddl   |
| problem_006.pddl | pddl_4_6.pddl   |
| problem_007.pddl | pddl_4_7.pddl   |
| problem_008.pddl | pddl_4_8.pddl   |
| problem_009.pddl | pddl_4_9.pddl   |
| problem_010.pddl | pddl_4_10.pddl  |
| problem_011.pddl | pddl_4_11.pddl  |
| problem_012.pddl | pddl_4_12.pddl  |
| problem_013.pddl | pddl_4_13.pddl  |
| problem_014.pddl | pddl_4_14.pddl  |
| problem_015.pddl | pddl_4_15.pddl  |
| problem_016.pddl | pddl_4_16.pddl  |
| problem_017.pddl | pddl_4_17.pddl  |
| problem_018.pddl | pddl_4_18.pddl  |
| problem_019.pddl | pddl_4_19.pddl  |
| problem_020.pddl | pddl_4_20.pddl  |
| problem_021.pddl | pddl_5_1.pddl   |
| problem_022.pddl | pddl_5_2.pddl   |
| problem_023.pddl | pddl_5_3.pddl   |
| problem_024.pddl | pddl_5_4.pddl   |
| problem_025.pddl | pddl_5_5.pddl   |
| problem_026.pddl | pddl_5_6.pddl   |
| problem_027.pddl | pddl_5_7.pddl   |
| problem_028.pddl | pddl_5_8.pddl   |
| problem_029.pddl | pddl_5_9.pddl   |
| problem_030.pddl | pddl_5_10.pddl  |
| problem_031.pddl | pddl_5_11.pddl  |
| problem_032.pddl | pddl_5_12.pddl  |
| problem_033.pddl | pddl_5_13.pddl  |
| problem_034.pddl | pddl_5_14.pddl  |
| problem_035.pddl | pddl_5_15.pddl  |
| problem_036.pddl | pddl_5_16.pddl  |
| problem_037.pddl | pddl_5_17.pddl  |
| problem_038.pddl | pddl_5_18.pddl  |
| problem_039.pddl | pddl_5_19.pddl  |
| problem_040.pddl | pddl_5_20.pddl  |
| problem_041.pddl | pddl_6_1.pddl   |
| problem_042.pddl | pddl_6_2.pddl   |
| problem_043.pddl | pddl_6_3.pddl   |
| problem_044.pddl | pddl_6_4.pddl   |
| problem_045.pddl | pddl_6_5.pddl   |
| problem_046.pddl | pddl_6_6.pddl   |
| problem_047.pddl | pddl_6_7.pddl   |
| problem_048.pddl | pddl_6_8.pddl   |
| problem_049.pddl | pddl_6_9.pddl   |
| problem_050.pddl | pddl_6_10.pddl  |
| problem_051.pddl | pddl_6_11.pddl  |
| problem_052.pddl | pddl_6_12.pddl  |
| problem_053.pddl | pddl_6_13.pddl  |
| problem_054.pddl | pddl_6_14.pddl  |
| problem_055.pddl | pddl_6_15.pddl  |
| problem_056.pddl | pddl_6_16.pddl  |
| problem_057.pddl | pddl_6_17.pddl  |
| problem_058.pddl | pddl_6_18.pddl  |
| problem_059.pddl | pddl_6_19.pddl  |
| problem_060.pddl | pddl_6_20.pddl  |
| problem_061.pddl | pddl_7_1.pddl   |
| problem_062.pddl | pddl_7_2.pddl   |
| problem_063.pddl | pddl_7_3.pddl   |
| problem_064.pddl | pddl_7_4.pddl   |
| problem_065.pddl | pddl_7_5.pddl   |
| problem_066.pddl | pddl_7_6.pddl   |
| problem_067.pddl | pddl_7_7.pddl   |
| problem_068.pddl | pddl_7_8.pddl   |
| problem_069.pddl | pddl_7_9.pddl   |
| problem_070.pddl | pddl_7_10.pddl  |
| problem_071.pddl | pddl_7_11.pddl  |
| problem_072.pddl | pddl_7_12.pddl  |
| problem_073.pddl | pddl_7_13.pddl  |
| problem_074.pddl | pddl_7_14.pddl  |
| problem_075.pddl | pddl_7_15.pddl  |
| problem_076.pddl | pddl_7_16.pddl  |
| problem_077.pddl | pddl_7_17.pddl  |
| problem_078.pddl | pddl_7_18.pddl  |
| problem_079.pddl | pddl_7_19.pddl  |
| problem_080.pddl | pddl_7_20.pddl  |
| problem_081.pddl | pddl_8_1.pddl   |
| problem_082.pddl | pddl_8_2.pddl   |
| problem_083.pddl | pddl_8_3.pddl   |
| problem_084.pddl | pddl_8_4.pddl   |
| problem_085.pddl | pddl_8_5.pddl   |
| problem_086.pddl | pddl_8_6.pddl   |
| problem_087.pddl | pddl_8_7.pddl   |
| problem_088.pddl | pddl_8_8.pddl   |
| problem_089.pddl | pddl_8_9.pddl   |
| problem_090.pddl | pddl_8_10.pddl  |
| problem_091.pddl | pddl_8_11.pddl  |
| problem_092.pddl | pddl_8_12.pddl  |
| problem_093.pddl | pddl_8_13.pddl  |
| problem_094.pddl | pddl_8_14.pddl  |
| problem_095.pddl | pddl_8_15.pddl  |
| problem_096.pddl | pddl_8_16.pddl  |
| problem_097.pddl | pddl_8_17.pddl  |
| problem_098.pddl | pddl_8_18.pddl  |
| problem_099.pddl | pddl_8_19.pddl  |
| problem_100.pddl | pddl_8_20.pddl  |
| problem_101.pddl | pddl_8_109.pddl |
| problem_102.pddl | pddl_9_1.pddl   |
| problem_103.pddl | pddl_9_2.pddl   |
| problem_104.pddl | pddl_9_3.pddl   |
| problem_105.pddl | pddl_9_4.pddl   |
| problem_106.pddl | pddl_9_5.pddl   |
| problem_107.pddl | pddl_9_6.pddl   |
| problem_108.pddl | pddl_9_7.pddl   |
| problem_109.pddl | pddl_9_8.pddl   |
| problem_110.pddl | pddl_9_9.pddl   |
| problem_111.pddl | pddl_9_10.pddl  |
| problem_112.pddl | pddl_9_11.pddl  |
| problem_113.pddl | pddl_9_12.pddl  |
| problem_114.pddl | pddl_9_13.pddl  |
| problem_115.pddl | pddl_9_14.pddl  |
| problem_116.pddl | pddl_9_15.pddl  |
| problem_117.pddl | pddl_9_16.pddl  |
| problem_118.pddl | pddl_9_17.pddl  |
| problem_119.pddl | pddl_9_18.pddl  |
| problem_120.pddl | pddl_9_19.pddl  |
| problem_121.pddl | pddl_9_20.pddl  |
| problem_122.pddl | pddl_10_1.pddl  |
| problem_123.pddl | pddl_10_2.pddl  |
| problem_124.pddl | pddl_10_3.pddl  |
| problem_125.pddl | pddl_10_4.pddl  |
| problem_126.pddl | pddl_10_5.pddl  |
| problem_127.pddl | pddl_10_6.pddl  |
| problem_128.pddl | pddl_10_7.pddl  |
| problem_129.pddl | pddl_10_8.pddl  |
| problem_130.pddl | pddl_10_9.pddl  |
| problem_131.pddl | pddl_10_10.pddl |
| problem_132.pddl | pddl_10_11.pddl |
| problem_133.pddl | pddl_10_12.pddl |
| problem_134.pddl | pddl_10_13.pddl |
| problem_135.pddl | pddl_10_14.pddl |
| problem_136.pddl | pddl_10_15.pddl |
| problem_137.pddl | pddl_10_16.pddl |
| problem_138.pddl | pddl_10_17.pddl |
| problem_139.pddl | pddl_10_18.pddl |
| problem_140.pddl | pddl_10_19.pddl |
| problem_141.pddl | pddl_10_20.pddl |
