class PanSchError(BaseException):
    """
    Base class for all pandas_schema exceptions
    """


class PanSchInvalidSchemaError(PanSchError):
    """
    The schema is malformed, whether or not it fits the data frame
    """


class PanSchNoIndexError(PanSchInvalidSchemaError):
    """
    A validation was provided that has not specified an index
    """


class PanSchArgumentError(PanSchError):
    """
    An argument passed to a function has an invalid type or value
    """
