from shiny import App, render, ui, reactive
import shinyswatch

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
                class_="btn-primary main-page-button main-page-load-world",
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
            rows=8,
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
            "to_page_world_interact",
            "Create new world",
            width="100%",
        ),
        class_="main-page-container col-lg-7 col-md-8 col-sm-10 col-12 mx-auto",
    )
)

PAGE_WORLD_INTERACT = ui.TagList(
    ui.div(
        ui.p("Initialized world"),
        ui.output_text_verbatim("global_goals"),
        ui.input_action_button(
            "check_world",
            "Check world",
            width="100%",
        ),
    )
)
