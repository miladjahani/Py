"""
Unit tests for Calculator class using unittest (standard library compatible).
"""
import unittest
from calc import Calculator

class TestCalculator(unittest.TestCase):
    def test_add_positive(self):
        self.assertEqual(Calculator.add(2, 3), 5)
        self.assertEqual(Calculator.add(10.5, 4.5), 15.0)

    def test_add_negative(self):
        self.assertEqual(Calculator.add(-5, -7), -12)
        self.assertEqual(Calculator.add(-5, 5), 0)

    def test_multiply_positive(self):
        self.assertEqual(Calculator.multiply(3, 4), 12)
        self.assertEqual(Calculator.multiply(2.5, 2), 5.0)

    def test_multiply_zero_and_negative(self):
        self.assertEqual(Calculator.multiply(0, 100), 0)
        self.assertEqual(Calculator.multiply(-3, 4), -12)
        self.assertEqual(Calculator.multiply(-2, -6), 12)

if __name__ == "__main__":
    unittest.main()
