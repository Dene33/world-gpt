import os
from shiny import App, render, ui, reactive, Inputs, Outputs, Session
from shiny.types import FileInfo
import shinyswatch
from classes import Settings, Game
from pathlib import Path
from utils import ensure_dirs_exist, zip_files, unzip_files, check_openai_api_key
from resources_paths import DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH
import uuid
import asyncio
from pages import (
    PAGE_HOME,
    PAGE_WORLD_CREATE,
    PAGE_WORLD_LOADING,
    PAGE_WORLD_INTERACT,
    PAGE_WORLD_UPDATING,
    PAGE_MISSING_API_KEY
)
from operator import attrgetter
import logging
from ui_modules.generate_tabs import generate_world_tab, generate_npc_tab, image_render
from logging import debug
from dotenv import load_dotenv
from io import StringIO
import aiofiles

logging.basicConfig(level=logging.DEBUG)

# Uncomment to disable logging and comment to enable logging
logging.disable(logging.DEBUG)

www_dir = Path(__file__).parent / "www"

app_ui = ui.page_fluid(
    {"id": "app-content"},
    shinyswatch.theme.sketchy(),
    ui.tags.head(
        ui.tags.link(rel="stylesheet", type="text/css", href="css/style.css"),
        ui.tags.script(src="js/iframeResizer.contentWindow.min.js"),
    ),
    ui.tags.body(
        ui.navset_hidden(
            ui.nav("Home page", PAGE_HOME, value="page_home"),
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
            ui.nav(
                "Missing API key",
                PAGE_MISSING_API_KEY,
                value="page_missing_api_key",
            ),
            id="pages",
        ),
    ),
)


def server(input: Inputs, output: Outputs, session: Session):
    progress_task_val = reactive.Value(None)

    # Check if the API key is valid
    @reactive.Calc
    async def check_api_key() -> bool:
        env_stream = StringIO(f"OPENAI_API_KEY={input.API_key()}")
        load_dotenv(stream=env_stream, override=True)

        if Path("openai_key").exists() and not input.API_key():
            load_dotenv("openai_key", override=True)

        api_key_valid = check_openai_api_key(str(os.environ.get("OPENAI_API_KEY")))

        return api_key_valid
    
    # Render warning message if the API key is invalid
    @output
    @render.ui
    async def missing_api_key():
        api_key_valid = await check_api_key()

        if not api_key_valid:
            return PAGE_MISSING_API_KEY
    
    # Render the "Create new world" button if the API key is valid
    @output
    @render.ui
    async def new_world_button():
        api_key_valid = await check_api_key()

        if api_key_valid:
            return ui.input_action_button(
                        "to_page_world_create",
                        "Create new world",
                    )

    # Render the "Upload world" button if the API key is valid
    @output
    @render.ui
    async def upload_existing_world():
        api_key_valid = await check_api_key()

        if api_key_valid:
            return ui.input_file(
                        label="",
                        id="upload_world",
                        button_label="Upload your world",
                        accept=[".zip"],
                    )

    # Process the uploaded world, unzip it and return the path to the unzipped folder
    @reactive.Calc
    async def get_uploaded_filepath() -> Path | None:
        debug("World upload")
        file: list[FileInfo] | None = input.upload_world()

        if file:
            uploaded_file_path = Path(file[0]["datapath"])
            unzip_path = Path("data") / "games"
            unzip_path_extracted = await unzip_files(uploaded_file_path, unzip_path)

            return unzip_path_extracted


    @session.download(filename="story_generator_world.zip")
    async def download_world():
        game_task = await generate_world()
        if game_task.done():
            game = game_task.result()
            zip_path = Path("data") / f'{game.cur_world.name}.zip'
            zipped_file = await zip_files(game.game_path, zip_path)

            async with aiofiles.open(zip_path, 'rb') as f:
                data = await f.read()
                yield data
            
            zip_path.unlink()

    # Switch to the world creation page
    @reactive.Effect
    @reactive.event(input.to_page_world_create)
    async def _():
        ui.update_navs("pages", selected="page_world_create")

    # Switch page to page_world_loading for the time of the world generation or world upload
    @reactive.Effect
    @reactive.event(input.to_page_world_loading, input.upload_world)
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
        
        unziped_game_path = await get_uploaded_filepath()

        if unziped_game_path:
            settings = Settings()
            settings.load(path=unziped_game_path / "settings.yaml")

            game = Game()
            game.game_name = unziped_game_path.stem
            game.settings = settings
            game.load_game()

            game_task = asyncio.create_task(game.init_world())

            return game_task
        else:
            settings = Settings()
            settings.load(path="./settings.yaml")

            game = Game()
            game.new_game(game_name=str(uuid.uuid4()))
            game.settings = settings

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
            world_uuid = uuid.uuid4().hex

            img_url = game.cur_world_path / f"world_tick_{game.cur_world.current_tick}.jpg"

            if not game.settings.text_to_image_generate_world or not img_url.exists():
                img_url = www_dir / "img/img_placeholder.png"
            image_render(world_uuid, img_url)
            world_nav = generate_world_tab(world_uuid, game, "world_nav")
            ui.nav_insert(
                "world_interact_tabs",
                world_nav,
                target="npcs_nav_menu",
                position="before",
            )

            ui.nav_hide("world_interact_tabs", "npc_placeholder")
            npcs = game.npcs
            for i, npc in enumerate(reversed(npcs)):
                npc_uuid = uuid.uuid4().hex

                img_url = game.cur_world_path / f"npcs/{npc.name}/npc_tick_{game.cur_world.current_tick}.jpg"

                if not game.settings.text_to_image_generate_npcs or not img_url.exists():
                    img_url = www_dir / "img/img_placeholder.png"

                image_render(npc_uuid, img_url)
                npc_nav = generate_npc_tab(npc_uuid, npc, npc.name.lower().replace(" ", "_"))
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
            world_uuid = uuid.uuid4().hex

            img_url = game.cur_world_path / f"world_tick_{game.cur_world.current_tick}.jpg"

            if not game.settings.text_to_image_generate_world or not img_url.exists():
                img_url = www_dir / "img/img_placeholder.png"

            image_render(world_uuid, img_url)
            world_nav = generate_world_tab(world_uuid, game, "world_nav")
            ui.nav_remove("world_interact_tabs", "world_nav")
            ui.nav_insert(
                "world_interact_tabs",
                world_nav,
                target="npcs_nav_menu",
                position="before",
            )
            
            npcs = game.npcs
            for i, npc in enumerate(reversed(npcs)):
                npc_uuid = uuid.uuid4().hex

                img_url = game.cur_world_path / f"npcs/{npc.name}/npc_tick_{game.cur_world.current_tick}.jpg"

                if not game.settings.text_to_image_generate_npcs or not img_url.exists():
                    img_url = www_dir / "img/img_placeholder.png"

                image_render(npc_uuid, img_url)
                npc_nav = generate_npc_tab(npc_uuid, npc, npc.name.lower().replace(" ", "_"))

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


app = App(app_ui, server, static_assets=www_dir)
