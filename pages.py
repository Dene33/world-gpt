from shiny import App, render, ui, reactive
import shinyswatch
from classes import Npc, Game

PAGE_HOME = ui.TagList(
    ui.div(
        {"id": "page-0-content"},
        ui.h1("WorldGPT"),
        ui.div(
            ui.div(
                ui.p(
                    "WorldGPT is a groundbreaking app that brings your imagination to life. \
            Input your world description, and watch as an entire universe unfolds before your eyes. \
            With ChatGPT as the backbone, witness the progression of your world and observe \
            lifelike NPCs as they navigate its intricacies. Experience the joy of creation \
            in real-time, all within the palm of your hand."
                ),
                class_="text-panel well",
            ),
            ui.input_action_button(
                "to_page_world_create",
                "Create a new world",
                class_="btn-primary main-page-button",
            ),
            ui.input_action_button(
                "load_existing_world",
                "Load existing world",
                class_="btn-primary main-page-button main-page-load-world disabled",
            ),
            ui.output_text_verbatim("main"),
            class_="main-page-container col-lg-7 col-md-8 col-sm-10 col-12 mx-auto",
        ),
    ),
)

PAGE_WORLD_CREATE = ui.TagList(
    ui.div(
        {"id": "create-world-content"},
        ui.h1("Create a new world"),
        ui.input_password(
            "API_key",
            "OpenAI key",
            placeholder="Provide your OpenAI key. Optional",
            value="",
            width="100%",
        ),
        ui.input_text(
            "new_world_name",
            "World name",
            placeholder="World name",
            value="My world",
            width="100%",
        ),
        ui.input_text_area(
            "new_world_description",
            "World description",
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
        ui.row(
            {"id": "create-world-settings"},
            ui.input_numeric(
                "new_world_tick_rate", "Tick Rate", min=1, value=1, width="25%"
            ),
            ui.input_select(
                "new_world_tick_type",
                "Tick type",
                ["day", "year", "hour", "minute", "second"],
                width="25%",
            ),
            ui.input_select(
                "new_world_npc_num",
                "# NPCs",
                [*range(1, 16)],
                selected=5,
                width="25%",
            ),
            ui.input_numeric(
                "new_world_temperature",
                "t (°C)",
                value=18,
                width="25%",
            ),
        ),
        ui.row(
            {"id": "create-world-datetime"},
            ui.input_numeric("new_world_year", "Year", value=1000, width="25%"),
            ui.input_select(
                "new_world_era",
                "Era",
                ["AD", "BC"],
                width="25%",
            ),
            ui.input_select(
                "new_world_day",
                "Day",
                [*range(1, 32)],
                width="25%",
            ),
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
        ),
        ui.row(
            ui.input_select(
                "new_world_hour", "Hour", [*range(0, 24)], selected=12, width="33.3%"
            ),
            ui.input_select(
                "new_world_minute", "Minute", [*range(0, 60)], selected=0, width="33.3%"
            ),
            ui.input_select(
                "new_world_second", "Second", [*range(0, 60)], selected=0, width="33.3%"
            ),
        ),
        ui.input_action_button(
            "to_page_world_loading",
            "Create new world",
            width="100%",
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
        ),
        ui.input_action_button(
            "to_page_world_updating",
            ui.output_text("world_progress_button_text"),
            width="100%",
        ),
        # ui.input_action_button(
        #     "change_state",
        #     "Change state",
        #     width="100%",
        # ),
        class_="main-page-container col-lg-9 col-md-12 col-sm-12 col-12 mx-auto",
    )
)


def generate_world_tab(game: Game):
    world_content = ui.TagList(
        ui.div(
            "World state",
            ui.pre(
                game.cur_world.current_state_prompt,
                class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
            ),
        ),
        ui.row(
            ui.column(
                6,
                ui.div(
                    "Date",
                    ui.pre(
                        game.current_date_to_str(),
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    ),
                ),
            ),
            ui.column(
                4,
                ui.div(
                    "Time",
                    ui.pre(
                        game.current_time_to_str(),
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    ),
                ),
            ),
            ui.column(
                2,
                ui.div(
                    "C°",
                    ui.pre(
                        game.cur_world.attributes["temperature"],
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    ),
                ),
            ),
        ),
    )

    world_tab = ui.nav("World", world_content, value="world_nav")

    return world_tab


def generate_npc_tab(npc: Npc):
    npc_value = npc.name.lower().replace(" ", "_")
    npc_content = ui.TagList(
        ui.div(
            {"id": f"npc-content-{npc_value}"},
            ui.div(
                "Name",
                ui.pre(
                    npc.name,
                    class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                ),
            ),
            ui.div(
                "State",
                ui.pre(
                    npc.current_state_prompt,
                    class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                ),
            ),
            ui.row(
                ui.column(
                    6,
                    ui.div(
                        "Goal",
                        ui.pre(
                            npc.global_goal,
                            class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                        ),
                    ),
                ),
                ui.column(
                    6,
                    ui.div(
                        "Attributes",
                        ui.pre(
                            str(npc.attributes)[1:-1].replace(", ", ",\n"),
                            class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll npc-attributes",
                        ),
                    ),
                ),
            ),
        )
    )

    npc_tab = ui.nav(npc.name, npc_content, value=npc_value)
    return npc_tab
