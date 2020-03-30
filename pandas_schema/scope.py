import enum

class ValidationScope(enum.Enum):
    """
    Defines the scope of a validation, ie DATA_FRAME scope means this validation validates the entire DataFrame is
    valid or invalid, SERIES means each series can be valid/invalid, and CELL means each index anywhere in the frame
    can be valid/invalid
    """
    DATA_FRAME = 0
    SERIES = 1
    CELL = 2

