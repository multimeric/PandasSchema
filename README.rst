
PandasSchema
************

For the full documentation, refer to the `Github Pages Website
<https://tmiguelt.github.io/PandasSchema/>`_.

======================================================================

PandasSchema is a module for validating tabulated data, such as CSVs
(Comma Separated Value files), and TSVs (Tab Separated Value files).
It uses the incredibly powerful data analysis tool Pandas to do so
quickly and efficiently.

For example, say your code expects a CSV that looks a bit like this:

.. code:: default

   Given Name,Family Name,Age,Sex,Customer ID
   Gerald,Hampton,82,Male,2582GABK
   Yuuwa,Miyake,27,Male,7951WVLW
   Edyta,Majewska,50,Female,7758NSID

Now you want to be able to ensure that the data in your CSV is in the
correct format:

.. code:: python

   import pandas as pd
   from io import StringIO
   from pandas_schema import Column, Schema
   from pandas_schema.validation import LeadingWhitespaceValidation, TrailingWhitespaceValidation, CanConvertValidation, MatchesPatternValidation, InRangeValidation, InListValidation

   schema = Schema([
       Column('Given Name', [LeadingWhitespaceValidation(), TrailingWhitespaceValidation()]),
       Column('Family Name', [LeadingWhitespaceValidation(), TrailingWhitespaceValidation()]),
       Column('Age', [InRangeValidation(0, 120)]),
       Column('Sex', [InListValidation(['Male', 'Female', 'Other'])]),
       Column('Customer ID', [MatchesPatternValidation(r'\d{4}[A-Z]{4}')])
   ])

   test_data = pd.read_csv(StringIO('''Given Name,Family Name,Age,Sex,Customer ID
   Gerald ,Hampton,82,Male,2582GABK
   Yuuwa,Miyake,270,male,7951WVLW
   Edyta,Majewska ,50,Female,775ANSID
   '''))

   errors = schema.validate(test_data)

   for error in errors:
       print(error)

PandasSchema would then output

.. code:: text

   {row: 0, column: "Given Name"}: "Gerald " contains trailing whitespace
   {row: 1, column: "Age"}: "270" was not in the range [0, 120)
   {row: 1, column: "Sex"}: "male" is not in the list of legal options (Male, Female, Other)
   {row: 2, column: "Family Name"}: "Majewska " contains trailing whitespace
   {row: 2, column: "Customer ID"}: "775ANSID" does not match the pattern "\d{4}[A-Z]{4}"
