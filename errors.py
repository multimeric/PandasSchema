class PandasSchemaError(BaseException):
    """
    Base class for all pandas_schema exceptions
    """


class InvalidSchemaError(BaseException):
    """
    Used when the schema is malformed, whether or not it fits the data frame
    """
