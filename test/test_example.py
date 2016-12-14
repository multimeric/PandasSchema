import sys
import pathlib
import unittest
from contextlib import redirect_stdout
from io import StringIO

here = pathlib.Path(__file__).parent
sys.path.append(str((here / '../..').resolve()))
examples = here / '../example'

class Example(unittest.TestCase):
    def test_example(self):
        """
        Checks that the text printed out by the example.py is the same as the text in result.txt
        :return:
        """
        code_path = examples / 'example.py'
        stdout = StringIO()
        with code_path.open() as code_file, (examples / 'result.txt').open() as result_file, redirect_stdout(stdout):
            code = compile(code_file.read(), str(code_path), 'exec')
            exec(code)
            self.assertEqual(stdout.getvalue(), result_file.read())

