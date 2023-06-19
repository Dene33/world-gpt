from dataclasses import dataclass, field
from yamldataclassconfig.config import YamlDataClassConfig
from pathlib import Path
import numpy as np
from utils import (
    get_last_modified_file,
    get_oldest_modified_file,
    bcolors,
    int_to_month,
    Input,
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
    dataclass_to_dict_copy,
    load_yaml,
    get_previous_to_last_modified_file,
    is_year_leap,
    check_yaml_update_npc,
    check_yaml_new_npc,
    # debug,
)
import validators
from prompt_toolkit import prompt
from prompts import (
    create_npc_request,
    create_global_goals,
    create_social_connections,
    world_new_state,
    npc_new_state,
)
from typing import List, Union, Any
import yaml
import openai
import random
from resources_paths import DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH
import sys

from logging import debug


@dataclass
class Settings(YamlDataClassConfig):
    LLM_model: str = ""
    API_key: str = ""
    openai_verbose: bool = False
    llm_request_tries_num: int = -1
    npc_history_steps: int = 0
    npc_attributes_names: list[str] = field(default_factory=list)
    max_attribute_delta: int = 0
    npc_num_global_goals: int = 0
    max_npc_social_connections: int = 0
    number_of_npcs: int = 0
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
    social_connections: list[str] = field(default_factory=list)
    current_state_prompt: str = ""


class Game:
    def __init__(self):
        # Settings
        self.settings: Settings = Settings()
        self.settings.load(path="./settings.yaml")
        # openai.api_key = self.settings.API_key
        # openai.api_key = ""
        # if not openai.api_key:
        #     openai.api_key = prompt("Provide OpenAI API key: ", is_password=True)

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

    async def progress_world(self):
        await self.tick_increment()
        await self.update_world()
        await self.update_npcs()

        self.save_world()
        self.save_npcs()

        return self

    async def update_world(self):
        world_new_state_request = world_new_state.format(
            init_state=self.world_general_description,
            previous_state=get_previous_to_last_modified_file(self.cur_world_path),
            current_state=self.cur_world.current_state_prompt,
            attributes=self.cur_world.attributes,
            date=self.current_date_to_str(),
            tick_rate=self.cur_world.tick_rate,
            tick_type=self.cur_world.tick_type,
        )

        debug(world_new_state_request)

        new_world_state = await request_openai(
            model=self.settings.LLM_model,
            prompt=world_new_state_request,
            tries_num=self.settings.llm_request_tries_num,
            response_processors=[yaml_from_str],
            verbose=self.settings.openai_verbose,
            api_key=self.settings.API_key,
        )

        self.cur_world.current_state_prompt = new_world_state["world_new_state"]

        for attribute_key in self.cur_world.attributes.keys():
            new_attribute_value = new_world_state["attributes"].get(attribute_key, None)
            if new_attribute_value:
                self.cur_world.attributes[attribute_key] = new_attribute_value

        return

    async def update_npcs(self):
        for npc in self.npcs:
            await self.update_npc(npc)

        return

    async def update_npc(self, current_npc: Npc):
        keys_to_delete = [
            key
            for key in self.npcs[0].__dict__.keys()
            if key not in ["name", "current_state_prompt"]
        ]
        other_npcs = [
            dataclass_to_dict_copy(npc, keys_to_delete)
            for npc in self.npcs
            if npc.name != current_npc.name
        ]

        npc_new_state_request = npc_new_state.format(
            world_general_description=self.world_general_description,
            world_current_state=self.cur_world.current_state_prompt,
            world_attributes=self.cur_world.attributes,
            date=self.current_date_to_str(),
            current_npc=yaml.dump(
                current_npc, sort_keys=False, Dumper=YamlDumperDoubleQuotes
            ),
            other_npcs=other_npcs,
            tick_rate=self.cur_world.tick_rate,
            tick_type=self.cur_world.tick_type,
            max_attribute_delta=self.settings.max_attribute_delta,
        )

        npc_new_data = await request_openai(
            model=self.settings.LLM_model,
            prompt=npc_new_state_request,
            tries_num=self.settings.llm_request_tries_num,
            response_processors=[yaml_from_str, check_yaml_update_npc],
            verbose=self.settings.openai_verbose,
            api_key=self.settings.API_key,
        )

        current_npc.current_state_prompt = npc_new_data["npc_new_state"]

        for attribute_key in current_npc.attributes.keys():
            new_attribute_value = npc_new_data["attributes"].get(attribute_key, 0)
            current_npc.attributes[attribute_key] += new_attribute_value
        # current_npc.attributes = npc_new_data["attributes"].copy()

        return

    async def tick_increment(self):
        self.cur_time = to_datetime(
            self.cur_world.time["current_year"],
            self.cur_world.time["current_month"],
            self.cur_world.time["current_day"],
            self.cur_world.time["current_hour"],
            self.cur_world.time["current_minute"],
            self.cur_world.time["current_second"],
        )

        self.cur_world.current_tick += 1

        if self.cur_world.tick_type in ("day", "year"):
            timeformat = self.cur_world.tick_type[0].capitalize()
        else:
            timeformat = self.cur_world.tick_type[0]

        if not self.cur_world.tick_type == "year":
            time_delta = np.timedelta64(self.cur_world.tick_rate, timeformat)
        else:
            if is_year_leap(self.cur_time.astype("datetime64[Y]").astype(int)):
                days = 366
            else:
                days = 365
            time_delta = np.timedelta64(self.cur_world.tick_rate * days, "D")

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

        debug(
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

    def new_game(self, game_name: str = None):
        if not game_name:
            self.game_name = prompt(
                f"Input the new game name: ",
                validator=validators.IsInListValidator(self.existing_games),
            )
        else:
            self.game_name = game_name

        self.game_path = GAMES_PATH / self.game_name
        Path(self.game_path / "worlds").mkdir(parents=True, exist_ok=True)

        debug(f"{bcolors.OKGREEN}The game: {self.game_name} is created{bcolors.ENDC}")

        return

    def load_game(self):
        if self.existing_games:
            self.game_name = prompt(
                f"Choose the game to load: {', '.join(self.existing_games)} :",
                validator=validators.NotInListValidator(self.existing_games),
            )
            self.game_path = GAMES_PATH / self.game_name

            debug(
                f"{bcolors.OKGREEN}The game: {self.game_name} is loaded{bcolors.ENDC}"
            )
        else:
            debug(
                f"{bcolors.FAIL}No existing games found. Create a new game.{bcolors.ENDC}"
            )
            self.input_handler(Input.init_game)

        return

    async def init_world(self, world_data: dict = None):
        if world_data:
            new_or_load = "n"
        else:
            new_or_load = prompt(
                f"(L)oad existing world or create a (n)ew one? (l/n)",
                validator=validators.NotInListValidator(
                    ["N", "n", "new", "L", "l", "load"]
                ),
                validate_while_typing=True,
            )

        # New World
        if new_or_load.lower() in ["n", "new"]:
            self.new_world(world_data)

            self.cur_npcs_path: Path = self.cur_world_path / "npcs"
            self.cur_global_goals_path: Path = self.cur_npcs_path / "global_goals.yaml"
            await self.new_global_goals()
            await self.new_npcs()
            await self.new_npcs_social_connections()

        # Load World
        elif new_or_load.lower() in ["l", "load"]:
            self.load_world()
            self.load_npcs()

        return self

    def new_world(self, world_data: dict = None):
        # Add the world attributes and time attributes to the current world from the settings
        populate_dataclass_with_dicts(
            self.cur_world,
            [self.settings.world_attributes_names, self.settings.world_time_names],
        )

        if world_data:
            self.new_world_from_ui(world_data)
        else:
            template_or_input = prompt(
                f"Create a new world from the predefined (t)emplate or (i)nput world settings manually? (t/i)",
                validator=validators.NotInListValidator(
                    ["t", "template", "i", "input"]
                ),
                validate_while_typing=True,
            )

            if template_or_input.lower() in ["t", "template"]:
                self.new_world_from_template()
            elif template_or_input.lower() in ["i", "input"]:
                self.new_world_from_input()

        return

    def new_world_from_ui(self, world_data: dict):
        self.cur_world.name = world_data["name"]
        debug(self.cur_world.name)
        debug(type(self.cur_world.name))

        for attribute_key in self.cur_world.attributes.keys():
            new_attribute_value = world_data["attributes"].get(attribute_key, None)
            if new_attribute_value is not None:
                self.cur_world.attributes[attribute_key] = new_attribute_value
        self.cur_world.time = world_data["time"]
        self.cur_world.tick_type = world_data["tick_type"]
        self.cur_world.tick_rate = world_data["tick_rate"]
        self.cur_world.current_state_prompt = world_data["current_state_prompt"]

        self.cur_world_path = (
            GAMES_PATH / self.game_name / "worlds" / self.cur_world.name
        )
        self.cur_world_path.mkdir(parents=True, exist_ok=True)

        self.world_general_description = self.cur_world.current_state_prompt

        self.save_world()

        debug(
            f"{bcolors.OKGREEN}The world {self.cur_world.name} is created from UI{bcolors.ENDC}"
        )

        return

    def settings_from_ui(self, settings_data: dict):
        for key in self.settings.__dict__.keys():
            new_settings_value = settings_data.get(key, None)
            if new_settings_value:
                setattr(self.settings, key, new_settings_value)

        self.save_settings_from_ui()
        return

    def save_settings_from_ui(self):
        self.game_path.mkdir(parents=True, exist_ok=True)
        save_path = self.game_path / f"settings.yaml"

        save_yaml_from_data(save_path, self.settings)

        return

    def new_world_from_template(self):
        if not self.is_in_existing_items(self.existing_init_worlds, "world"):
            self.input_handler(Input.init_world)
            return

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

        debug(
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

        self.settings.number_of_npcs = int(
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

        debug(
            f"{bcolors.OKGREEN}The world {self.cur_world.name} is loaded from input{bcolors.ENDC}"
        )

        return

    def load_world(self):
        if not self.is_in_existing_items(self.existing_worlds, "world"):
            self.input_handler(Input.init_world)
            return

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

        debug(
            f"{bcolors.OKGREEN}The world: {self.cur_world.name} is loaded{bcolors.ENDC}"
        )

        return

    async def new_npcs(self):
        if not self.cur_npcs_path.exists():
            self.cur_npcs_path.mkdir(parents=True, exist_ok=True)

        for npc_num in range(self.settings.number_of_npcs):
            debug(
                f"{bcolors.OKCYAN}Generating NPC {npc_num+1}/{self.settings.number_of_npcs}...{bcolors.ENDC}"
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

            new_npc_data = await request_openai(
                model=self.settings.LLM_model,
                prompt=new_npc_prompt,
                tries_num=self.settings.llm_request_tries_num,
                response_processors=[yaml_from_str, check_yaml_new_npc],
                verbose=self.settings.openai_verbose,
                api_key=self.settings.API_key,
            )

            self.save_npc(new_npc_data)
            new_npc_yaml_path = (
                self.cur_npcs_path
                / new_npc_data["name"]
                / f"npc_tick_{self.cur_world.current_tick}.yaml"
            )

            load_yaml_to_dataclass(new_npc, new_npc_yaml_path)

            debug(
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

    async def new_global_goals(self):
        debug(f"{bcolors.OKCYAN}Generating global goals for NPCs...{bcolors.ENDC}")

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

        self.global_goals = await request_openai(
            model=self.settings.LLM_model,
            prompt=create_global_goals_prompt,
            tries_num=self.settings.llm_request_tries_num,
            response_processors=[yaml_from_str],
            verbose=self.settings.openai_verbose,
            api_key=self.settings.API_key,
        )

        self.save_global_goals()
        debug(f"{bcolors.OKGREEN}Global goals generated successfully{bcolors.ENDC}")

        return

    async def new_npcs_social_connections(self):
        debug(
            f"{bcolors.OKCYAN}Generating social connections between NPCs...{bcolors.ENDC}"
        )
        keys_to_delete = [
            key
            for key in self.npcs[0].__dict__.keys()
            if key not in ["name", "global_goal", "current_state_prompt"]
        ]

        for current_npc in self.npcs:
            if len(self.npcs) < 2:
                current_npc.social_connections = []
                self.save_npc(current_npc)
                break
            other_npcs = []
            for other_npc in self.npcs:
                if current_npc.name == other_npc.name:
                    continue
                npc_dict = dataclass_to_dict_copy(other_npc, keys_to_delete)
                other_npcs.append([npc_dict])

            create_social_connections_prompt = create_social_connections.format(
                world_general_description=self.cur_world.current_state_prompt,
                current_npc_name=current_npc.name,
                current_npc_state=current_npc.current_state_prompt,
                max_npc_social_connections=self.settings.max_npc_social_connections,
                npc_social_connection_yaml_template=load_yaml(
                    YAML_TEMPLATES_PATH / "npc_social_connections.yaml"
                ),
                other_npcs=[
                    yaml.dump(npc, sort_keys=False, Dumper=YamlDumperDoubleQuotes)
                    for npc in other_npcs
                ],
            )

            npc_social_connections = await request_openai(
                model=self.settings.LLM_model,
                prompt=create_social_connections_prompt,
                tries_num=self.settings.llm_request_tries_num,
                response_processors=[yaml_from_str],
                verbose=self.settings.openai_verbose,
                api_key=self.settings.API_key,
            )

            current_npc.social_connections = npc_social_connections
            self.save_npc(current_npc)

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

    def is_in_existing_items(self, existing_items: List | None, item_name: str):
        in_existing_items = False
        if not existing_items:
            debug(
                f"{bcolors.FAIL}No existing {item_name}s found. Create a new {item_name}.{bcolors.ENDC}"
            )

            in_existing_items = False
        else:
            in_existing_items = True

        return in_existing_items

    def print_info_world(self):
        self.print_current_time()

        npc_names = [npc.name for npc in self.npcs]
        debug(
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
            debug(
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

    def current_time_to_str(self):
        current_time = (
            f"{hour_to_iso(self.cur_world.time['current_hour'])}:{minute_to_iso(self.cur_world.time['current_minute'])}:"
            f"{second_to_iso(self.cur_world.time['current_second'])}"
        )

        return current_time

    def current_date_to_str(self):
        current_date = (
            f"{self.cur_world.time['current_day']} {int_to_month(self.cur_world.time['current_month'])},"
            f"{self.cur_world.time['current_year']} {self.cur_world.time['current_era']}. "
        )

        return current_date

    def print_current_time(self):
        current_time = (
            f"{bcolors.OKBLUE}"
            f"Current time:{bcolors.ENDC} {self.current_time_to_str()}, {self.current_date_to_str()}"
        )

        debug(current_time)

        return

    def quit_game(self):
        debug(f"{bcolors.OKCYAN}Quitting game...{bcolors.ENDC}")
        sys.exit(0)


if __name__ == "__main__":
    # with open(YAML_TEMPLATES_PATH / "npc.yaml", "r") as f:
    #     npc_yaml_template = yaml.safe_load(f)

    # t = ["happiness", "health", "hunger", "love", "rested", "stress", "wealth"]

    # for i in t:
    #     npc_yaml_template["attributes"][i] = 0

    # cur_time = to_datetime(2021, 1, 1, 0, 0, 0)
    # debug(cur_time.astype("datetime64[Y]"))
    # time_delta = np.timedelta64(1, "Y")
    # time_delta_d = np.timedelta64(365, "D")

    # debug(type(time_delta.astype("datetime64[Y]").astype(int)))
    # new_time = cur_time + time_delta_d
    # debug(new_time)

    #     t = yaml_from_str(
    #         """
    # npc_new_state: "Ragnar the Warrior spends the day on a successful raid against bandits, showcasing his improved sword fighting skills. However, he suffers from a minor injury, decreasing his health by 1, while also gaining 1 happiness and 2 stress from the adrenaline rush of battle."

    # attributes:
    # health: -1
    # happiness: 1
    # stress: 2"""
    #     )

    #     print(t.get("npc_new_state"))
    settings = Settings()
    settings.load(path="settings.yaml")

    print(settings)
