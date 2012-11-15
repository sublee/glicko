# -*- coding: utf-8 -*-
"""
    glicko2
    ~~~~~~~

    The Glicko2 rating system.

    :copyright: (c) 2012 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
import math

from glicko import Glicko, WIN, DRAW, LOSS, MU, SIGMA, Q


VOLATILITY = 0.06
TAU = 1.0
EPSILON = 0.000001


class Rating(object):

    def __init__(self, mu=MU, sigma=SIGMA, volatility=VOLATILITY):
        self.mu = mu
        self.sigma = sigma
        self.volatility = volatility

    def __repr__(self):
        c = type(self)
        args = (c.__module__, c.__name__, self.mu, self.sigma, self.volatility)
        return '%s.%s(mu=%.3f, sigma=%.3f, volatility=%.3f)' % args


class Glicko2(Glicko):

    def __init__(self, mu=MU, sigma=SIGMA, volatility=VOLATILITY, tau=TAU,
                 epsilon=EPSILON):
        self.mu = mu
        self.sigma = sigma
        self.volatility = volatility
        self.tau = tau
        self.epsilon = epsilon

    def create_rating(self, mu=None, sigma=None, volatility=None):
        if mu is None:
            mu = self.mu
        if sigma is None:
            sigma = self.sigma
        if volatility is None:
            volatility = self.volatility
        return Rating(mu, sigma, volatility)

    def scale_down(self, rating, ratio=173.7178):
        mu = (rating.mu - self.mu) / ratio
        sigma = rating.sigma / ratio
        return self.create_rating(mu, sigma, rating.volatility)

    def scale_up(self, rating, ratio=173.7178):
        mu = rating.mu * ratio + self.mu
        sigma = rating.sigma * ratio
        return self.create_rating(mu, sigma, rating.volatility)

    def reduce_impact(self, rating):
        """The original form is `g(RD)`. This function reduces the impact of
        games as a function of an opponent's RD.
        """
        return 1 / math.sqrt(1 + (3 * rating.sigma ** 2) / (math.pi ** 2))

    def expect_score(self, rating, other_rating, impact):
        return 1. / (1 + math.exp(-impact * (rating.mu - other_rating.mu)))

    def determine_volatility(self, rating, difference, variance):
        """Determines new volatility."""
        sigma = rating.sigma
        difference_squared = difference ** 2
        # 1. Let a = ln(s^2), and define f(x)
        alpha = math.log(rating.volatility ** 2)
        def f(x):
            """This function is twice the conditional log-posterior density of
            sigma, and is the optimality criterion.
            """
            tmp = sigma ** 2 + variance + math.exp(x)
            a = math.exp(x) * (difference_squared - tmp) / (2 * tmp ** 2)
            b = (x - alpha) / (self.tau ** 2)
            return a - b
        # 2. Set the initial values of the iterative algorithm.
        a = alpha
        if difference_squared > sigma ** 2 + variance:
            b = math.log(difference_squared - sigma ** 2 - variance)
        else:
            k = 1
            while f(alpha - k * math.sqrt(self.tau ** 2)) < 0:
                k += 1
            b = alpha - k * math.sqrt(self.tau ** 2)
        # 3. Let fA = f(A) and f(B) = f(B)
        f_a, f_b = f(a), f(b)
        # 4. While |B-A| > e, carry out the following steps.
        # (a) Let C = A + (A - B)fA / (fB-fA), and let fC = f(C).
        # (b) If fCfB < 0, then set A <- B and fA <- fB; otherwise, just set
        #     fA <- fA/2.
        # (c) Set B <- C and fB <- fC.
        # (d) Stop if |B-A| <= e. Repeat the above three steps otherwise.
        while abs(b - a) > self.epsilon:
            c = a + (a - b) * f_a / (f_b - f_a)
            f_c = f(c)
            if f_c * f_b < 0:
                a, f_a = b, f_b
            else:
                f_a /= 2
            b, f_b = c, f_c
        # 5. Once |B-A| <= e, set s' <- e^(A/2)
        return math.exp(1) ** (a / 2)

    def rate(self, rating, series):
        # Step 2. For each player, convert the rating and RD's onto the
        #         Glicko-2 scale.
        rating = self.scale_down(rating)
        # Step 3. Compute the quantity v. This is the estimated variance of the
        #         team's/player's rating based only on game outcomes.
        # Step 4. Compute the quantity difference, the estimated improvement in
        #         rating by comparing the pre-period rating to the performance
        #         rating based only on game outcomes.
        d_square_inv = 0
        variance_inv = 0
        difference = 0
        for actual_score, other_rating in series:
            other_rating = self.scale_down(other_rating)
            impact = self.reduce_impact(other_rating)
            expected_score = self.expect_score(rating, other_rating, impact)
            variance_inv += impact ** 2 * expected_score * (1 - expected_score)
            difference += impact * (actual_score - expected_score)
            d_square_inv += (
                expected_score * (1 - expected_score) *
                (Q ** 2) * (impact ** 2))
        difference /= variance_inv
        variance = 1. / variance_inv
        denom = rating.sigma ** -2 + d_square_inv
        mu = rating.mu + Q / denom * (difference / variance_inv)
        sigma = math.sqrt(1 / denom)
        # Step 5. Determine the new value, Sigma', ot the volatility. This
        #         computation requires iteration.
        volatility = self.determine_volatility(rating, difference, variance)
        # Step 6. Update the rating deviation to the new pre-rating period
        #         value, Phi*.
        sigma_star = math.sqrt(sigma ** 2 + volatility ** 2)
        # Step 7. Update the rating and RD to the new values, Mu' and Phi'.
        sigma = 1 / math.sqrt(1 / sigma_star ** 2 + 1 / variance)
        mu = rating.mu + sigma ** 2 * (difference / variance)
        # Step 8. Convert ratings and RD's back to original scale.
        return self.scale_up(self.create_rating(mu, sigma, volatility))
