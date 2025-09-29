# Cluedo AI Agents 🎲🕵️‍♀️

This project was developed as the final project for the course Introduction to AI (67842) at HUJI.  
We built a full implementation of the board game Cluedo, along with multiple AI agents that can play (and often win) the game — against each other or against a human player.

<img src="https://github.com/user-attachments/assets/9b8e035e-a997-48d8-b5f3-7d3303ac26fe" width="400">

# About the Project
Cluedo is a deduction-based board game full of uncertainty, hidden information, and strategy.  
At the start of the game, three hidden cards (suspect, weapon, room) form the murder mystery.  
Players collect information by moving around the board, making suggestions, and eliminating possibilities — until someone solves the mystery.  

Our AI agents are based on algorithms studied in the course:
- Random Agent – baseline.
- Minimax Agent – adversarial search with heuristics.
- Expectimax Agent – probabilistic search under uncertainty.
- Knowledge Representation (KR) Agent – logical deduction using forward chaining.

# Results at a Glance
- The KR agent consistently achieved the highest win rate, especially in multiplayer matches.  
- Expectimax performed well under uncertainty but was slower.
- Minimax made smart moves but struggled more than expected in practice.
- Random agents... remained random.

(See the [full paper](https://github.com/user-attachments/files/22604572/67842_Final_project_documentation_-_Cluedo_final.1.pdf) for detailed benchmarks, comparisons, and insights.)

# Getting Started
__Run a game with default settings:__  
python3 cluedo_main.py

__Customize with parameters:__   
1. --players_num: number of players (2–6, default: 2).  
2. --suspects_num: number of suspects (default: 6, max: 10).  
3. --weapons_num: number of weapons (default: 6, max: 10).  
4. --ui: show UI ('y'/'n', default: 'n').  
5. --players: the types of players: human (Manual), random (AI), minimax (AI), expectimax (AI), kr (AI). Specify a type for each player separated by spaces (default: "random expectimax").  
6. --rounds: number of rounds (default: 1).  
7. --test_mode: compact mode, no UI or humans ('y'/'n', default: 'n').  
8. --seed: random seed for reproducibility (default: 1).  

Examples:  
python3 cluedo_main.py --rounds=3  
python3 cluedo_main.py --players_num=3 --players="kr kr random" --seed=123  

# Project Structure
cluedo_main.py – entry point to run the game.  
algorithms/ – AI agent implementations.  
game_elements/ – core game logic and mechanics (board, cards, game state).  
ui/ – frontend and game interface.  
resources/ – supplementary materials.  

# Documentation
For a deep dive into methodology, experiments, and results, check out the [full project report (PDF)](https://github.com/user-attachments/files/22604572/67842_Final_project_documentation_-_Cluedo_final.1.pdf).

# Contributors
- [Noga Friedman](mailto:noga.fri@mail.huji.ac.il)  
- [Inbar Elmaliach](mailto:inbar.elmaliach@mail.huji.ac.il)  
- [Metar Megiora](mailto:metar.megiora@mail.huji.ac.il)
