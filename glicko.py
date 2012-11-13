# -*- coding: utf-8 -*-
"""
    glicko
    ~~~~~~

    The Glicko rating system.

    :copyright: (c) 2012 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from math import exp, log, pi, sqrt
from time import mktime, time


#: The actual score for win
WIN = 1.
#: The actual score for draw
DRAW = 0.5
#: The actual score for loss
LOSS = 0.


MU = 1500
SIGMA = 350
Q = log(10) / 400


def utctime():
    return mktime(datetime.utcnow().timetuple())


class Rating(object):

    def __init__(self, mu=MU, sigma=SIGMA, rated_at=None):
        self.mu = mu
        self.sigma = sigma
        self.rated_at = rated_at

    def __repr__(self):
        c = type(self)
        args = (c.__module__, c.__name__, self.mu, self.sigma, self.rated_at)
        return '%s.%s(mu=%.3f, sigma=%.3f, rated_at=%r)' % args


class Glicko(object):

    def __init__(self, mu=MU, sigma=SIGMA, period=86400):
        self.mu = mu
        self.sigma = sigma
        self.period = period

    def create_rating(self, mu=None, sigma=None, rated_at=None):
        if mu is None:
            mu = self.mu
        if sigma is None:
            sigma = self.sigma
        return Rating(mu, sigma, rated_at)

    def g(self, rating):
        return 1 / sqrt(1 + (3 * (Q ** 2) * rating.sigma ** 2) / (pi ** 2))

    def expect_score(self, rating, other_rating, g):
        return 1. / (1 + 10 ** (g * (rating.mu - other_rating.mu) / -400.))

    def rate(self, rating, series, rated_at=None):
        if rated_at is None:
            rated_at = utctime()
        d_square_inv = 0
        difference = 0
        for actual_score, other_rating in series:
            g = self.g(other_rating)
            expected_score = self.expect_score(rating, other_rating, g)
            difference += g * (actual_score - expected_score)
            d_square_inv += (
                expected_score * (1 - expected_score) * (Q ** 2) * (g ** 2))
        denom = 1. / (rating.sigma ** 2) + d_square_inv
        mu = rating.mu + Q / denom * difference
        sigma = sqrt(1 / denom)
        return self.create_rating(mu, sigma, rated_at)

    def quality_1vs1(self, rating1, rating2):
        expected_score1 = self.expect_score(rating1, rating2, self.g(rating1))
        expected_score2 = self.expect_score(rating2, rating1, self.g(rating2))
        expected_score = (expected_score1 + expected_score2) / 2
        return 2 * (0.5 - abs(0.5 - expected_score))


def rate_1vs1(rating1, rating2, drawn=False):
    return (rate(rating1, [(DRAW if drawn else WIN, rating2)]),
            rate(rating2, [(DRAW if drawn else LOSS, rating1)]))
