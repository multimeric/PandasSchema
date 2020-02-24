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
