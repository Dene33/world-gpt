from enum import Enum, StrEnum
from pathlib import Path
import ast
from yamldataclassconfig.config import YamlDataClassConfig
import yaml
import openai
import itertools
import numpy as np


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class InitInput(StrEnum):
    game = "game"
    world = "world"
    npcs = "npcs"


class TickInput(StrEnum):
    increment = "increment"


class Input:
    init = InitInput
    tick = TickInput


def get_last_modified_file(path):
    files = [f for f in Path(path).iterdir() if f.is_file()]
    if files:
        last_modified_file = max(files, key=lambda p: p.stat().st_mtime)
    else:
        last_modified_file = None
    return last_modified_file


def int_to_month(month: int):
    if month == 1:
        return "January"
    elif month == 2:
        return "February"
    elif month == 3:
        return "March"
    elif month == 4:
        return "April"
    elif month == 5:
        return "May"
    elif month == 6:
        return "June"
    elif month == 7:
        return "July"
    elif month == 8:
        return "August"
    elif month == 9:
        return "September"
    elif month == 10:
        return "October"
    elif month == 11:
        return "November"
    elif month == 12:
        return "December"
    else:
        return "Invalid month"


def hour_to_pm_am(hour: int):
    if hour > 12:
        return "PM"
    else:
        return "AM"


def hour_to_daytime(hour: int):
    if hour < 0 or hour > 24:
        return "Invalid hour"

    if hour >= 6 and hour < 12:
        return "Morning"
    elif hour >= 12 and hour < 18:
        return "Afternoon"
    elif hour >= 18 and hour < 22:
        return "Evening"
    elif hour >= 22 or hour < 2:
        return "Night"
    elif hour >= 2 and hour < 6:
        return "Late night"


def code_block_to_var(code_block: str):
    # remove the code block characters from the string
    split_lines = code_block.split("\n")[1:-1]
    no_code_block_str = "\n".join(split_lines)

    # convert the string to a variable
    var = ast.literal_eval(no_code_block_str.split("=")[1].strip())
    return var


def save_yaml_from_dataclass(save_path: Path, data: YamlDataClassConfig):
    yaml.emitter.Emitter.process_tag = lambda self, *args, **kw: None
    with open(save_path, "w") as savefile:
        yaml.dump(data, savefile)


def load_yaml_to_dataclass(yaml_dataclass: YamlDataClassConfig, yaml_path: Path):
    if yaml_path:
        yaml_dataclass.load(path=yaml_path)
    else:
        print(f"Can't load yaml from path: {yaml_path}, path doesn't exist")

    return


def request_openai(
    model: str, prompt: str, tries_num: int = -1, response_processor=None, verbose=False
):
    processed_response = None

    if tries_num == -1:
        tries_range = itertools.count()
    else:
        tries_range = range(tries_num)

    for i in tries_range:
        try:
            print(f"{bcolors.OKBLUE}OpenAI request try {i+1}...{bcolors.ENDC}")
            response = openai.ChatCompletion.create(
                model=model, messages=[{"role": "user", "content": prompt}]
            )

            # get the response
            response_content = response["choices"][0]["message"]["content"]
            if verbose:
                print(response_content)
            if response_processor:
                processed_response = response_processor(response_content)
            else:
                processed_response = response_content

        except Exception as e:
            continue
        else:
            break

    if not processed_response:
        print(
            f"{bcolors.FAIL}OpenAI request failed, check your prompt or increase the number of request tries{bcolors.ENDC}"
        )
        return None

    return processed_response


def ensure_dirs_exist(dirs: list[Path]):
    for dir in dirs:
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)


def month_to_iso(month: int):
    if month == 1:
        return "01"
    elif month == 2:
        return "02"
    elif month == 3:
        return "03"
    elif month == 4:
        return "04"
    elif month == 5:
        return "05"
    elif month == 6:
        return "06"
    elif month == 7:
        return "07"
    elif month == 8:
        return "08"
    elif month == 9:
        return "09"
    elif month == 10:
        return "10"
    elif month == 11:
        return "11"
    elif month == 12:
        return "12"
    else:
        return "Invalid month"


def day_to_iso(day: int):
    if day == 1:
        return "01"
    elif day == 2:
        return "02"
    elif day == 3:
        return "03"
    elif day == 4:
        return "04"
    elif day == 5:
        return "05"
    elif day == 6:
        return "06"
    elif day == 7:
        return "07"
    elif day == 8:
        return "08"
    elif day == 9:
        return "09"
    elif day >= 10 and day <= 31:
        return str(day)
    else:
        return "Invalid day"


def hour_to_iso(hour: int):
    if hour == 0:
        return "00"
    elif hour == 1:
        return "01"
    elif hour == 2:
        return "02"
    elif hour == 3:
        return "03"
    elif hour == 4:
        return "04"
    elif hour == 5:
        return "05"
    elif hour == 6:
        return "06"
    elif hour == 7:
        return "07"
    elif hour == 8:
        return "08"
    elif hour == 9:
        return "09"
    elif hour >= 10 and hour <= 23:
        return str(hour)
    else:
        return "Invalid hour"


def minute_to_iso(minute: int):
    if minute == 0:
        return "00"
    elif minute == 1:
        return "01"
    elif minute == 2:
        return "02"
    elif minute == 3:
        return "03"
    elif minute == 4:
        return "04"
    elif minute == 5:
        return "05"
    elif minute == 6:
        return "06"
    elif minute == 7:
        return "07"
    elif minute == 8:
        return "08"
    elif minute == 9:
        return "09"
    elif minute >= 10 and minute <= 59:
        return str(minute)
    else:
        return "Invalid minute"


second_to_iso = hour_to_iso


def to_datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    era: str = "AD",
):
    if era == "BC":
        year = -(year - 1)

    return np.datetime64(
        f"{year}-{month_to_iso(month)}-{(day_to_iso(day))}T{hour_to_iso(hour)}:{minute_to_iso(minute)}:{second_to_iso(second)}"
    )


def from_datetime(datetime: np.datetime64):
    datetime_str = datetime.astype("str")
    if datetime_str.startswith("-"):
        era = "BC"
        datetime_str = datetime_str[1:]
    else:
        era = "AD"

    year_month_day = datetime_str.split("T")[0]
    year, month, day = year_month_day.split("-")

    hour_minute_second = datetime_str.split("T")[1]
    hour, minute, second = hour_minute_second.split(":")

    return int(year), int(month), int(day), int(hour), int(minute), int(second), era


if __name__ == "__main__":
    dt = to_datetime(month=1, day=1, year=20000, era="AD")

    print(dt)
    delta = np.timedelta64(365, "D")

    t = dt + delta + delta
    print(t)
    year, month, day, hour, minute, second, era = from_datetime(t)
    print(year, month, day, hour, minute, second, era)
