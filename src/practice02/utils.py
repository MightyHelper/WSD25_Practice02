import math


def is_prime(n: int) -> bool:
    """Check if a number is prime.

    Args:
        n: The number to check.

    Returns:
        bool: True if the number is prime, False otherwise.
    """
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2

    # Check odd divisors up to square root
    sqrt_n = int(math.isqrt(n)) + 1
    for i in range(3, sqrt_n, 2):
        if n % i == 0:
            return False
    return True
