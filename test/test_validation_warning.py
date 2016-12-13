from validation_warning import ValidationWarning
import unittest

class WarningTest(unittest.TestCase):

    MESSAGE = 'Message'

    def test_shows_row_col(self):
        """
        Checks that a validation warning shows the row and column even if they are falsy values
        :return:
        """
        v = ValidationWarning(self.MESSAGE, '', 0, '')
        vs = str(v)
        self.assertRegexpMatches(vs, 'row')
        self.assertRegexpMatches(vs, self.MESSAGE)
        self.assertRegexpMatches(vs, 'column')

    def test_no_row_col(self):
        """
        Checks that a validation warning doesn't mention the row or column if neither is specified
        :return:
        """
        v = ValidationWarning(self.MESSAGE)
        vs = str(v)
        self.assertNotRegexpMatches(vs, 'row')
        self.assertRegexpMatches(vs, self.MESSAGE)
        self.assertNotRegexpMatches(vs, 'column')
