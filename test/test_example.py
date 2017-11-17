import pathlib
import unittest
from contextlib import redirect_stdout
from io import StringIO

examples = (pathlib.Path(__file__) / '../../example').resolve()


class Example(unittest.TestCase):
    def test_example(self):
        """
        Checks that the text printed out by the example.py is the same as the text in example.txt
        :return:
        """
        code_path = examples / 'example.py'
        stdout = StringIO()
        with code_path.open() as code_file, (examples / 'example.txt').open() as result_file, redirect_stdout(stdout):
            code = compile(code_file.read(), str(code_path), 'exec')
            exec(code)
            self.assertEqual(stdout.getvalue(), result_file.read())

    def test_boolean(self):
        """
        Checks that the text printed out by boolean.py is the same as the text in boolean.txt
        :return:
        """
        code_path = examples / 'boolean.py'
        stdout = StringIO()
        with code_path.open() as code_file, (examples / 'boolean.txt').open() as result_file, redirect_stdout(stdout):
            code = compile(code_file.read(), str(code_path), 'exec')
            exec(code)
            self.assertEqual(stdout.getvalue(), result_file.read())
