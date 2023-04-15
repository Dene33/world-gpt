from classes import Settings, Game
from pathlib import Path
from utils import Input


def main():
    game = Game()

    game.input_handler(Input.init.game)
    game.input_handler(Input.init.world)
    # game.input_handler(Input.init.npcs)

    print(game.cur_world)
    print(game.global_goals)


if __name__ == "__main__":
    main()
