# -*- coding: utf-8 -*-
"""
    glicko
    ~~~~~~

    The Glicko rating system.

    :copyright: (c) 2012 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
import datetime
import math
import time


#: The actual score for win
WIN = 1.
#: The actual score for draw
DRAW = 0.5
#: The actual score for loss
LOSS = 0.


MU = 1500
SIGMA = 350
#: A constant which is used to standardize the logistic function to
#: `1/(1+exp(-x))` from `1/(1+10^(-r/400))`
Q = math.log(10) / 400


def utctime():
    """A function like :func:`time.time` but it uses a time of UTC."""
    return time.mktime(datetime.datetime.utcnow().timetuple())


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

    def volatilize(self, rating):
        if rating.rated_at is None:
            return rating
        sigma = min(math.sqrt(rating.sigma ** 2 + c ** 2 * t), self.sigma)
        return self.create_rating(rating.mu, sigma, rating.rated_at)

    def reduce_impact(self, rating):
        """The original form is `g(RD)`. This function reduces the impact of
        games as a function of an opponent's RD.
        """
        return (1 + (3 * (Q ** 2) * rating.sigma ** 2) / math.pi ** 2) ** -0.5

    def expect_score(self, rating, other_rating, impact):
        return 1 / (1 + 10 ** (impact * (rating.mu - other_rating.mu) / -400.))

    def rate(self, rating, series, rated_at=None):
        if rated_at is None:
            rated_at = utctime()
        d_square_inv = 0
        difference = 0
        for actual_score, other_rating in series:
            impact = self.reduce_impact(other_rating)
            expected_score = self.expect_score(rating, other_rating, impact)
            difference += impact * (actual_score - expected_score)
            d_square_inv += (
                expected_score * (1 - expected_score) *
                (Q ** 2) * (impact ** 2))
        denom = rating.sigma ** -2 + d_square_inv
        mu = rating.mu + Q / denom * difference
        sigma = math.sqrt(1. / denom)
        return self.create_rating(mu, sigma, rated_at)

    def rate_1vs1(self, rating1, rating2, drawn=False):
        return (self.rate(rating1, [(DRAW if drawn else WIN, rating2)]),
                self.rate(rating2, [(DRAW if drawn else LOSS, rating1)]))

    def quality_1vs1(self, rating1, rating2):
        expected_score1 = self.expect_score(rating1, rating2, self.g(rating1))
        expected_score2 = self.expect_score(rating2, rating1, self.g(rating2))
        expected_score = (expected_score1 + expected_score2) / 2
        return 2 * (0.5 - abs(0.5 - expected_score))
