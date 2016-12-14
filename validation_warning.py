class ValidationWarning:
    """
    Represents a difference between the schema and data frame, found during the validation of the data frame
    """

    def __init__(self, message: str, value: str = None, row: int = None, column: str = None):
        self.message = message
        self.value = value
        """The value of the failing cell in the DataFrame"""
        self.row = row
        """The row index (usually an integer starting from 0) of the cell that failed the validation"""
        self.column = column
        """The column name of the cell that failed the validation"""

    def __str__(self) -> str:
        """
        The entire warning message as a string
        """
        if self.row is not None and self.column is not None and self.value is not None:
            return '{{row: {}, column: "{}"}}: "{}" {}'.format(self.row, self.column, self.value, self.message)
        else:
            return self.message
