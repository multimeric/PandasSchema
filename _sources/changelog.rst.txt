0.3.6
~~~~~

* Include the column name in the ``ValidationWarning`` when a column listed in the schema is not present in the data frame (`#65 <https://github.com/multimeric/PandasSchema/issues/65>`_)
* ``schema.validate()`` now no longer immediately returns when a column is missing. Instead it adds a ``ValidationWarning`` and continues validation

0.3.5
~~~~~
- Add version to a separate file, so that ``pandas_schema.__version__`` now works (see `#11 <https://github.com/TMiguelT/PandasSchema/issues/11>`_)
- Make the ``InRangeValidation`` correctly report a validation failure when it validates non-numeric text, instead of crashing (see `#30 <https://github.com/TMiguelT/PandasSchema/pull/11>`_)
