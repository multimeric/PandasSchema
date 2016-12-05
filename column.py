import typing
from validation import Validation


class Column:
    def __init__(self, name: str, validations: typing.Iterable[Validation]=[], allow_empty=False):
        self.name = name
        self.validations = list(validations)
        self.allow_empty = allow_empty
