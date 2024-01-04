from itertools import islice
from pathlib import Path
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
                    ui.output_ui(
                        id="render_world_state",
                    ),
                    class_="field-margin-left",
                ),
                ui.div(
                    "Date",
                    ui.output_ui(
                        id="render_date",
                    ),
                    class_="field-margin-left",
                ),
                ui.div(
                    "Time",
                    ui.output_ui(
                        id="render_time",
                    ),
                    class_="field-margin-left",
                ),
                ui.div(
                    "C°",
                    ui.output_ui(
                        id="render_temperature",
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
                        ui.output_ui(
                            id="render_npc_name",
                        ),
                        class_="field-margin-left",
                    ),
                    ui.div(
                        "State",
                        ui.output_ui(
                            id="render_npc_state",
                        ),
                        class_="field-margin-left",
                    ),
                    ui.div(
                        "Goal",
                        ui.output_ui(
                            id="render_npc_goal",
                        ),
                        class_="field-margin-left",
                    ),
                    ui.div(
                        "Attributes",
                        ui.output_ui(
                            id="render_npc_attributes",
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
def render_world_tab(input: Inputs,
                     output: Outputs,
                     session: Session,
                     img_path: Path,
                     world_state: str,
                     date: str,
                     time: str,
                     temperature: str):
    
    @output(suspend_when_hidden=False)
    @render.image
    def generated_image():
        img: ImgData = {"src": str(img_path), "width": "100%", "style": "float: left;"}
        return img

    @output(suspend_when_hidden=False)
    @render.text
    def render_world_state():
        return ui.input_text_area(
                        id="world_state",
                        label="",
                        value=world_state,
                        width="100%",
                        rows=12,
                        resize="vertical",
                    )

    @output(suspend_when_hidden=False)
    @render.text
    def render_date():
        return ui.pre(
                        date,
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    )

    @output(suspend_when_hidden=False)
    @render.text
    def render_time():
        return ui.pre(
                        time,
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    )

    @output(suspend_when_hidden=False)
    @render.text
    def render_temperature():
        return ui.input_text_area(
                        id="world_temperature",
                        label="",
                        value=temperature,
                        resize="none",
                        width="100%",
                        rows=1,
                    )
    
    return input

@module.server
def render_npc_tab(input: Inputs,
                     output: Outputs,
                     session: Session,
                     img_path: Path,
                     npc_name: str,
                     npc_state: str,
                     npc_goal: str,
                     npc_attributes: str
                     ):
    
    @output(suspend_when_hidden=False)
    @render.image
    def generated_image():
        img: ImgData = {"src": str(img_path), "width": "100%", "style": "float: left;"}
        return img

    @output(suspend_when_hidden=False)
    @render.text
    def render_npc_name():
        return ui.pre(
                        npc_name,
                        class_="shiny-text-output noplaceholder shiny-bound-output text-no-scroll",
                    )

    @output(suspend_when_hidden=False)
    @render.text
    def render_npc_state():
        return ui.input_text_area(
                        id="npc_state",
                        label="",
                        value=npc_state,
                        width="100%",
                        rows=6,
                        resize="vertical",
                    )
    
    @output(suspend_when_hidden=False)
    @render.text
    def render_npc_goal():
        return ui.input_text_area(
                        id="npc_goal",
                        label="",
                        value=npc_goal,
                        width="100%",
                        rows=3,
                        resize="vertical",
                    )
    
    @output(suspend_when_hidden=False)
    @render.text
    def render_npc_attributes():
        attributes = ui.TagList()

        attributes_num = len(npc_attributes)
        attributes_per_column = 3
        attribute_rows_num = attributes_num // attributes_per_column + attributes_num % attributes_per_column
        attributes_slices = [dict(islice(npc_attributes.items(), i, i + attributes_per_column)) for i in range(0, attributes_num, attributes_per_column)]

        for attributes_slice in attributes_slices:
            attributes_row = ui.row()
            attributes_column = ui.column(12 // attribute_rows_num)

            for key, value in attributes_slice.items(): 
                attributes_column = ui.column(12 // attribute_rows_num)
                attributes_column.append(
                    ui.input_text_area(
                        id=key,
                        label=key,
                        value=value,
                        width="100%",
                        rows=1,
                        resize="none",
                    )
                )
                attributes_row.append(attributes_column)

            attributes.append(attributes_row)
        
        return attributes
    
    return input