from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.formatted_text import HTML
from utils import bcolors, Input
from pathlib import Path
from prompt_toolkit import prompt
from resources_paths import DATA_PATH, GAMES_PATH, YAML_TEMPLATES_PATH, INIT_WORLDS_PATH


def _is_number(text: str):
    return text.isdigit()


def _is_tick_type(text: str):
    return text in ("years", "months", "days", "hours", "minutes", "seconds")


def _is_float(text: str):
    try:
        float(text)
        return True
    except ValueError:
        return False


def _is_era(text: str):
    return text in ("BC", "AD")


def _is_month(text: str):
    return text in [str(i) for i in range(1, 13)]


def _is_day(text: str):
    return text in [str(i) for i in range(1, 32)]


def _is_hour(text: str):
    return text in [str(i) for i in range(0, 24)]


def _is_minute(text: str):
    return text in [str(i) for i in range(0, 60)]


def _is_second(text: str):
    return text in [str(i) for i in range(0, 60)]


is_number = Validator.from_callable(
    _is_number, error_message="This input contains non-numeric characters"
)

is_tick_type = Validator.from_callable(
    _is_tick_type, error_message="This input contains incorrect tick type"
)

is_float = Validator.from_callable(
    _is_float, error_message="This input contains non-float value"
)

is_era = Validator.from_callable(
    _is_era, error_message="This input contains incorrect era"
)

is_month = Validator.from_callable(
    _is_month, error_message="This input contains incorrect month, use numbers 1-12"
)

is_day = Validator.from_callable(
    _is_day, error_message="This input contains incorrect day"
)

is_hour = Validator.from_callable(
    _is_hour, error_message="This input contains incorrect hour"
)

is_minute = Validator.from_callable(
    _is_minute, error_message="This input contains incorrect minute"
)

is_second = Validator.from_callable(
    _is_second, error_message="This input contains incorrect second"
)


class NotInListValidator(Validator):
    def __init__(self, list_to_check: list):
        self.list_to_check = list_to_check

    def validate(self, document):
        text = document.text

        if text not in self.list_to_check:
            raise ValidationError(
                message=f"{text} does not exist in {self.list_to_check}. Try again"
            )


class IsInListValidator(Validator):
    def __init__(self, list_to_check: list):
        self.list_to_check = list_to_check

    def validate(self, document):
        text = document.text

        if text in self.list_to_check:
            raise ValidationError(
                message=f"{text} already exists in {self.list_to_check}. Try again"
            )
