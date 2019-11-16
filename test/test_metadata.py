import unittest
from packaging import version
import pandas_schema


class Version(unittest.TestCase):
    def test_version(self):
        """
        Check that we have a __version__ defined, and that it's at least 0.3.0
        """
        self.assertIsNotNone(pandas_schema.__version__)
        parsed = version.parse(pandas_schema.__version__)
        self.assertGreaterEqual(parsed, version.Version('0.3.0'))
