class ValidationWarning:
    """
    Represents a difference between the schema and data frame, found during the validation of the data frame
    """

    def __init__(self, message: str, value: str = None, row: int = None, column: str = None):
        self.message = message
        self.value = value
        self.row = row
        self.column = column

    def __str__(self):
        if self.row is not None and self.column is not None and self.value is not None:
            return '{{row: {}, column: "{}"}}: "{}" {}'.format(self.row, self.column, self.value, self.message)
        else:
            return self.message
