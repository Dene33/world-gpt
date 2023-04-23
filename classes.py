from dataclasses import dataclass, field
from yamldataclassconfig.config import YamlDataClassConfig
from pathlib import Path
import numpy as np
from utils import (
    get_last_modified_file,
    bcolors,
    int_to_month,
    hour_to_pm_am,
    hour_to_daytime,
    Input,
    code_block_to_var,
    save_yaml_from_dataclass,
    request_openai,
    load_yaml_to_dataclass,
    to_datetime,
    from_datetime,
    hour_to_iso,
    minute_to_iso,
    second_to_iso,
)
import validators
from prompt_toolkit import prompt
import prompts
from typing import List, Union
import yaml
import openai
import random
from resources_paths import DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH


@dataclass
class Settings(YamlDataClassConfig):
    LLM_model: str = ""
    API_key: str = ""
    llm_request_tries_num: int = -1
    npc_history_steps: int = 0
    world_history_steps: int = 0
    num_global_goals: int = 0


@dataclass
class World(YamlDataClassConfig):
    name: str = ""  # name of the world
    number_of_npcs: int = 0
    tick_type: str = ""  # years, months, days, hours, minutes, seconds, etc
    tick_rate: int = 0  # how much time of tick_type passes in the world per tick
    current_tick: int = 0  # indicates how many ticks passed
    temperature: float = 0.0  # temperature of the world in Celsius
    current_era: str = ""  # era of the world
    current_year: int = 0
    current_month: int = 0
    current_day: int = 0
    current_hour: int = 0
    current_minute: int = 0
    current_second: int = 0
    current_state_prompt: str = ""


@dataclass
class Npc(YamlDataClassConfig):
    name: str = ""
    global_goal: str = ""
    happiness: str = ""
    love: str = ""
    health: str = ""
    rested: str = ""
    wealth: str = ""
    hunger: str = ""
    stress: str = ""
    current_state_prompt: str = ""


@dataclass
class GlobalGoals(YamlDataClassConfig):
    global_goals: list[str] = field(default_factory=list)


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
        self.global_goals: GlobalGoals = GlobalGoals()

    def input_handler(self, user_input: Input.init | Input.tick):
        if user_input == Input.init.game:
            self.init_game()

        elif user_input == Input.init.world:
            self.init_world()

        elif user_input == Input.tick.increment:
            self.tick_increment()
            self.save_world()

        return

    def print_current_time(self):
        current_time = (
            f"{bcolors.OKBLUE}"
            f"Current time: {self.cur_world.current_day} {int_to_month(self.cur_world.current_month)},"
            f"{self.cur_world.current_year} {self.cur_world.current_era} \n"
            f"{hour_to_iso(self.cur_world.current_hour)}:{minute_to_iso(self.cur_world.current_minute)}:"
            f"{second_to_iso(self.cur_world.current_second)}{bcolors.ENDC}"
        )

        print(current_time)

    def tick_increment(self):
        self.cur_time = to_datetime(
            self.cur_world.current_year,
            self.cur_world.current_month,
            self.cur_world.current_day,
            self.cur_world.current_hour,
            self.cur_world.current_minute,
            self.cur_world.current_second,
        )

        self.print_current_time()

        tick_increment = prompt(
            f"{self.cur_world.tick_rate} {self.cur_world.tick_type}(s) will pass. Continue? (y/n)",
            validator=validators.NotInListValidator(["Y", "y", "yes", "N", "n", "no"]),
            validate_while_typing=True,
        )

        if tick_increment.lower() in ["y", "yes"]:
            self.cur_world.current_tick += 1

            if self.cur_world.tick_type == "day":
                timeformat = self.cur_world.tick_type[0].capitalize()
            else:
                timeformat = self.cur_world.tick_type[0]

            time_delta = np.timedelta64(self.cur_world.tick_rate, timeformat)

            new_time = self.cur_time + time_delta

            (
                self.cur_world.current_year,
                self.cur_world.current_month,
                self.cur_world.current_day,
                self.cur_world.current_hour,
                self.cur_world.current_minute,
                self.cur_world.current_second,
                self.cur_world.current_era,
            ) = from_datetime(new_time)

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
        self.is_in_existing_items(self.existing_games, "game", Input.init.game)

        self.game_name = prompt(
            f"Choose the game to load: {', '.join(self.existing_games)} :",
            validator=validators.NotInListValidator(self.existing_games),
        )
        self.game_path = GAMES_PATH / self.game_name

        print(f"{bcolors.OKGREEN}The game: {self.game_name} is loaded{bcolors.ENDC}")

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

        # Load World
        elif new_or_load.lower() in ["l", "load"]:
            self.load_world()

        return

    def new_world(self):
        template_or_input = prompt(
            f"Create a new world from the predefined (t)emplate or (i)nput world settings manually? (t/i)",
            validator=validators.NotInListValidator(["t", "template", "i", "input"]),
            validate_while_typing=True,
        )

        if template_or_input.lower() in ["t", "template"]:
            self.new_world_from_template()
        elif template_or_input.lower() in ["i", "input"]:
            self.new_world_from_input()

        self.cur_npcs_path: Path = self.cur_world_path / "npcs"
        self.cur_global_goals_path: Path = self.cur_npcs_path / "global_goals.yaml"
        self.new_global_goals()
        self.new_npcs()

        return

    def new_world_from_template(self):
        self.is_in_existing_items(self.existing_init_worlds, "world", Input.init.world)

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

        self.world_prompt = prompts.create_world.substitute(
            world_state_prompt=self.cur_world.current_state_prompt,
            temperature=self.cur_world.temperature,
            day=self.cur_world.current_day,
            month=int_to_month(self.cur_world.current_month),
            year=self.cur_world.current_year,
            era=self.cur_world.current_era,
            hour=self.cur_world.current_hour,
            minute=self.cur_world.current_minute,
            second=self.cur_world.current_second,
            pm_am=hour_to_pm_am(self.cur_world.current_hour),
            daytime=hour_to_daytime(self.cur_world.current_hour),
        )

        self.save_world()

        print(
            f"{bcolors.OKGREEN}The world {self.cur_world.name} is loaded from template {world_template_name}{bcolors.ENDC}"
        )

        return

    def new_world_from_input(self):
        self.cur_world.name = prompt(
            "Input the name of the world: ",
            validator=validators.IsInListValidator(self.existing_worlds),
        )

        self.cur_world.number_of_npcs = int(
            prompt(
                "Input the number of npcs you want to create: ",
                validator=validators.is_number,
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
        self.cur_world.temperature = float(
            prompt(
                "Input the temperature (in Celsius) of the world at current tick: ",
                validator=validators.is_float,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_era = prompt(
            "Input the current era (BC/AD) of the world: ",
            validator=validators.is_era,
            validate_while_typing=True,
        )

        self.cur_world.current_year = int(
            prompt(
                "Input the current year of the world: ",
                validator=validators.is_number,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_month = int(
            prompt(
                "Input the current month of the world: ",
                validator=validators.is_month,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_day = int(
            prompt(
                "Input the current day of the world: ",
                validator=validators.is_day,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_hour = int(
            prompt(
                "Input the current hour of the world (24h format): ",
                validator=validators.is_hour,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_minute = int(
            prompt(
                "Input the current minute of the world: ",
                validator=validators.is_minute,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_second = int(
            prompt(
                "Input the current second of the world: ",
                validator=validators.is_second,
                validate_while_typing=True,
            )
        )

        self.cur_world.current_state_prompt = prompt(
            "Input the description of the current World state: "
        )

        self.world_prompt = prompts.create_world.substitute(
            world_state_prompt=self.cur_world.current_state_prompt,
            temperature=self.cur_world.temperature,
            day=self.cur_world.current_day,
            month=int_to_month(self.cur_world.current_month),
            year=self.cur_world.current_year,
            era=self.cur_world.current_era,
            hour=self.cur_world.current_hour,
            minute=self.cur_world.current_minute,
            second=self.cur_world.current_second,
            pm_am=hour_to_pm_am(self.cur_world.current_hour),
            daytime=hour_to_daytime(self.cur_world.current_hour),
        )

        self.cur_world_path = (
            GAMES_PATH / self.game_name / "worlds" / self.cur_world.name
        )

        self.save_world()

        print(
            f"{bcolors.OKGREEN}The world {self.cur_world.name} is loaded from input{bcolors.ENDC}"
        )

        return

    def load_world(self):
        self.is_in_existing_items(self.existing_worlds, "world", Input.init.world)

        world_name_to_load = prompt(
            f"Choose the world to load: {', '.join(self.existing_worlds)} ",
            validator=validators.NotInListValidator(self.existing_worlds),
        )
        self.cur_world_path = Path(self.game_path / "worlds" / world_name_to_load)
        last_modified_world_yaml = get_last_modified_file(self.cur_world_path)
        load_yaml_to_dataclass(self.cur_world, last_modified_world_yaml)

        return

    def new_npcs(self):
        if not self.cur_npcs_path.exists():
            self.cur_npcs_path.mkdir(parents=True, exist_ok=True)

        for npc_num in range(self.cur_world.number_of_npcs):
            print(
                f"{bcolors.OKCYAN}Generating NPC {npc_num+1}/{self.cur_world.number_of_npcs}...{bcolors.ENDC}"
            )
            new_npc = Npc()

            with open(YAML_TEMPLATES_PATH / "npc.yaml", "r") as f:
                npc_yaml_template = yaml.safe_load(f)

            new_npc_prompt = prompts.create_npc.substitute(
                world_prompt=self.world_prompt,
                temperature=self.cur_world.temperature,
                day=self.cur_world.current_day,
                month=int_to_month(self.cur_world.current_month),
                year=self.cur_world.current_year,
                era=self.cur_world.current_era,
                hour=self.cur_world.current_hour,
                minute=self.cur_world.current_minute,
                second=self.cur_world.current_second,
                pm_am=hour_to_pm_am(self.cur_world.current_hour),
                daytime=hour_to_daytime(self.cur_world.current_hour),
                npc_yaml_template=npc_yaml_template,
                global_goal=random.choice(self.global_goals.global_goals),
            )

            new_npc_data = request_openai(
                model=self.settings.LLM_model,
                prompt=new_npc_prompt,
                tries_num=self.settings.llm_request_tries_num,
                response_processor=code_block_to_var,
                verbose=True,
            )

            for k, v in new_npc_data.items():
                setattr(new_npc, k, v)

            self.save_npc(new_npc)

            print(
                f"{bcolors.OKGREEN}NPC {new_npc.name} generated successfully{bcolors.ENDC}"
            )

        return

    def new_global_goals(self):
        print(f"{bcolors.OKCYAN}Generating global goals for NPCs...{bcolors.ENDC}")
        create_global_goals_prompt = prompts.create_global_goals.substitute(
            world_prompt=self.world_prompt,
            num_global_goals=self.settings.num_global_goals,
        )

        global_goals = request_openai(
            model=self.settings.LLM_model,
            prompt=create_global_goals_prompt,
            tries_num=self.settings.llm_request_tries_num,
            response_processor=code_block_to_var,
        )

        self.global_goals.global_goals = global_goals

        self.save_global_goals()
        print(f"{bcolors.OKGREEN}Global goals generated successfully{bcolors.ENDC}")

        return

    def save_world(self):
        self.cur_world_path.mkdir(parents=True, exist_ok=True)
        save_path = (
            self.cur_world_path / f"world_tick_{self.cur_world.current_tick}.yaml"
        )

        save_yaml_from_dataclass(save_path, self.cur_world)

        return

    def save_global_goals(self):
        self.cur_global_goals_path.parent.mkdir(parents=True, exist_ok=True)
        save_yaml_from_dataclass(self.cur_global_goals_path, self.global_goals)

        return

    def save_npc(self, npc: Npc):
        npc_dir = self.cur_npcs_path / npc.name
        npc_dir.mkdir(parents=True, exist_ok=True)
        save_yaml_from_dataclass(
            npc_dir / f"npc_tick_{self.cur_world.current_tick}.yaml", npc
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
