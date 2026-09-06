"""
Calculator module implementing core arithmetic operations.
"""
from typing import Union

Number = Union[int, float]

class Calculator:
    """A robust calculator supporting addition and multiplication."""

    @staticmethod
    def add(a: Number, b: Number) -> Number:
        """Return the sum of a and b."""
        return a + b

    @staticmethod
    def multiply(a: Number, b: Number) -> Number:
        """Return the product of a and b."""
        return a * b
