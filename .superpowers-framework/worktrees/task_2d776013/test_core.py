
import unittest
from core import process

class TestCore(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(process("test"), "processed: test")
    
    def test_empty(self):
        self.assertEqual(process(""), "processed: ")

if __name__ == '__main__':
    unittest.main()
