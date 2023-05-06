from dataclasses import dataclass, field
from yamldataclassconfig.config import YamlDataClassConfig
from pathlib import Path
import numpy as np
from utils import (
    get_last_modified_file,
    get_oldest_modified_file,
    bcolors,
    int_to_month,
    hour_to_pm_am,
    hour_to_daytime,
    Input,
    code_block_to_var,
    save_yaml_from_data,
    request_openai,
    load_yaml_to_dataclass,
    to_datetime,
    from_datetime,
    hour_to_iso,
    minute_to_iso,
    second_to_iso,
    populate_dataclass_with_dicts,
    yaml_from_str,
    YamlDumperDoubleQuotes,
)
import validators
from prompt_toolkit import prompt
from prompts import create_npc_request, create_global_goals
from typing import List, Union, Any
import yaml
import openai
import random
from resources_paths import DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH
import sys


@dataclass
class Settings(YamlDataClassConfig):
    LLM_model: str = ""
    API_key: str = ""
    llm_request_tries_num: int = -1
    npc_history_steps: int = 0
    npc_attributes_names: list[str] = field(default_factory=list)
    npc_num_global_goals: int = 0
    world_attributes_names: list[str] = field(default_factory=list)
    world_time_names: list[str] = field(default_factory=list)
    world_history_steps: int = 0


@dataclass
class World(YamlDataClassConfig):
    name: str = ""  # name of the world
    attributes: dict[str, Any] = field(default_factory=dict)  # attributes of the world
    time: dict[str, Any] = field(default_factory=dict)  # time of the world
    tick_type: str = ""  # years, months, days, hours, minutes, seconds, etc
    tick_rate: int = 0  # how much time of tick_type passes in the world per tick
    current_tick: int = 0  # indicates how many ticks passed
    current_state_prompt: str = ""


@dataclass
class Npc(YamlDataClassConfig):
    name: str = ""
    global_goal: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    current_state_prompt: str = ""


class Game:
    def __init__(self):
        # Settings
        self.settings: Settings = Settings()
        self.settings.load(path="./settings.yaml")
        openai.api_key = self.settings.API_key
        if not openai.api_key:
            openai.api_key = prompt("Provide OpenAI API key: ", is_password=True)

        # Paths
        self.game_path: Path = ""
        self.cur_world_path: Path = ""
        self.cur_npcs_path: Path = ""
        self.cur_global_goals_path: Path = ""

        # Game
        self.game_name: str = ""
        self.existing_games = [x.name for x in GAMES_PATH.iterdir() if x.is_dir()]
        self.existing_init_worlds = [
            x.name for x in INIT_WORLDS_PATH.iterdir() if x.is_file()
        ]

        # World
        self.cur_world: World = World()
        self.world_prompt: str = ""
        self.world_general_description: str = ""

        # Npcs
        self.npcs: List[Npc] = []
        self.global_goals: list = []

    def input_handler(self, user_input: Input):
        if user_input == Input.init_game:
            self.init_game()

        elif user_input == Input.init_world:
            self.init_world()

        elif user_input == Input.progress_world:
            self.progress_world()

        elif user_input == Input.info_world:
            self.print_info_world()

        elif user_input == Input.info_npcs:
            self.print_info_npcs()

        elif user_input == Input.info_everything:
            self.print_info_all()

        elif user_input == Input.quit_game:
            self.quit_game()

        return

    def prompt_next_action(self):
        next_action = prompt(
            "What would you like to do next? ",
            bottom_toolbar=f"(W)ait {self.cur_world.tick_rate} {self.cur_world.tick_type}s/(A)ll info/World (i)nfo/(N)PCs info/(Q)uit",
            validator=validators.NotInListValidator(
                ["W", "w", "A", "a", "I", "i", "N", "n", "Q", "q"]
            ),
            validate_while_typing=True,
        )

        if next_action in ["W", "w"]:
            next_action = Input.progress_world
        elif next_action in ["A", "a"]:
            next_action = Input.info_everything
        elif next_action in ["I", "i"]:
            next_action = Input.info_world
        elif next_action in ["N", "n"]:
            next_action = Input.info_npcs
        elif next_action in ["Q", "q"]:
            next_action = Input.quit_game
        self.input_handler(next_action)

        return

    def progress_world(self):
        self.tick_increment()

        self.save_world()
        self.save_npcs()

    def tick_increment(self):
        self.cur_time = to_datetime(
            self.cur_world.time["current_year"],
            self.cur_world.time["current_month"],
            self.cur_world.time["current_day"],
            self.cur_world.time["current_hour"],
            self.cur_world.time["current_minute"],
            self.cur_world.time["current_second"],
        )

        self.cur_world.current_tick += 1

        if self.cur_world.tick_type == "day":
            timeformat = self.cur_world.tick_type[0].capitalize()
        else:
            timeformat = self.cur_world.tick_type[0]

        time_delta = np.timedelta64(self.cur_world.tick_rate, timeformat)

        new_time = self.cur_time + time_delta

        (
            self.cur_world.time["current_year"],
            self.cur_world.time["current_month"],
            self.cur_world.time["current_day"],
            self.cur_world.time["current_hour"],
            self.cur_world.time["current_minute"],
            self.cur_world.time["current_second"],
            self.cur_world.time["current_era"],
        ) = from_datetime(new_time)

        print(
            f"{bcolors.OKGREEN}{self.cur_world.tick_rate} {self.cur_world.tick_type}s have passed...{bcolors.ENDC}"
        )
        self.print_current_time()

        return

    def init_game(self):
        new_or_load = prompt(
            f"You want to start a game. (L)oad the game or create a (n)ew one? (l/n)",
            validator=validators.NotInListValidator(
                ["N", "n", "new", "L", "l", "load"]
            ),
            validate_while_typing=True,
        )

        # New Game
        if new_or_load.lower() in ["n", "new"]:
            self.new_game()

        # Load Game
        elif new_or_load.lower() in ["l", "load"]:
            self.load_game()

        self.existing_worlds = [
            x.name for x in Path(self.game_path / "worlds").iterdir() if x.is_dir()
        ]

        return

    def new_game(self):
        self.game_name = prompt(
            f"Input the new game name: ",
            validator=validators.IsInListValidator(self.existing_games),
        )

        self.game_path = GAMES_PATH / self.game_name
        Path(self.game_path / "worlds").mkdir(parents=True, exist_ok=True)

        print(f"{bcolors.OKGREEN}The game: {self.game_name} is created{bcolors.ENDC}")

        return

    def load_game(self):
        if self.existing_games:
            self.game_name = prompt(
                f"Choose the game to load: {', '.join(self.existing_games)} :",
                validator=validators.NotInListValidator(self.existing_games),
            )
            self.game_path = GAMES_PATH / self.game_name

            print(
                f"{bcolors.OKGREEN}The game: {self.game_name} is loaded{bcolors.ENDC}"
            )
        else:
            print(
                f"{bcolors.FAIL}No existing games found. Create a new game.{bcolors.ENDC}"
            )
            self.input_handler(Input.init_game)

        return

    def init_world(self):
        new_or_load = prompt(
            f"(L)oad existing world or create a (n)ew one? (l/n)",
            validator=validators.NotInListValidator(
                ["N", "n", "new", "L", "l", "load"]
            ),
            validate_while_typing=True,
        )

        # New World
        if new_or_load.lower() in ["n", "new"]:
            self.new_world()

            self.cur_npcs_path: Path = self.cur_world_path / "npcs"
            self.cur_global_goals_path: Path = self.cur_npcs_path / "global_goals.yaml"
            self.new_global_goals()
            self.new_npcs()

        # Load World
        elif new_or_load.lower() in ["l", "load"]:
            self.load_world()
            self.load_npcs()

        return

    def new_world(self):
        template_or_input = prompt(
            f"Create a new world from the predefined (t)emplate or (i)nput world settings manually? (t/i)",
            validator=validators.NotInListValidator(["t", "template", "i", "input"]),
            validate_while_typing=True,
        )

        # Add the world attributes and time attributes to the current world from the settings
        populate_dataclass_with_dicts(
            self.cur_world,
            [self.settings.world_attributes_names, self.settings.world_time_names],
        )

        if template_or_input.lower() in ["t", "template"]:
            self.new_world_from_template()
        elif template_or_input.lower() in ["i", "input"]:
            self.new_world_from_input()

        return

    def new_world_from_template(self):
        self.is_in_existing_items(self.existing_init_worlds, "world", Input.init_world)

        world_template_name = prompt(
            f"Choose the world template to load: {', '.join(self.existing_init_worlds)} ",
            validator=validators.NotInListValidator(self.existing_init_worlds),
        )

        world_template_path = INIT_WORLDS_PATH / world_template_name
        load_yaml_to_dataclass(self.cur_world, world_template_path)

        if self.cur_world.name in self.existing_worlds:
            self.cur_world.name = prompt(
                f"World with name {self.cur_world.name} already exists. Choose a new name:",
                validator=validators.IsInListValidator(self.existing_worlds),
            )

        self.cur_world_path = (
            GAMES_PATH / self.game_name / "worlds" / self.cur_world.name
        )
        self.cur_world_path.mkdir(parents=True, exist_ok=True)

        self.world_general_description = self.cur_world.current_state_prompt

        self.save_world()

        print(
            f"{bcolors.OKGREEN}The world {self.cur_world.name} is created from template {world_template_name}{bcolors.ENDC}"
        )

        return

    def new_world_from_input(self):
        self.cur_world.name = prompt(
            "Input the name of the world: ",
            validator=validators.IsInListValidator(self.existing_worlds),
        )

        self.cur_world.attributes["temperature"] = float(
            prompt(
                "Input the temperature (in Celsius) of the world at current tick: ",
                validator=validators.is_float,
                validate_while_typing=True,
            )
        )

        self.cur_world.attributes["number_of_npcs"] = int(
            prompt(
                "Input the number of npcs you want to create: ",
                validator=validators.is_number,
                validate_while_typing=True,
            )
        )

        self.cur_world.attributes["current_era"] = prompt(
            "Input the current era (BC/AD) of the world: ",
            validator=validators.is_era,
            validate_while_typing=True,
        )

        self.cur_world.attributes["current_year"] = int(
            prompt(
                "Input the current year of the world: ",
                validator=validators.is_number,
                validate_while_typing=True,
            )
        )

        self.cur_world.attributes["current_month"] = int(
            prompt(
                "Input the current month of the world: ",
                validator=validators.is_month,
                validate_while_typing=True,
            )
        )

        self.cur_world.attributes["current_day"] = int(
            prompt(
                "Input the current day of the world: ",
                validator=validators.is_day,
                validate_while_typing=True,
            )
        )

        self.cur_world.attributes["current_hour"] = int(
            prompt(
                "Input the current hour of the world (24h format): ",
                validator=validators.is_hour,
                validate_while_typing=True,
            )
        )

        self.cur_world.attributes["current_minute"] = int(
            prompt(
                "Input the current minute of the world: ",
                validator=validators.is_minute,
                validate_while_typing=True,
            )
        )

        self.cur_world.attributes["current_second"] = int(
            prompt(
                "Input the current second of the world: ",
                validator=validators.is_second,
                validate_while_typing=True,
            )
        )

        self.cur_world.tick_type = prompt(
            "Input tick type (days/hours/minutes/seconds): ",
            validator=validators.is_tick_type,
            validate_while_typing=True,
        )

        self.cur_world.tick_rate = int(
            prompt(
                "Input the tick rate (how much time of tick_type passes in the world per tick): ",
                validator=validators.is_number,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_tick = 0

        self.cur_world.current_state_prompt = prompt(
            "Input the description of the current World state: "
        )

        self.world_general_description = self.cur_world.current_state_prompt

        self.cur_world_path = (
            GAMES_PATH / self.game_name / "worlds" / self.cur_world.name
        )

        self.save_world()

        print(
            f"{bcolors.OKGREEN}The world {self.cur_world.name} is loaded from input{bcolors.ENDC}"
        )

        return

    def load_world(self):
        self.is_in_existing_items(self.existing_worlds, "world", Input.init_world)

        world_name_to_load = prompt(
            f"Choose the world to load: {', '.join(self.existing_worlds)} ",
            validator=validators.NotInListValidator(self.existing_worlds),
        )
        self.cur_world_path = Path(self.game_path / "worlds" / world_name_to_load)
        last_modified_world_yaml = get_last_modified_file(self.cur_world_path)
        load_yaml_to_dataclass(self.cur_world, last_modified_world_yaml)

        oldest_modified_world_yaml = get_oldest_modified_file(self.cur_world_path)
        with open(oldest_modified_world_yaml) as f:
            oldest_modified_world = yaml.safe_load(f)
        self.world_general_description = oldest_modified_world["current_state_prompt"]

        print(
            f"{bcolors.OKGREEN}The world: {self.cur_world.name} is loaded{bcolors.ENDC}"
        )

        return

    def new_npcs(self):
        if not self.cur_npcs_path.exists():
            self.cur_npcs_path.mkdir(parents=True, exist_ok=True)

        for npc_num in range(self.cur_world.attributes["number_of_npcs"]):
            print(
                f"{bcolors.OKCYAN}Generating NPC {npc_num+1}/{self.cur_world.attributes['number_of_npcs']}...{bcolors.ENDC}"
            )
            new_npc = Npc()
            self.npcs.append(new_npc)

            populate_dataclass_with_dicts(new_npc, [self.settings.npc_attributes_names])

            new_npc_prompt = create_npc_request.format(
                world_general_description=self.world_general_description,
                world_current_attributes=self.cur_world.attributes,
                npc_yaml_template=yaml.dump(
                    new_npc, sort_keys=False, Dumper=YamlDumperDoubleQuotes
                ),
                global_goal=random.choice(self.global_goals),
            )

            print("new_npc_prompt", new_npc_prompt)

            new_npc_data = request_openai(
                model=self.settings.LLM_model,
                prompt=new_npc_prompt,
                tries_num=self.settings.llm_request_tries_num,
                response_processor=yaml_from_str,
                verbose=True,
            )

            self.save_npc(new_npc_data)
            new_npc_yaml_path = (
                self.cur_npcs_path
                / new_npc_data["name"]
                / f"npc_tick_{self.cur_world.current_tick}.yaml"
            )

            load_yaml_to_dataclass(new_npc, new_npc_yaml_path)

            print(
                f"{bcolors.OKGREEN}NPC {new_npc.name} generated successfully{bcolors.ENDC}"
            )

        return

    def load_npcs(self):
        self.cur_npcs_path = self.cur_world_path / "npcs"

        for npc_path in self.cur_npcs_path.iterdir():
            # Skip global_goals.yaml file
            if npc_path.name == "global_goals.yaml":
                continue

            new_npc = Npc()
            last_modified_npc_yaml = get_last_modified_file(npc_path)
            load_yaml_to_dataclass(new_npc, last_modified_npc_yaml)
            self.npcs.append(new_npc)

    def new_global_goals(self):
        print(f"{bcolors.OKCYAN}Generating global goals for NPCs...{bcolors.ENDC}")

        # Duplicate, refactor later
        with open(YAML_TEMPLATES_PATH / "npc.yaml", "r") as f:
            npc_yaml_template = yaml.safe_load(f)

        for attribute in self.settings.npc_attributes_names:
            npc_yaml_template["attributes"][attribute] = 0

        with open(YAML_TEMPLATES_PATH / "global_goals.yaml", "r") as f:
            npc_global_goals_template = yaml.safe_load(f)

        create_global_goals_prompt = create_global_goals.format(
            world_general_description=self.world_general_description,
            npc_yaml_template=yaml.dump(
                npc_yaml_template, sort_keys=False, Dumper=YamlDumperDoubleQuotes
            ),
            num_global_goals=self.settings.npc_num_global_goals,
            global_goals_yaml_template=yaml.dump(
                npc_global_goals_template,
                sort_keys=False,
                Dumper=YamlDumperDoubleQuotes,
            ),
        )

        self.global_goals = request_openai(
            model=self.settings.LLM_model,
            prompt=create_global_goals_prompt,
            tries_num=self.settings.llm_request_tries_num,
            response_processor=yaml_from_str,
            verbose=True,
        )

        self.save_global_goals()
        print(f"{bcolors.OKGREEN}Global goals generated successfully{bcolors.ENDC}")

        return

    def save_world(self):
        self.cur_world_path.mkdir(parents=True, exist_ok=True)
        save_path = (
            self.cur_world_path / f"world_tick_{self.cur_world.current_tick}.yaml"
        )

        save_yaml_from_data(save_path, self.cur_world)

        return

    def save_global_goals(self):
        self.cur_global_goals_path.parent.mkdir(parents=True, exist_ok=True)
        save_yaml_from_data(self.cur_global_goals_path, self.global_goals)

        return

    def save_npcs(self):
        for npc in self.npcs:
            self.save_npc(npc)

        return

    def save_npc(self, npc_data: dict | Npc):
        if isinstance(npc_data, dict):
            npc_name = npc_data["name"]
        else:
            npc_name = npc_data.name

        npc_dir = self.cur_npcs_path / npc_name
        npc_dir.mkdir(parents=True, exist_ok=True)
        save_yaml_from_data(
            npc_dir / f"npc_tick_{self.cur_world.current_tick}.yaml", npc_data
        )

        return

    def is_in_existing_items(
        self, existing_items: List | None, item_name: str, input_type: Input
    ):
        if not existing_items:
            print(
                f"{bcolors.FAIL}No existing {item_name}s found. Create a new {item_name}.{bcolors.ENDC}"
            )

            self.input_handler(input_type)

        return

    def print_info_world(self):
        self.print_current_time()

        npc_names = [npc.name for npc in self.npcs]
        print(
            f"\n"
            f"{bcolors.OKBLUE}World name: {bcolors.ENDC}{self.cur_world.name}\n"
            f"{bcolors.OKBLUE}Current state: {bcolors.ENDC}{self.cur_world.current_state_prompt}\n"
            f"{bcolors.OKBLUE}Time: {bcolors.ENDC}{self.cur_world.time}\n"
            f"{bcolors.OKBLUE}Attributes: {bcolors.ENDC}{self.cur_world.attributes}\n"
            f"{bcolors.OKBLUE}Current tick: {bcolors.ENDC}{self.cur_world.current_tick}\n"
            f"{bcolors.OKBLUE}Tick type: {bcolors.ENDC}{self.cur_world.tick_type}\n"
            f"{bcolors.OKBLUE}Tick rate: {bcolors.ENDC}{self.cur_world.tick_rate}\n"
            f"{bcolors.OKBLUE}NPCs: {bcolors.ENDC}{npc_names}"
            f"\n"
        )

        return

    def print_info_npcs(self):
        for npc in self.npcs:
            print(
                f"\n"
                f"{bcolors.OKBLUE}NPC name: {bcolors.ENDC}{npc.name}\n"
                f"{bcolors.OKBLUE}Current state: {bcolors.ENDC}{npc.current_state_prompt}\n"
                f"{bcolors.OKBLUE}Global goal: {bcolors.ENDC}{npc.global_goal}\n"
                f"{bcolors.OKBLUE}Attributes: {bcolors.ENDC}{npc.attributes}\n"
                f"\n"
            )

        return

    def print_info_all(self):
        self.print_info_world()
        self.print_info_npcs()

        return

    def print_current_time(self):
        current_time = (
            f"{bcolors.OKBLUE}"
            f"Current time:{bcolors.ENDC} {self.cur_world.time['current_day']} {int_to_month(self.cur_world.time['current_month'])},"
            f"{self.cur_world.time['current_year']} {self.cur_world.time['current_era']}. "
            f"{hour_to_iso(self.cur_world.time['current_hour'])}:{minute_to_iso(self.cur_world.time['current_minute'])}:"
            f"{second_to_iso(self.cur_world.time['current_second'])}"
        )

        print(current_time)

        return

    def quit_game(self):
        print(f"{bcolors.OKCYAN}Quitting game...{bcolors.ENDC}")
        sys.exit(0)


if __name__ == "__main__":
    with open(YAML_TEMPLATES_PATH / "npc.yaml", "r") as f:
        npc_yaml_template = yaml.safe_load(f)

    t = ["happiness", "health", "hunger", "love", "rested", "stress", "wealth"]

    for i in t:
        npc_yaml_template["attributes"][i] = 0
    print(npc_yaml_template["attributes"])
    print(npc_yaml_template)
