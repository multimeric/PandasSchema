# ValidationWarnings
## Options for the ValidationWarning data
* We keep it as is, with one single ValidationWarning class that stores a `message` and a reference to the validation
that spawned it
* PREFERRED: As above, but we add a dictionary of miscellaneous kwargs to the ValidationWarning for storing stuff like the row index that failed
* We have a dataclass for each Validation type that stores things in a more structured way
    * Why bother doing this if the Validation stores its own structure for the column index etc?

## Options for the ValidationWarning message
* It's generated from the Validation as a fixed string, as it is now
* It's generated dynamically by the VW
    * This means that custom messages means overriding the VW class
* PREFERRED: It's generated dynamically in the VW by calling the parent Validation with a reference to itself, e.g. 
  ```python
  class ValidationWarning:
      def __str__(self):
          return self.validation.generate_message(self)
  
  class Validation:
      def generate_message(warning: ValidationWarning) -> str:
          pass
  ```
    * This lets the message function use all the validation properties, and the dictionary of kwargs that it specified
    * `generate_message()` will call `default_message(**kwargs)`, the dynamic class method, or `self.custom_message`, the
    non-dynamic string specified by the user
    * Each category of Validation will define a `create_prefix()` method, that creates the {row: 1, column: 2} prefix
    that goes before each message. Thus, `generate_message()` will concatenate that with the actual message
* 

## Options for placing CombinedValidation in the inheritance hierarchy
* In order to make both CombinedValidation and BooleanSeriesValidation both share a class, so they can be chained together,
either we had to make a mixin that creates a "side path" that doesn't call `validate` (in this case, `validate_with_series`),
or we 

# Rework of Validation Indexing
## All Indexed
* All Validations now have an index and an axis
* However, this index can be none, can be column only, row only, or both
* When combined with each other, the resulting boolean series will be broadcast using numpy broadcasting rules
* e.g. 
    * A per-series validation might have index 0 (column 0) and return a scalar (the whole series is okay)
    * A per-cell validation might have index 0 (column 0) and return a series (True, True, False) indicating that cell 0 and 1 of column 0 are okay
    * A per-frame validation would have index None, and might return True if the whole frame meets the validation, or a series indicating which columns or rows match the validation
    
# Rework of combinedvalidations
## Bitwise
* Could assign each validation a bit in a large bitwise enum, and `or` together a number each time that index fails a validatioin. This lets us track the origin of each warning, allowing us to slice them out by bit and generate an appropriate list of warnings