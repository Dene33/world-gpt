from classes import Settings, Game
from pathlib import Path
from utils import Input, ensure_dirs_exist
from resources_paths import DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH


def main():
    ensure_dirs_exist([DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH])

    game = Game()

    game.input_handler(Input.init_game)
    game.input_handler(Input.init_world)
    # game.input_handler(Input.init.npcs)

    # print(game.cur_world)
    # print(game.global_goals)

    while True:
        game.prompt_next_action()
        # game.input_handler(Input.tick.increment)


if __name__ == "__main__":
    main()
