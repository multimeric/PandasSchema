PandasSchema
------------

.. image:: https://travis-ci.org/TMiguelT/PandasSchema.svg?branch=master
    :target: https://travis-ci.org/TMiguelT/PandasSchema

.. contents::

Introduction
------------
.. include:: ../common/introduction.rst

Installation
------------
Install PandasSchema using pip:

.. code:: bash

    pip install pandas_schema

Module Summary
--------------
As you can probably see from the example above, the main classes you need to interact with to perform a validation are
Schema_, Column_, the `Validation`__ classes, and ValidationWarning_. A Schema contains many Columns, and a Column contains many
Validations. Then to run a validation, you simply call ``schema.validate()`` on a DataFrame, which will produce a list of
ValidationWarnings. The public interface of these classes is documented here. Validations are covered in the next section.

__ Validators_

Schema
~~~~~~
.. py:currentmodule:: pandas_schema.schema
.. autoclass:: Schema
    :members:

Column
~~~~~~
.. py:currentmodule:: pandas_schema.column
.. autoclass:: Column

ValidationWarning
~~~~~~~~~~~~~~~~~
.. automodule:: pandas_schema.validation_warning
    :members:
    :special-members: __str__

Validators
----------

Built-in Validators
~~~~~~~~~~~~~~~~~~~
.. automodule:: pandas_schema.validation
    :members:
    :exclude-members: CustomElementValidation,CustomSeriesValidation


Custom Validators
~~~~~~~~~~~~~~~~~

Simple Validators
_________________
The easiest way to add your own Validator is to use the CustomSeriesValidation or CustomElementValidation class.

For example if you wanted a validation that checked if each cell in a column contained the word 'fail', and failed if
it did, you'd do one of the following:

.. code:: python

    CustomSeriesValidation(lambda s: ~s.str.contains('fail'), 'contained the word fail')

    CustomElementValidation(lambda s: ~s.contains('fail'), 'contained the word fail')

The difference between these two classes is that CustomSeriesValidation uses Pandas Series methods to operate on the entire
series using fast, natively implemented functions, while CustomElementValidation operates on each element using
ordinary Python code.

Consequently, if the validation you want to create is easy to express using Pandas Series methods
(http://pandas.pydata.org/pandas-docs/stable/api.html#series), we recommend you use a CustomSeriesValidation since it
will likely perform better. Otherwise, feel free to use a CustomElementValidation. Of course, if there is a built-in
Validation class that fits your use-case, like MatchesPattern, it will be implemented as fast as possible, so then
this is the recommended method to implement the validation

    The arguments to these classes constructors are listed here:


.. automodule:: pandas_schema.validation
    :members: CustomSeriesValidation,CustomElementValidation


Inheriting From _SeriesValidation
_________________________________
If you want to implement more complicated logic that doesn't fit in a lambda, or you want to parameterize your Validator
and re-use it in different parts of your application, you can instead make a class that inherits from
:code:`_SeriesValidation`.

All this class needs is:

* An :code:`__init__` constructor that calls :code:`super().__init__(**kwargs)`
* A :code:`default_message` property
* A :code:`validate` method

For reference on how these fields should look, have a look at the source code for the `Built-in Validators`_ (click the
:code:`[source]` button next to any of them)

Boolean Logic on Validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can also combine validators with the Boolean operators ``and``, ``or`` and ``not``. These are implemented using
the following python operators:

=================  ========
Boolean Operation  Operator
=================  ========
``not``             ``~``
``and``             ``&``
``or``              ``|``
=================  ========

For example, if we wanted a validation that checks if the cell either contains a number, or is a word with more than 1
character that also contains an 'a', we could do the following:

.. literalinclude:: ../../example/boolean.py
    :language: python

This would produce the following result, because 'a' is a word, but isn't more than one character, and because 'the' is
a word, but it doesn't contain the letter 'a':

.. literalinclude:: ../../example/boolean.txt

Note that these operators do not short-circuit, so all validations will be applied to all rows, regardless of if that
row has already failed a validation.

Changelog
---------
.. include:: ./changelog.rst

Development
-----------

To install PandasSchema's development requirements, run

.. code:: bash

    pip install -r requirements.txt

The setup.py can be run as an executable, and it provides the following extra commands:

* :code:`./setup.py test`: runs the tests
* :code:`./setup.py build_readme`: rebuilds the ``README.rst`` from ``doc/readme/README.rst``
* :code:`./setup.py build_site --dir=<dir>`: builds the documentation website from ``doc/site/index.rst`` into ``<dir>``
