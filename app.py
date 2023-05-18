from shiny import App, render, ui, reactive
import shinyswatch
from classes import Settings, Game
from pathlib import Path
from utils import Input, ensure_dirs_exist, request_openai
from resources_paths import DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH
import uuid
import openai
import asyncio
import time
from pages import PAGE_HOME, PAGE_WORLD_CREATE, PAGE_WORLD_INTERACT


app_ui = ui.page_fluid(
    {"id": "app-content"},
    shinyswatch.theme.sketchy(),
    ui.tags.head(ui.tags.link(rel="stylesheet", type="text/css", href="css/style.css")),
    ui.tags.body(
        ui.navset_hidden(
            ui.nav("Home page", PAGE_HOME, value="page_home"),
            ui.nav("Create a new world", PAGE_WORLD_CREATE, value="page_world_create"),
            ui.nav(
                "Interact with the world",
                PAGE_WORLD_INTERACT,
                value="page_world_interact",
            ),
            id="pages",
        ),
    ),
)


def server(input, output, session):
    @reactive.Effect
    @reactive.event(input.to_page_world_create)
    def _():
        ui.update_navs("pages", selected="page_world_create")

    @reactive.Effect
    @reactive.event(input.to_page_world_interact)
    async def _():
        game_task = await generate_world()
        ui.update_navs("pages", selected="page_world_interact")

    @reactive.Calc
    async def generate_world():
        ensure_dirs_exist(
            [DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH]
        )
        settings = Settings()
        settings.load(path="./settings.yaml")

        game = Game()
        game.new_game(game_name=str(uuid.uuid4()))

        world_data = {
            "name": input.new_world_name(),
            "attributes": {"temperature": input.new_world_temperature()},
            "time": {
                "current_day": int(input.new_world_day()),
                "current_month": int(input.new_world_month()),
                "current_year": int(input.new_world_year()),
                "current_era": str(input.new_world_era()),
                "current_hour": int(input.new_world_hour()),
                "current_minute": int(input.new_world_minute()),
                "current_second": int(input.new_world_second()),
            },
            "tick_type": input.new_world_tick_type(),
            "tick_rate": input.new_world_tick_rate(),
            "current_state_prompt": input.new_world_description(),
        }
        settings_data = {
            "API_key": input.API_key(),
            "number_of_npcs": int(input.new_world_npc_num()),
        }

        openai.api_key = input.API_key()
        game.settings_from_ui(settings_data)

        game_task = asyncio.create_task(game.init_world(world_data))

        return game_task

    @reactive.Effect
    @reactive.event(input.check_world)
    async def _():
        ui.update_navs("pages", selected="page_world_interact")
        print("check_world")
        game_task = await generate_world()
        if game_task.done():
            game = game_task.result()
            print(game.__dict__)
            print(game.cur_world)

    @output
    @render.text
    async def global_goals():
        game_task = await generate_world()
        if game_task.done():
            print("invalidate_done")
            return game_task.result().global_goals
        else:
            reactive.invalidate_later(3)
            print("invalidate_loading")
            return "Loading..."


www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
