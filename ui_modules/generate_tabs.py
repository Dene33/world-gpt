from shiny import App, Inputs, Outputs, Session, module, render, ui
from shiny.types import ImgData
from classes import Npc, Game


@module.ui
def generate_world_tab(game: Game, nav_value: str):
    world_content = ui.TagList(
        ui.row(
            ui.column(
                6,
                ui.output_image(
                    id="generated_image",
                ),
            ),
            ui.column(
                6,
                ui.div(
                    "World state",
                    ui.pre(
                        game.cur_world.current_state_prompt,
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    ),
                    class_="field-margin-left",
                ),
                ui.div(
                    "Date",
                    ui.pre(
                        game.current_date_to_str(),
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    ),
                    class_="field-margin-left",
                ),
                ui.div(
                    "Time",
                    ui.pre(
                        game.current_time_to_str(),
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    ),
                    class_="field-margin-left",
                ),
                ui.div(
                    "C°",
                    ui.pre(
                        game.cur_world.attributes["temperature"],
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    ),
                    class_="field-margin-left",
                ),
            ),
        ),
    )

    world_tab = ui.nav("World", world_content, value=nav_value)

    return world_tab

@module.ui
def generate_npc_tab(npc: Npc, nav_value: str):
    # npc_value = npc.name.lower().replace(" ", "_")
    npc_content = ui.TagList(
        ui.div(
            {"id": f"npc-content-{nav_value}"},
            ui.row(
                ui.column(
                    6,
                    ui.output_image(
                        id="generated_image",
                    ),
                ),
                ui.column(
                    6,
                    ui.div(
                        "Name",
                        ui.pre(
                            npc.name,
                            class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                        ),
                        class_="field-margin-left",
                    ),
                    ui.div(
                        "State",
                        ui.pre(
                            npc.current_state_prompt,
                            class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                        ),
                        class_="field-margin-left",
                    ),
                    ui.div(
                        "Goal",
                        ui.pre(
                            npc.global_goal,
                            class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                        ),
                        class_="field-margin-left",
                    ),
                    ui.div(
                        "Attributes",
                        ui.pre(
                            str(npc.attributes)[1:-1].replace(", ", ",\n"),
                            class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll npc-attributes",
                        ),
                        class_="field-margin-left",
                    ),
                ),
            ),
        )
    )

    npc_tab = ui.nav(npc.name, npc_content, value=nav_value)
    return npc_tab

@module.server
def image_render(input: Inputs, output: Outputs, session: Session, img_path):
    @output
    @render.image
    def generated_image():
        img: ImgData = {"src": str(img_path), "width": "100%", "style": "float: left;"}
        return img
