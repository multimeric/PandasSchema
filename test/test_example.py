import doctest
import sys
import pathlib

here = pathlib.Path(__file__).parent
sys.path.append(str((here / '../..').resolve()))


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocFileSuite('README.rst', package='pandas_schema'))
    return tests
