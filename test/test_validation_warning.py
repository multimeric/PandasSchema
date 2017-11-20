import unittest

from pandas_schema import ValidationWarning


class WarningTest(unittest.TestCase):
    MESSAGE = 'Message'

    def test_shows_row_col(self):
        """
        Checks that a validation warning shows the row and column even if they are falsy values
        :return:
        """
        v = ValidationWarning(self.MESSAGE, '', 0, '')
        vs = str(v)
        self.assertRegex(vs, 'row')
        self.assertRegex(vs, self.MESSAGE)
        self.assertRegex(vs, 'column')

    def test_no_row_col(self):
        """
        Checks that a validation warning doesn't mention the row or column if neither is specified
        :return:
        """
        v = ValidationWarning(self.MESSAGE)
        vs = str(v)
        self.assertNotRegex(vs, 'row')
        self.assertRegex(vs, self.MESSAGE)
        self.assertNotRegex(vs, 'column')
