class ValidationError:
    """
    Represents a difference between the schema and data frame, found during the validation of the data frame
    """

    def __init__(self, message: str, row: int = None, column: str = None):
        self.message = message
        self.row = row
        self.column = column

    def __str__(self):
        if self.row and self.column:
            return '{{row: {}, column: "{}"}}: {}'.format(self.row, self.column, self.message)
        else:
            return self.message
