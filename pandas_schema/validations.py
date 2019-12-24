from .core import _SeriesValidation, IndexSeriesValidation
from .validation_warning import ValidationWarning
import pandas as pd
import math
import typing

class InRangeValidation(IndexSeriesValidation):
    """
    Checks that each element in the series is within a given numerical range
    """

    def __init__(self, min: float = -math.inf, max: float = math.inf, **kwargs):
        """
        :param min: The minimum (inclusive) value to accept
        :param max: The maximum (exclusive) value to accept
        """
        self.min = min
        self.max = max
        super().__init__(**kwargs)

    @property
    def default_message(self):
        return 'was not in the range [{}, {})'.format(self.min, self.max)

    def validate_series(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
        series = pd.to_numeric(series)
        return (series >= self.min) & (series < self.max)
