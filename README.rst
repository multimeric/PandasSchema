PandasSchema
============

Introduction
------------
PandasSchema is a module for validating tabulated data, such as CSVs (Comma Separated Value files), and TSVs (Tab
Separated Value files). It uses the incredibly powerful data analysis tool pandas to do so quickly and efficiently.

For example, say your code expects a CSV that looks a bit like this:

..
    Given Name,Family Name,Age,Sex,Customer ID
    Gerald,Hampton,82,Male,2582GABK
    Yuuwa,Miyake,27,Male,7951WVLW
    Edyta,Majewska,50,Female,7758NSID

Now you want to be able to ensure that the data in your CSV is in the correct format:

.. code:: python
    import pandas as pd
    from io import StringIO
    from pandas_schema import Column, Schema
    from pandas_schema.validation import LeadingWhitespaceValidation, TrailingWhitespaceValidation, CanConvertValidation, MatchesRegexValidation, InRangeValidation, InListValidation

    schema = Schema([
        Column('Given Name', [LeadingWhitespaceValidation(), TrailingWhitespaceValidation()]),
        Column('Family Name', [LeadingWhitespaceValidation(), TrailingWhitespaceValidation()]),
        Column('Age', [InRangeValidation(0, 120)]),
        Column('Sex', [InListValidation(['Male', 'Female', 'Other'])]),
        Column('Customer ID', [MatchesRegexValidation(r'\d{4}[A-Z]{4}')])
    ])

    test_data = pd.from_csv(StringIO('''
        Gerald ,Hampton,82,Male,2582GABK
        Yuuwa,Miyake,270,male,7951WVLW
        Edyta,Majewska ,50,Female,775ANSID
    '''))

    schema.validate()


Installation
------------
Install PandasSchema using pip:

.. code:: bash
pip install pandas_schema


