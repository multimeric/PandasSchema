PandasSchema is a module for validating tabulated data, such as CSVs (Comma Separated Value files), and TSVs (Tab
Separated Value files). It uses the incredibly powerful data analysis tool pandas to do so quickly and efficiently.

For example, say your code expects a CSV that looks a bit like this:

..
    Given Name,Family Name,Age,Sex,Customer ID
    Gerald,Hampton,82,Male,2582GABK
    Yuuwa,Miyake,27,Male,7951WVLW
    Edyta,Majewska,50,Female,7758NSID

Now you want to be able to ensure that the data in your CSV is in the correct format:

.. include:: ../../example/example.py
    :code: python

PandasSchema would then output

.. include:: ../../example/result.txt

