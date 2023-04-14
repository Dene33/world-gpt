from enum import Enum, StrEnum
from pathlib import Path
import ast
from yamldataclassconfig.config import YamlDataClassConfig
import yaml
import openai
import itertools

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class InitInput(StrEnum):
    game = 'game'
    world = 'world'
    npcs = 'npcs'

class Input:
    init = InitInput
    placeholder = 'placeholder'

def get_last_modified_file(path):
    files = [f for f in Path(path).iterdir() if f.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime)

def int_to_month(month: int):
    if month == 1:
        return 'January'
    elif month == 2:
        return 'February'
    elif month == 3:
        return 'March'
    elif month == 4:
        return 'April'
    elif month == 5:
        return 'May'
    elif month == 6:
        return 'June'
    elif month == 7:
        return 'July'
    elif month == 8:
        return 'August'
    elif month == 9:
        return 'September'
    elif month == 10:
        return 'October'
    elif month == 11:
        return 'November'
    elif month == 12:
        return 'December'
    else:
        return 'Invalid month'
    
def hour_to_pm_am(hour: int):
    if hour > 12:
        return 'PM'
    else:
        return 'AM'

def hour_to_daytime(hour: int):
    if hour < 0 or hour > 24:
        return 'Invalid hour'

    if hour >= 6 and hour < 12:
        return 'Morning'
    elif hour >= 12 and hour < 18:
        return 'Afternoon'
    elif hour >= 18 and hour < 22:
        return 'Evening'
    elif hour >= 22 or hour < 2:
        return 'Night'
    elif hour >= 2 and hour < 6:
        return 'Late night'

def code_block_to_var(code_block: str):
    # remove the code block characters from the string
    split_lines = code_block.split('\n')[1:-1]
    no_code_block_str = '\n'.join(split_lines)

    # convert the string to a variable
    var = ast.literal_eval(no_code_block_str.split('=')[1].strip())
    return var

def save_yaml(save_path: Path, data:YamlDataClassConfig):
    yaml.emitter.Emitter.process_tag = lambda self, *args, **kw: None
    with open(save_path, 'w') as savefile:
        yaml.dump(data, savefile)

def request_openai(model: str, prompt: str, tries_num: int=-1, response_processor=None):
    processed_response = None

    if tries_num == -1:
        tries_range = itertools.count()
    else:
        tries_range = range(tries_num)
    
    for i in tries_range:
        try:
            print(f'{bcolors.OKBLUE}OpenAI request try {i+1}...{bcolors.ENDC}')
            response = openai.ChatCompletion.create(model=model,
                                                    messages=[{"role": "user", "content": prompt}]
                                                    )

            # get the response
            response_content = response['choices'][0]['message']['content']
            # print(response_content)
            processed_response = response_processor(response_content)
        except Exception as e:
            continue
        else:
            break
    
    if not processed_response:
        print(f'{bcolors.FAIL}OpenAI request failed, check your prompt or increase the number of request tries{bcolors.ENDC}')
        return None

    return processed_response

if __name__ == '__main__':
    # print(get_last_modified_file('./data/Test_Game/worlds/Test_World'))
    # t = hour_to_pm_am(23)
    # for i in range(30):
    #     print(f'{i} {hour_to_daytime(i)}')
    # t = hour_to_daytime(0)
    # print(t)

    t = Input.init.game

    if isinstance(t, Input.init):
        if t == Input.init.game:
            print(t)

    # if t == Input.init.game:
    #     print('init')