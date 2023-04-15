from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.formatted_text import HTML
from utils import bcolors, Input


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


class InitValidator(Validator):
    def __init__(self, game, user_input: Input):
        self.game = game
        self.user_input = user_input

    def validate(self, document):
        text = document.text

        if text == "l":
            if not getattr(self.game, f"cur_{self.user_input}_path").exists():
                raise ValidationError(
                    message=f'{self.user_input} with {getattr(self.game.settings, f"cur_{self.user_input}_name")} name does not exist. Try again'
                )
        elif text == "n":
            if getattr(self.game, f"cur_{self.user_input}_path").exists():
                raise ValidationError(
                    message=f'{self.user_input} with {getattr(self.game.settings, f"cur_{self.user_input}_name")} name already exists. Try again'
                )
        else:
            raise ValidationError(message="Invalid input (l/n). Try again")
