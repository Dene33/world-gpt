from classes import Settings, Game
from pathlib import Path
from utils import Input

def main():
    game = Game()
    
    # game.init_game_input_handler()
    # game.init_world_input_handler()
    game.input_handler(Input.init.game)
    game.input_handler(Input.init.world)
    # game.input_handler(Input.init.npcs)

    # game = Game()
    # game.load()
    print(game.cur_world)
    print(game.global_goals)

if __name__ == '__main__':
    main()