# -*- coding: utf-8 -*-
from attest import Tests, assert_hook, raises

from glicko import *


suite = Tests()


class almost(object):

    def __init__(self, val, precision=3):
        self.val = val
        self.precision = precision

    def almost_equals(self, val1, val2):
        if round(val1, self.precision) == round(val2, self.precision):
            return True
        fmt = '%.{0}f'.format(self.precision)
        mantissa = lambda f: int((fmt % f).replace('.', ''))
        return abs(mantissa(val1) - mantissa(val2)) <= 1

    def __eq__(self, other):
        try:
            if not self.almost_equals(self.val.volatility, other.volatility):
                return False
        except AttributeError:
            pass
        return self.almost_equals(self.val.mu, other.mu) and \
               self.almost_equals(self.val.sigma, other.sigma)

    def __repr__(self):
        return repr(self.val)


@suite.test
def glicko_glickman_example():
    env = Glicko()
    r1 = Rating(1500, 200)
    r2 = Rating(1400, 30)
    r3 = Rating(1550, 100)
    r4 = Rating(1700, 300)
    rated = env.rate(r1, [(WIN, r2), (LOSS, r3), (LOSS, r4)])
    assert almost(rated) == Rating(1464.106, 151.399) # Rating(1464, 151.4)


@suite.test
def glicko2_glickman_example():
    env = Glicko2(tau=0.5)
    r1 = Rating2(1500, 200, 0.06)
    r2 = Rating2(1400, 30)
    r3 = Rating2(1550, 100)
    r4 = Rating2(1700, 300)
    rated = env.rate(r1, [(WIN, r2), (LOSS, r3), (LOSS, r4)])
    assert almost(rated) == Rating2(1464.086, 151.507, 0.05999)
    # Rating2(1464.06, 151.52, 0.05999)
