from dataclasses import dataclass, field

@dataclass
class ValidationWarning:
    """
    Represents a difference between the schema and data frame, found during the validation
    of the data frame
    """
    validation: 'pandas_schema.core.BaseValidation'
    """
    The validation that spawned this warning
    """

    props: dict = field(default_factory=dict)
    """
    List of data about this warning in addition to that provided by the validation, for
    example, if a cell in the DataFrame didn't match the validation, the props might
    include a `value` key, for storing what the actual value was
    """

    def __init__(self, validation, **props):
        self.validation = validation
        self.props = props

    @property
    def message(self) -> str:
        """
        Return this validation as a string
        """
        # Internally, this actually asks the validator class to formulate a message
        return self.validation.message(self)

    @property
    def prefix(self) -> str:
        return self.validation.prefix(self)

    @property
    def suffix(self) -> str:
        return self.validation.suffix(self)

    def __str__(self):
        return self.message


class CombinedValidationWarning(ValidationWarning):
    """
    Warning for a CombinedValidation, which itself wraps 2 other Warnings from child Validations
    """
    left: ValidationWarning
    right: ValidationWarning

    def __init__(self, left: ValidationWarning, right: ValidationWarning, **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.right = right

    @property
    def message(self):
        """
        Return this validation as a string
        """
        # Unlike a normal ValidationWarning, this doesn't ask CombinedValidation for a message, it just combines
        # existing messages
        return '{} {} and {}'.format(self.left.prefix, self.left.suffix, self.right.suffix)

    @property
    def suffix(self) -> str:
        return '{} and {}'.format(self.left.suffix, self.right.suffix)

    @property
    def prefix(self) -> str:
        return self.left.prefix
