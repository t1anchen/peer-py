import math


def prime_factors(n):
    ans = []
    # even number divisible
    while n % 2 == 0:
        n = n / 2

    # n became odd
    for i in range(3, int(math.sqrt(n))+1, 2):

        while (n % i == 0):
            ans.append(i)
            n = n / i

    if n > 2:
        ans.append(n)

    return ans
