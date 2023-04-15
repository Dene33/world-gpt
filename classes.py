from dataclasses import dataclass, field
from yamldataclassconfig.config import YamlDataClassConfig
from yamldataclassconfig import create_file_path_field
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
    save_yaml,
    request_openai,
)
import validators
from prompt_toolkit import prompt
import prompts
from enum import Enum
from typing import Union
import yaml
import openai
import random


@dataclass
class Settings(YamlDataClassConfig):
    LLM_model: str = ""
    API_key: str = ""
    llm_request_tries_num: int = -1
    cur_game_name: str = ""
    cur_world_name: str = ""
    init_prompt: str = ""
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
        self.cur_game_path: Path = Path("./data") / self.settings.cur_game_name
        self.cur_world_path: Path = (
            Path("./data")
            / self.settings.cur_game_name
            / "worlds"
            / self.settings.cur_world_name
        )
        self.cur_npcs_path: Path = self.cur_world_path / "npcs"
        self.cur_global_goals_path: Path = self.cur_npcs_path / "global_goals.yaml"

        # World
        self.cur_world: World = World()
        self.world_prompt: str = None
        self.global_goals: GlobalGoals = GlobalGoals()

    def input_handler(self, user_input: Union[Input.init, Input.placeholder]):
        if isinstance(user_input, Input.init):
            self.input_handler_init(user_input)

    def input_handler_init(self, user_input):
        msg = f"You want to create {user_input}. Load the {user_input} or create a new one(s)? (l/n)"
        response = prompt(msg, validator=validators.InitValidator(self, user_input))

        # Load
        if response == "l":
            if user_input == Input.init.game:
                pass
            elif user_input == Input.init.world:
                self.load_world()
            # elif user_input == Input.init.npcs:
            #     load_name = ''
            load_name = getattr(self.settings, f"cur_{user_input}_name")
            print(
                f'{bcolors.OKGREEN}{user_input.capitalize()} "{load_name}" loaded{bcolors.ENDC}'
            )

        # Create new
        elif response == "n":
            if user_input == Input.init.game:
                self.cur_game_path.mkdir(parents=True, exist_ok=True)

            elif user_input == Input.init.world:
                self.new_world()
                self.new_global_goals()
                self.new_npcs()
            # elif user_input == Input.init.npcs:
            #     self.new_npcs()
            #     new_name = ''

            new_name = getattr(self.settings, f"cur_{user_input}_name")
            print(
                f"{bcolors.OKGREEN}{user_input.capitalize()} {new_name} created{bcolors.ENDC}"
            )

    def new_world(self):
        self.cur_world.name = self.settings.cur_world_name
        self.cur_world.number_of_npcs = int(
            prompt(
                "Input the number of npcs you want to create: ",
                validator=validators.is_number,
                validate_while_typing=True,
            )
        )

        self.cur_world.tick_type = prompt(
            "Input tick type (years/months/days/hours/minutes/seconds): ",
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

        self.cur_world.current_state_prompt = self.settings.init_prompt

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
        # self.create_npcs()

    def new_npcs(self):
        if not self.cur_npcs_path.exists():
            self.cur_npcs_path.mkdir(parents=True, exist_ok=True)

        for npc_num in range(self.cur_world.number_of_npcs):
            print(
                f"{bcolors.OKCYAN}Generating NPC {npc_num+1}/{self.cur_world.number_of_npcs}...{bcolors.ENDC}"
            )
            new_npc = Npc()

            with open("data/yaml_templates/npc.yaml", "r") as f:
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

    def load_world(self):
        world_yaml_path = get_last_modified_file(self.cur_world_path)
        self.cur_world.load(path=world_yaml_path)

    def save_world(self):
        self.cur_world_path.mkdir(parents=True, exist_ok=True)
        save_path = (
            self.cur_world_path / f"world_tick_{self.cur_world.current_tick}.yaml"
        )

        save_yaml(save_path, self.cur_world)

    def save_global_goals(self):
        self.cur_global_goals_path.parent.mkdir(parents=True, exist_ok=True)
        save_yaml(self.cur_global_goals_path, self.global_goals)

    def save_npc(self, npc: Npc):
        npc_dir = self.cur_npcs_path / npc.name
        npc_dir.mkdir(parents=True, exist_ok=True)
        save_yaml(npc_dir / f"npc_tick_{self.cur_world.current_tick}.yaml", npc)


if __name__ == "__main__":
    print(prompts.create_global_goals.safe_substitute())
