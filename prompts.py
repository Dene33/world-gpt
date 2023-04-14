from string import Template
# WORLD_BEGINNING = "Here is the world: "

#Example
# """Here is the world: A mid-sized village situated by the river in medieval Moldova. \
# It has a self-sufficient community surrounded by a wooden palisade. There is a market square, \
# a church, and fields for growing crops and grazing livestock. The villagers are engaged in crafts, \
# and in times of war or danger, they rely on a small militia from nearby castle.

# Temperature outside is -5C
# Current date is 2 February 1000 AD
# Current time is 12:01:00 PM, noon

# Create 3 NPCs for this world. Parse it to a .yaml files of the structure described below. \
# Replace zeros and empty values with NPC's parameters. Each parameter can't be less than 0 and more than 10. \
# Output only the constructed .yamls as individual code blocks without describing them. Do not output anything else.

# name: ''
# global_goal: ''
# happiness: 0
# love: 0
# health: 0
# rested: 0
# wealth: 0
# hunger: 0
# stress: 0
# current_state_prompt: ''
# NPCs are usually awake during the day. And they usually sleep at night. Take this into account in `current_state_prompt`."""

create_world = Template("""Here is the world: $world_state_prompt

Temperature outside is $temperature
Current date is $day $month $year $era
Current time is $hour:$minute:$second $pm_am, $daytime""")

create_npcs = Template("""Here is the world: $world_prompt

Temperature outside is $temperature
Current date is $day $month $year $era
Current time is $hour:$minute:$second $pm_am, $daytime

Create $num_npcs NPCs for this world. Parse it to a .yaml files of the structure described below. \
Replace zeros and empty values with NPC's parameters. Each parameter can't be less than 0 and more than 10. \
Output only the constructed .yamls as individual code blocks without describing them. Do not output anything else.

$npc_yaml_template

NPCs are usually awake during the day. And they usually sleep at night. Take this into account in `current_state_prompt`.""")
                              
# create_world = Template("""Here is the world: $world_prompt""")



#TODO paraphrase for better English
create_global_goals = Template("""Here is the world: $world_prompt

NPCs have the following attributes: happiness, love, health, rested, wealth, hunger, stress

Create $num_global_goals random `global_goals` that some NPC will try to achieve in this world. \
Output it as a python list assigned to `global_goals` var in the code block, don't output anything else. Be creative and remember that \
some NPCs just want to live their lives without achieving something professionally.  \
NPC can be not only male but also female, so generate global goals taking into account both sexes.""")

if __name__ == '__main__':
    world_prompt = "A mid-sized village situated by the river in medieval Moldova. \
It has a self-sufficient community surrounded by a wooden palisade. There is a market square, \
a church, and fields for growing crops and grazing livestock. The villagers are engaged in crafts, \
and in times of war or danger, they rely on a small militia from nearby castle."
    temperature = -5
    day = 2
    month = 'February'
    year = 1000
    era = 'AD'
    hour = 12
    minute = 1
    second = 0
    pm_am = 'PM'
    daytime = 'noon'
    num_npcs = 3
    npc_yaml_template = """name: ''
global_goal: ''
happiness: 0
love: 0
health: 0
rested: 0
wealth: 0
hunger: 0
stress: 0
current_state_prompt: ''"""

    npcs_prompt = CREATE_NPCS_PROMPT.substitute(world_prompt=world_prompt, temperature=temperature, day=day, month=month, year=year, era=era, hour=hour, minute=minute, second=second, pm_am=pm_am, daytime=daytime, num_npcs=num_npcs, npc_yaml_template=npc_yaml_template)
    print(npcs_prompt)