from shiny import App, render, ui, reactive
import shinyswatch
from classes import Npc, Game
from utils import add_tooltip, img_to_base64str

PAGE_HOME = ui.TagList(
    ui.div(
        {"id": "page-0-content"},
        # ui.h1("Try it for free"),
        add_tooltip(
            ui.input_password(
                "API_key",
                "OpenAI key",
                placeholder="Provide your OpenAI key. Now it's GPT4 + Dall-e 3 so the free version is limited to N requests per month",
                value="",
                width="100%",
            ),
            "Your OpenAI API key. Optional",
        ),
        ui.output_ui(id="missing_api_key"),
        ui.row(
            ui.column(
                6,
                ui.output_ui(id="new_world_button"),
                style_="margin-top: 40px;",
            ),
            ui.column(
                6,
                ui.output_ui(id="upload_existing_world"),
                style_="margin-top: 40px;",
            ),
        ),
        class_="main-page-container col-lg-7 col-md-8 col-sm-10 col-12 mx-auto",
    ),
)

PAGE_WORLD_CREATE = ui.TagList(
    ui.div(
        {"id": "create-world-content"},
        ui.h1("Try it for free"),
        add_tooltip(
            ui.input_text(
                "new_world_name",
                "World name",
                placeholder="World name",
                value="My world",
                width="100%",
            ),
            "The name of your world",
        ),
        add_tooltip(
            ui.input_text_area(
                "new_world_description",
                "Input your world description",
                value="A mid-sized village situated by the river in medieval Moldova. \
It has a self-sufficient community surrounded by a wooden palisade. There is a market \
square, a church, and fields for growing crops and grazing livestock. The villagers \
are engaged in crafts, and in times of war or danger, they rely on a small militia \
from nearby castle.",
                placeholder="World description",
                width="100%",
                rows=6,
                resize="none",
            ),
            "The prompt for ChatGPT to generate the world",
        ),
        ui.h4("General settings", style_="text-align: center; width: 100%;"),
        ui.row(
            {"id": "create-world-settings"},
            ui.column(
                3,
                add_tooltip(
                    ui.input_select(
                        "new_world_npc_num",
                        "# NPCs",
                        [*range(1, 16)],
                        selected=2,
                        width="80%",
                    ),
                    "The number of NPCs in the world",
                ),
            ),
            ui.column(
                3,
                add_tooltip(
                    ui.input_numeric(
                        "new_world_temperature",
                        "t (°C)",
                        value=0,
                        width="80%",
                    ),
                    "The initial temperature of the world",
                ),
            ),
            ui.column(
                6,
                add_tooltip(
                    ui.input_checkbox_group(
                        "images_to_generate",
                        "Choose type of images to generate:",
                        {
                            "text_to_image_generate_world": ui.span("World"),
                            "text_to_image_generate_npcs": ui.span("Npcs"),
                        },
                        selected=[
                            "text_to_image_generate_world",
                            "text_to_image_generate_npcs",
                        ],
                        # width="33.3%"
                    ),
                    "Choose type of images to generate. It will take more time to generate the result",
                ),
            ),
            class_="text-panel",
            style_="border-radius: 5px 5px 5px 5px/25px 25px 25px 5px;"
        ),
        ui.h4("Time settings", style_="text-align: center; width: 100%; margin-top: 1rem;"),
        ui.div(
            ui.row(
                {"id": "create-world-datetime"},
                add_tooltip(
                    ui.input_numeric("new_world_year", "Year", value=1000, width="25%"),
                    "The initial year of the world",
                ),
                add_tooltip(
                    ui.input_select(
                        "new_world_era",
                        "Era",
                        ["AD", "BC"],
                        width="25%",
                    ),
                    "The initial era of the world",
                ),
                add_tooltip(
                    ui.input_select(
                        "new_world_day",
                        "Day",
                        [*range(1, 32)],
                        width="25%",
                    ),
                    "The initial day of the world",
                ),
                add_tooltip(
                    ui.input_select(
                        "new_world_month",
                        "Month",
                        {
                            "1": "January",
                            "2": "February",
                            "3": "March",
                            "4": "April",
                            "5": "May",
                            "6": "June",
                            "7": "July",
                            "8": "August",
                            "9": "September",
                            "10": "October",
                            "11": "November",
                            "12": "December",
                        },
                        width="25%",
                    ),
                    "The initial month of the world",
                ),
            ),
            ui.row(
                add_tooltip(
                    ui.input_select(
                        "new_world_hour",
                        "Hour",
                        [*range(0, 24)],
                        selected=12,
                        width="33.3%",
                    ),
                    "The initial hour of the world",
                ),
                add_tooltip(
                    ui.input_select(
                        "new_world_minute",
                        "Minute",
                        [*range(0, 60)],
                        selected=0,
                        width="33.3%",
                    ),
                    "The initial minute of the world",
                ),
                add_tooltip(
                    ui.input_select(
                        "new_world_second",
                        "Second",
                        [*range(0, 60)],
                        selected=0,
                        width="33.3%",
                    ),
                    "The initial second of the world",
                ),
            ),
            class_="text-panel",
            style_="border-radius: 5px 5px 5px 5px/25px 25px 25px 5px;"
        ),
        ui.div(
            ui.input_action_button(
                "to_page_world_loading",
                "Create new world",
                width="100%",
                style_="margin-top: 1rem;"
            ),
        ),
        ui.tags.script(
            """
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        """
        ),
        class_="main-page-container main-page-container col-lg-9 col-md-10 col-sm-12 col-12 mx-auto",
    )
)

PAGE_WORLD_LOADING = ui.TagList(
    ui.div(
        {"id": "loading-world-content"},
        ui.row(
            ui.h1(
                ui.output_text("loading_world_header_text"),
                class_="loading_world_header",
            ),
            ui.img(
                id="loading_world_image",
                src="img/loading.svg",
                class_="loading_world_image",
            ),
            ui.div(
                ui.span(
                    "The process of generating the world relies on ChatGPT. It typically takes between 1 to 3 minutes to complete, and the time it takes depends on the number of NPCs",
                ),
                style_="margin-top: 40px;",
            ),
        ),
        class_="main-page-container col-lg-7 col-md-8 col-sm-10 col-12 mx-auto",
    )
)

PAGE_WORLD_UPDATING = ui.TagList(
    ui.div(
        {"id": "updating-world-content"},
        ui.row(
            ui.h1(
                ui.output_text("updating_world_header_text"),
                class_="updating_world_header",
            ),
            ui.img(
                id="loading_world_image",
                src="img/loading.svg",
                class_="loading_world_image",
            ),
            ui.div(
                ui.span(
                    "The process of updating the world relies on ChatGPT. It typically takes between 1 to 2 minutes to complete, and the time it takes depends on the number of NPCs",
                ),
                style_="margin-top: 40px;",
            ),
        ),
        class_="main-page-container col-lg-7 col-md-8 col-sm-10 col-12 mx-auto",
    )
)

PAGE_WORLD_INTERACT = ui.TagList(
    ui.div(
        {"id": "interact-world-content"},
        ui.h1(ui.output_text("world_interact_header")),
        ui.navset_tab_card(
            ui.nav_menu(
                "NPCs",
                ui.nav(
                    f"NPC placeholder",
                    "NPC placeholder",
                    value=f"npc_placeholder",
                ),
                value="npcs_nav_menu",
            ),
            id="world_interact_tabs",
            footer=ui.download_button("download_world", "Save the world", style_="margin-top: 1rem;")
        ),
        ui.row(
            ui.column(
                3,
                    ui.output_ui(id="world_tick_rate_input", style_="margin-top: 12px; width: 90%;"),
            ),
            ui.column(
                3,
                    ui.output_ui(id="world_tick_type_input", style_="margin-top: 12px; width: 90%;"),
            ),
            ui.column(
                6,
                ui.input_action_button(
                    "to_page_world_updating",
                    ui.output_text("world_progress_button_text"),
                    width="100%",
                    style_="height: 80%;",
                ),
            ),
        ),
        
        class_="main-page-container col-lg-9 col-md-12 col-sm-12 col-12 mx-auto",
    )
)

PAGE_MISSING_API_KEY = ui.TagList(
    ui.div(
        {"id": "page-0-content"},
        ui.h1("API key is missing!"),
        ui.div(
            ui.div(
                ui.p(
                    'OpenAI API key is missing. Please provide it to be able to generate the world.'
                ),
                ui.a(
                    "Get your OpenAI API key here",
                    href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-api-key",
                    style_="color: #fff;",
                    target="_blank",
                ),
                class_="text-panel well",
            ),
            class_="main-page-container col-lg-12 col-md-12 col-sm-12 col-12 mx-auto",
        ),
    ),
)