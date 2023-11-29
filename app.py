import os
from shiny import App, render, ui, reactive
import shinyswatch
from classes import Settings, Game
from pathlib import Path
from utils import Input, ensure_dirs_exist, request_openai  # , debug
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
    PAGE_WORLD_UPDATING,
    generate_world_tab,
    generate_npc_tab,
)
from shiny.types import ImgData
from operator import attrgetter
import random
from copy import copy, deepcopy
import logging

from logging import debug
from dotenv import load_dotenv


logging.basicConfig(level=logging.DEBUG)

# Uncomment to disable logging and comment to enable logging
logging.disable(logging.DEBUG)

app_ui = ui.page_fluid(
    {"id": "app-content"},
    shinyswatch.theme.sketchy(),
    ui.tags.head(
        ui.tags.link(rel="stylesheet", type="text/css", href="css/style.css"),
        ui.tags.script(src="js/iframeResizer.contentWindow.min.js"),
    ),
    ui.tags.body(
        ui.navset_hidden(
            # ui.nav("Home page", PAGE_HOME, value="page_home"),
            ui.nav("Create a new world", PAGE_WORLD_CREATE, value="page_world_create"),
            ui.nav("Loading page", PAGE_WORLD_LOADING, value="page_world_loading"),
            ui.nav(
                "Interact with the world",
                PAGE_WORLD_INTERACT,
                value="page_world_interact",
            ),
            ui.nav(
                "Updating page",
                PAGE_WORLD_UPDATING,
                value="page_world_updating",
            ),
            id="pages",
        ),
    ),
)


def server(input, output, session):
    progress_task_val = reactive.Value(None)

    # Switch page to page_world_loading for the time of the world generation
    @reactive.Effect
    @reactive.event(input.to_page_world_loading)
    async def _():
        # World generation running in the background
        game_task = await generate_world()

        # Switch to page_world_loading with a spinning loading icon while the world is generating
        ui.update_navs("pages", selected="page_world_loading")

    # Asyncronously generate a new world
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

        api_key = input.API_key()
        if not api_key:
            load_dotenv("openai_key")
            api_key = os.environ.get("OPENAI_API_KEY")

        settings_data = {
            "API_key": api_key,
            "number_of_npcs": int(input.new_world_npc_num()),
        }

        if "text_to_image_generate_world" in input.images_to_generate():
            game.settings.text_to_image_generate_world = True
        else:
            game.settings.text_to_image_generate_world = False

        if "text_to_image_generate_npcs" in input.images_to_generate():
            game.settings.text_to_image_generate_npcs = True
        else:
            game.settings.text_to_image_generate_npcs = False

        # openai.api_key = input.API_key()
        game.settings_from_ui(settings_data)

        game_task = asyncio.create_task(game.init_world(world_data))

        return game_task

    # Every 3 seconds check if @reactive.Calc function `generate_world` is finished.
    # If not, continue checking every 3 seconds.
    # If it is finished, update the UI and switch to page_world_interact
    @output
    @render.text
    async def loading_world_header_text():
        game_task = await generate_world()
        if game_task.done():
            debug("invalidate_done")
            ui.update_navs("pages", selected="page_world_interact")
            game = game_task.result()
            world_nav = generate_world_tab(game)
            ui.nav_insert(
                "world_interact_tabs",
                world_nav,
                target="npcs_nav_menu",
                position="before",
            )

            ui.nav_hide("world_interact_tabs", "npc_placeholder")
            npcs = game.npcs
            for npc in reversed(npcs):
                npc_nav = generate_npc_tab(npc)
                # npc_nav = ui.nav(npc.name, npc_content, value=npc_value)
                ui.nav_insert(
                    "world_interact_tabs",
                    npc_nav,
                    target="npc_placeholder",
                    position="after",
                )
            # ui.nav_remove("world_interact_tabs", "npc_placeholder")
            ui.update_navs("world_interact_tabs", selected="world_nav")
        else:
            reactive.invalidate_later(3)
            debug("invalidate_loading")
            return "World is initializing..."

    # Display the world name in the header through async def get_world_data(attribute)
    @output
    @render.text
    async def world_interact_header():
        return await get_world_data("cur_world.name")
    
    # Get any world data attribute when the @reactive.Calc function `generate_world` is finished
    async def get_world_data(attribute):
        game_task = await generate_world()
        if game_task.done():
            game = game_task.result()
            return attrgetter(attribute)(game)
        else:
            reactive.invalidate_later(3)
            return "Loading..."

    # Display the World's tick rate and tick type in the button text
    @output
    @render.text
    async def world_progress_button_text():
        tick_rate = await get_world_data("cur_world.tick_rate")
        tick_type = await get_world_data("cur_world.tick_type")
        return f"Wait {tick_rate} {tick_type}s"

    # Assign async task spawned with `async def progress_world(game: Game)` to Reactive.Value `progress_task_val`
    # Switch to page_world_updating with a spinning loading icon while the world is updating
    @reactive.Effect
    @reactive.event(input.to_page_world_updating)
    async def _():
        debug("Update the world")
        game_task = await generate_world()
        game = game_task.result()

        # Set Reactive.Value `progress_task_val` to the result (async task) of `progress_world` function
        progress_task = progress_task_val.set(await progress_world(game))
        debug("to_page_world_updating", progress_task)

        # Switch to page_world_updating with a spinning loading icon while the world is updating
        ui.update_navs("pages", selected="page_world_updating")

    # Spawn the world update async task in the background
    async def progress_world(game: Game):
        progress_task = asyncio.create_task(game.progress_world())
        debug("calc progress task", progress_task)
        return progress_task

    # Every 3 seconds check if the game.progress_world() task stored in Reactive.Value `progress_task_val` is finished.
    # If not, continue checking every 3 seconds.
    # If it is finished, update the UI and switch to page_world_interact
    @output
    @render.text
    # @reactive.Calc
    async def updating_world_header_text():
        debug("updating_world_header_text")
        progress_task = progress_task_val.get()
        if progress_task.done():
            debug("invalidate_done")
            game = progress_task.result()
            progress_task = None
            ui.update_navs("pages", selected="page_world_interact")
            world_nav = generate_world_tab(game)
            ui.nav_remove("world_interact_tabs", "world_nav")
            ui.nav_insert(
                "world_interact_tabs",
                world_nav,
                target="npcs_nav_menu",
                position="before",
            )
            npcs = game.npcs
            for npc in reversed(npcs):
                npc_nav = generate_npc_tab(npc)

                ui.nav_remove("world_interact_tabs", npc.name.lower().replace(" ", "_"))
                ui.nav_insert(
                    "world_interact_tabs",
                    npc_nav,
                    target="npc_placeholder",
                    position="after",
                )

            ui.update_navs("world_interact_tabs", selected="world_nav")

            return "World is updated"
        else:
            reactive.invalidate_later(3)
            debug("invalidate_loading")
            return "Updating the world..."


www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
