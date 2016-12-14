PandasSchema
============

.. contents::

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

.. include:: ../example/example.py
    :code: python

PandasSchema would then output

.. literalinclude:: ../example/result.txt

Installation
------------
Install PandasSchema using pip:

.. code:: bash

    pip install pandas_schema

Built-in Validators
-------------------
.. automodule:: validation
    :members:
    :exclude-members: BaseValidation,ElementValidation,CustomValidation


Custom Validators
-----------------

Simple Validators
~~~~~~~~~~~~~~~~~
The easiest way to add your own Validator is to use the CustomValidation class. For example if you wanted a validation
that checked if each cell in a column contained the word 'fail', and failed if it did, you'd do the following:

.. code:: python

    CustomValidation(lambda s: ~s.str.contains('fail'), 'contained the word fail')

The arguments to the CustomValidation constructor are listed here:

.. automodule:: validation
    :members: CustomValidation

Inheriting From ElementValidation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you want to implement more complicated logic that doesn't fit in a lambda, or you want to parameterize your Validator
and re-use it in different parts of your application, you can instead make a class that inherits from ElementValidation.

For example, the (simplified) implementation of the MatchesRegexValidation is presented below. All you need to do is write
an :code:`__init__`, :code:`get_message` and :code:`validate` function with the same signatures as in this example, and you should be
able to use your validation as though it were a built-in Validation.

.. code:: python

    class MatchesRegexValidation(ElementValidation):
        """
        Validates that a regular expression can match somewhere in each element in this column
        """

        def __init__(self, regex: typing.re.Pattern):
            self.pattern = regex

        def get_message(self) -> str:
            return 'does not match the regex "{}"'.format(self.pattern)

        def validate(self, series: pd.Series) -> pd.Series:
            return series.astype(str).str.contains(self.pattern)

API
---
Schema
~~~~~~
.. py:currentmodule:: schema
.. autoclass:: Schema
    :members:

Column
~~~~~~
.. py:currentmodule:: column
.. autoclass:: Column
    :members:

Validation_Warning
~~~~~~~~~~~~~~~~~~
.. automodule:: validation_warning
    :members:
    :special-members: __str__
