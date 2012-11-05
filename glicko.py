# -*- coding: utf-8 -*-
"""
    glicko
    ~~~~~~

    The Glicko and Glicko-2 rating system.

    :copyright: (c) 2012 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from math import e, exp, log, pi, sqrt
from time import mktime, time


#: The actual score for win
WIN = 1.
#: The actual score for draw
DRAW = 0.5
#: The actual score for loss
LOSS = 0.


MU = 1500
SIGMA = 350
VOLATILITY = 0.06
TAU = 1.0
EPSILON = 0.000001
Q = log(10) / 400


def utctime():
    return mktime(datetime.utcnow().timetuple())


class Rating(object):

    def __init__(self, mu=MU, sigma=SIGMA, rated_at=None):
        self.mu = mu
        self.sigma = sigma
        self.rated_at = rated_at

    def __repr__(self):
        args = (type(self).__name__, self.mu, self.sigma)
        front = '%s(mu=%.3f, sigma=%.3f' % args
        if self.rated_at is None:
            return front + ')'
        else:
            return front + ', rated_at=%r)' % self.rated_at


class Rating2(Rating):

    def __init__(self, mu=MU, sigma=SIGMA, volatility=VOLATILITY,
                 rated_at=None):
        super(Rating2, self).__init__(mu, sigma, rated_at)
        self.volatility = volatility


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

    def expect_score(self, rating, other_rating, g=1):
        return 1. / (1 + 10 ** (g * (rating.mu - other_rating.mu) / -400.))

    def rate(self, rating, series, rated_at=None):
        if rated_at is None:
            rated_at = utctime()
        d_square_inv = 0
        #: Glickman called it "Delta"
        difference = 0
        for actual_score, other_rating in series:
            g = self.g(other_rating)
            expected_score = self.expect_score(rating, other_rating, g)
            difference += g * (actual_score - expected_score)
            d_square_inv += expected_score * (1 - expected_score) * \
                            (Q ** 2) * (g ** 2)
        denom = 1. / (rating.sigma ** 2) + d_square_inv
        mu = rating.mu + Q / denom * difference
        sigma = sqrt(1 / denom)
        return self.create_rating(mu, sigma, rated_at)


class Glicko2(Glicko):

    def __init__(self, mu=MU, sigma=SIGMA, tau=TAU, epsilon=EPSILON,
                 period=86400):
        super(Glicko2, self).__init__(mu, sigma, period)
        self.tau = tau
        self.epsilon = epsilon

    def create_rating(self, mu=None, sigma=None, volatility=None,
                      rated_at=None):
        if mu is None:
            mu = self.mu
        if sigma is None:
            sigma = self.sigma
        if volatility is None:
            volatility = self.volatility
        return Rating2(mu, sigma, volatility, rated_at)

    scale = 173.7178

    def rescale(self, rating):
        return self.create_rating((rating.mu - 1500) / self.scale,
                                  rating.sigma / self.scale, rating.volatility)

    def rescale2(self, rating):
        return self.create_rating(self.scale * rating.mu + 1500,
                                  self.scale * rating.sigma, rating.volatility)

    def g(self, rating):
        return 1 / sqrt(1 + (3 * rating.sigma ** 2) / (pi ** 2))

    def expect_score(self, rating, other_rating, g=1):
        return 1. / (1 + exp(-g * (rating.mu - other_rating.mu)))

    def determine_volatility(self, rating, delta, variance):
        sigma = rating.sigma
        volatility = rating.volatility
        delta_squared = delta ** 2
        alpha = log(volatility ** 2)
        def f(x):
            return ((exp(x) * (delta_squared - sigma ** 2 - variance - exp(x))) / \
                   (2 * (sigma ** 2 + variance + exp(x)) ** 2)) - \
                   ((x - alpha) / (self.tau ** 2))
        if delta_squared > sigma ** 2 + variance:
            B = log(delta_squared - sigma ** 2 - variance)
        else:
            k = 1
            while f(alpha - k * sqrt(self.tau ** 2)) < 0:
                k += 1
            B = alpha - k * sqrt(self.tau ** 2)
        A = alpha
        fa, fb = f(A), f(B)
        while abs(B - A) > self.epsilon:
            C = A + (A - B) * fa / (fb - fa)
            fc = f(C)
            if fc * fb < 0:
                A = B
                fa = fb
            else:
                fa /= 2
            B = C
            fb = fc
        return e ** (A / 2)

    def rate(self, rating, series, rated_at=None):
        if rated_at is None:
            rated_at = utctime()
        d_square_inv = 0
        variance_inv = 0 #g2
        delta = 0
        rating = self.rescale(rating)
        for actual_score, other_rating in series:
            other_rating = self.rescale(other_rating)
            g = self.g(other_rating)
            expected_score = self.expect_score(rating, other_rating, g)
            g = round(g, 4)
            expected_score = round(expected_score, 3)
            variance_inv += g ** 2 * expected_score * (1 - expected_score) #g2
            delta += g * (actual_score - expected_score)
            d_square_inv += expected_score * (1 - expected_score) * \
                            (Q ** 2) * (g ** 2)
        variance = 1. / variance_inv
        delta *= variance
        denom = 1. / (rating.sigma ** 2) + d_square_inv
        mu = rating.mu + Q / denom * (delta / variance_inv)
        sigma = sqrt(1 / denom)
        volatility = self.determine_volatility(rating, delta, variance)
        sigma_star = sqrt(sigma ** 2 + volatility ** 2)
        sigma = 1 / sqrt(1 / sigma_star ** 2 + 1 / variance)
        mu = rating.mu + sigma ** 2 * (delta / variance)
        return self.rescale2(self.create_rating(mu, sigma, volatility, rated_at))



def rate_1vs1(rating1, rating2, drawn=False):
    return rate(rating1, [(DRAW if drawn else WIN, rating2)]), \
           rate(rating2, [(DRAW if drawn else LOSS, rating1)])
