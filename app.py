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
from pages import (
    PAGE_HOME,
    PAGE_WORLD_CREATE,
    PAGE_WORLD_LOADING,
    PAGE_WORLD_INTERACT,
    generate_npc_tab,
)
from shiny.types import ImgData
from operator import attrgetter


app_ui = ui.page_fluid(
    {"id": "app-content"},
    shinyswatch.theme.sketchy(),
    ui.tags.head(
        ui.div("Test"),
        ui.tags.link(rel="stylesheet", type="text/css", href="css/style.css"),
    ),
    ui.tags.body(
        ui.input_select(
            "page_select",
            "Select page",
            [
                "page_home",
                "page_world_create",
                "page_world_loading",
                "page_world_interact",
            ],
        ),
        ui.navset_hidden(
            ui.nav("Home page", PAGE_HOME, value="page_home"),
            ui.nav("Create a new world", PAGE_WORLD_CREATE, value="page_world_create"),
            ui.nav("Loading page", PAGE_WORLD_LOADING, value="page_world_loading"),
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
    def _():
        ui.update_navs("pages", selected=str(input.page_select()))

    @reactive.Effect
    @reactive.event(input.to_page_world_create)
    def _():
        ui.update_navs("pages", selected="page_world_create")

    @reactive.Effect
    @reactive.event(input.to_page_world_loading)
    async def _():
        game_task = await generate_world()
        ui.update_navs("pages", selected="page_world_loading")

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

    @reactive.Calc
    async def progress_world():
        game_task = await generate_world()
        if game_task.done():
            progress_task = asyncio.create_task(game_task.result().progress_world())
            return game_task

    # @reactive.Effect
    # @reactive.event(input.check_world)
    # async def _():
    #     game_task = await generate_world()
    #     if game_task.done():
    #         npcs = game_task.result().npcs
    #         for npc in reversed(npcs):
    #             npc_value = npc.name.lower().replace(" ", "_")
    #             npc_nav = ui.nav(npc.name, "NPC placeholder NEW", value=npc_value)
    #             ui.nav_insert(
    #                 "world_interact_tabs",
    #                 npc_nav,
    #                 target="npc_placeholder",
    #                 position="after",
    #             )
    #         ui.nav_remove("world_interact_tabs", "npc_placeholder")
    #     else:
    #         reactive.invalidate_later(3)

    @reactive.Effect
    @reactive.event(input.world_progress_button)
    async def _():
        await progress_world()

    @output
    @render.text
    async def loading_world_header_text():
        game_task = await generate_world()
        if game_task.done():
            print("invalidate_done")
            ui.update_navs("pages", selected="page_world_interact")
            npcs = game_task.result().npcs
            for npc in reversed(npcs):
                npc_value, npc_content = generate_npc_tab(npc)
                npc_nav = ui.nav(npc.name, npc_content, value=npc_value)
                ui.nav_insert(
                    "world_interact_tabs",
                    npc_nav,
                    target="npc_placeholder",
                    position="after",
                )
            ui.nav_remove("world_interact_tabs", "npc_placeholder")
        else:
            reactive.invalidate_later(3)
            print("invalidate_loading")
            return "World is initializing..."

    async def get_world_data(attribute):
        game_task = await generate_world()
        if game_task.done():
            game = game_task.result()
            return attrgetter(attribute)(game)
        else:
            reactive.invalidate_later(3)
            return "Loading..."

    @output
    @render.text
    async def world_interact_header():
        return await get_world_data("cur_world.name")

    @output
    @render.text
    async def world_current_state():
        return await get_world_data("cur_world.current_state_prompt")

    @output
    @render.text
    async def world_current_date():
        current_date_to_str_func = await get_world_data("current_date_to_str")
        return current_date_to_str_func()

    @output
    @render.text
    async def world_current_time():
        current_time_to_str_func = await get_world_data("current_time_to_str")
        return current_time_to_str_func()

    @output
    @render.text
    async def world_current_temperature():
        attributes = await get_world_data("cur_world.attributes")
        return attributes["temperature"]

    @output
    @render.text
    async def world_progress_button_text():
        tick_rate = await get_world_data("cur_world.tick_rate")
        tick_type = await get_world_data("cur_world.tick_type")
        return f"Wait {tick_rate} {tick_type}s"

    # @output
    # @render.text
    # async def world_interact_header():
    #     game_task = await generate_world()
    #     if game_task.done():
    #         return game_task.result().cur_world.name
    #     else:
    #         reactive.invalidate_later(3)
    #         return "Loading..."

    # @output
    # @render.text
    # async def world_current_state():
    #     game_task = await generate_world()
    #     if game_task.done():
    #         return game_task.result().cur_world.current_state_prompt
    #     else:
    #         reactive.invalidate_later(3)
    #         return "Loading..."

    # @output
    # @render.text
    # async def world_current_date():
    #     game_task = await generate_world()
    #     if game_task.done():
    #         return game_task.result().current_date_to_str()
    #     else:
    #         reactive.invalidate_later(3)
    #         return "Loading..."

    # @output
    # @render.text
    # async def world_current_time():
    #     game_task = await generate_world()
    #     if game_task.done():
    #         return game_task.result().current_time_to_str()
    #     else:
    #         reactive.invalidate_later(3)
    #         return "Loading..."

    # @output
    # @render.text
    # async def world_current_temperature():
    #     game_task = await generate_world()
    #     if game_task.done():
    #         return game_task.result().cur_world.attributes["temperature"]
    #     else:
    #         reactive.invalidate_later(3)
    #         return "Loading..."


www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
