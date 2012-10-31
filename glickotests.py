# -*- coding: utf-8 -*-
from attest import Tests, assert_hook, raises

from glicko import *


suite = Tests()


@suite.test
def glickman_example():
    env = Glicko()
    print 53670.85
    print (0.9955**2)*(0.639)*(1-0.639)
    print (0.9531**2)*(0.432)*(1-0.432)
    print (0.7242**2)*(0.303)*(1-0.303)
    print 1. /((0.0057565 ** 2) * ((0.9955**2)*(0.639)*(1-0.639) + \
                              (0.9531**2)*(0.432)*(1-0.432) + \
                              (0.7242**2)*(0.303)*(1-0.303)))
    r1 = Rating(1500, 200)
    r2 = Rating(1400, 30)
    r3 = Rating(1550, 100)
    r4 = Rating(1700, 300)
    assert env.rate(r1, [(WIN, r2), (LOSE, r3), (LOSE, r4)]) == \
           Rating(1464.106, 151.399)
    #assert env.rate(r1, [(WIN, r2), (LOSE, r3), (LOSE, r4)]) == Rating(1464, 151.4)
