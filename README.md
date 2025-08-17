# cluedo_ai_final_project


Hello and welcome to __Cluedo__!
This is our final project for the "Intro to AI" (67842) course.
We decided to build AI agents that play (and win!) in the game of Cluedo—a classic and well-known board game that involves a lot of strategic thinking, uncertainty, and indeterminacy. For more details on the game and its rules, refer to the attached project documentation.

As you will soon see, our agents are based on the algorithms and techniques we have learned throughout the course. You can choose to let them play against each other or join in yourself (but be warned, they are pretty good...).

__How to get started:__
In general, you can easily run cluedo_main.py to start a game with the default settings.
For a more customized experience, you can tweak the following parameters:

1. --players_num: The number of players. Any integer between 2 and 6. (Default: 2). _Note_: With more players, expect longer running times.
2. --suspects_num: The number of possible suspects to choose from. (Default: 6, Max: 10)
3. --weapons_num: The number of possible weapons to choose from. (Default: 6, Max: 10)
4. --ui: Turn the UI on ('y') or off ('n'). (Default: 'n')
5. --players: Choose the types of players: human (Manual), random (AI), minimax (AI), expectimax (AI), kr (AI). Specify a type for each player separated by spaces. (Default: "random expectimax")
6. --rounds: The number of game rounds to play. (Default: 1)
7. --test_mode: Run in test mode — no UI, no human players, only final (expanded) results. 'y' for yes, 'n' for no (Default: 'n')
8. --seed: Seed for reproducibility. (Default: 1)
(for example, you can use commands like: "python3 cluedo_main.py --rounds=3", "python3 cluedo_main.py --players_num=3 --players='kr kr random' --seed=123" etc)

Enjoy!
And for more details, questions and ideas, feel free to reach us at inbar.elmaliach@mail.huji.ac.il, noga.friedman@mail.huji.ac.il and metar.megiora@mail.huji.ac.il
