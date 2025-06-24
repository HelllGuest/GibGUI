import unittest
from src.main import main

class TestBasicFunctionality(unittest.TestCase):
    def test_main_returns_zero(self):
        """Test that main function returns 0."""
        self.assertEqual(main(), 0)

if __name__ == '__main__':
    unittest.main()
