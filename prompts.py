from string import Template
from langchain import PromptTemplate
from langchain.prompts import load_prompt
from utils import (
    request_openai,
    yaml_from_str,
    save_yaml_from_data,
    populate_dataclass_with_dicts,
)
import openai
from prompt_toolkit import prompt
import yaml


new_world_state_request = Template(
    """$tick_rate ${tick_type}s have passed. Describe only the new world state and the world's temperature. \
If something's changed in the world or there was some event(s), please describe them. Output it as a python string \
assigned to `world_state` var in the code block and int `temperature` var in the same code block. No matter what \
- DON'T output any comments, NPC's changes, notes and additional descriptions.
"""
)

new_npc_state_request = Template(
    """Here is the NPC:
$npc_prompt
Describe ${npc_name}'s state. \
Output it as a python string assigned to `current_state_prompt` var in the code block.
In the same code block, output the NPC's change attributes (delta) as a python list assigned to `attributes` var. \
If the attribute is not changed, output 0 for it. \
If the attribute is increased, output a positive number for it. \
If the attribute is decreased, output a negative number for it. \
NPCs can interact with each other and with the world. NPCs are usually awake during the day. \
And they usually sleep at night. Take this into account in `current_state_prompt` \
No matter what - DON'T output any comments, NPC's changes, notes, additional descriptions and explanations.
"""
)

# World
world_init_state = load_prompt("data/prompts/world/init_state.yaml")
world_current_state = load_prompt("data/prompts/world/current_state.yaml")
world_previous_state = load_prompt("data/prompts/world/previous_state.yaml")
world_parameters = load_prompt("data/prompts/world/parameters.yaml")
world_new_state_request = load_prompt("data/prompts/world/new_state_request.yaml")
create_global_goals = load_prompt("data/prompts/npc/create_global_goals.yaml")

# NPC
create_npc_request = load_prompt("data/prompts/npc/create_npc_request.yaml")


if __name__ == "__main__":
    from classes import World, Npc, Settings

    openai.api_key = prompt("Provide OpenAI API key: ", is_password=True)

    settings = Settings()
    settings.load(path="./settings.yaml")
    from utils import (
        load_yaml_to_dataclass,
        hour_to_pm_am,
        hour_to_daytime,
        dataclass_to_dict,
        int_to_month,
        hour_to_iso,
        minute_to_iso,
        second_to_iso,
        YamlDumperDoubleQuotes,
    )
    from resources_paths import *

    world = World()
    load_yaml_to_dataclass(
        world,
        "/mnt/Shared/Demania/repos/world-gpt/data/games/Test Game/worlds/Test_World/world_tick_0.yaml",
    )

    npc_0 = Npc()
    npc_1 = Npc()

    npcs = [npc_0, npc_1]

    with open(YAML_TEMPLATES_PATH / "npc.yaml", "r") as f:
        npc_yaml_template = yaml.safe_load(f)

    for attribute in settings.npc_attributes_names:
        npc_yaml_template["attributes"][attribute] = 0

    populate_dataclass_with_dicts(npc_0, [settings.npc_attributes_names])

    create_npc_request = create_npc_request.format(
        world_general_description=world.current_state_prompt,
        world_current_attributes=world.attributes,
        npc_yaml_template=yaml.dump(
            npc_0, sort_keys=False, Dumper=YamlDumperDoubleQuotes
        ),
        global_goal="Learn the art of magic and become the village's resident wizard.",
    )
    print(create_npc_request)
