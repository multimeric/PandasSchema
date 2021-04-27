class PanSchError(Exception):
    """
    Base class for all pandas_schema exceptions
    """

    def __init__(self, message=None):
        super().__init__(message)


class PanSchIndexError(PanSchError):
    """
    Some issue with creating a PandasIndexer
    """

    def __init__(self, message):
        super().__init__(message=message)


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
