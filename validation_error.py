class ValidationError:
    """
    Represents a difference between the schema and data frame, found during the validation of the data frame
    """

    def __init__(self, message: str, row: int, column: str):
        self.message = message
        self.row = row
        self.column = column

    def __str__(self):
        error = ''
        error += '{{row: {}, column: "{}"}}: '.format(self.row, self.column)
        error += self.message
        return error
