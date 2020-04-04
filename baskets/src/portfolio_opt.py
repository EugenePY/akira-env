# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy.optimize import minimize


def weight_sum(w_):
    return np.sum(w_) - 1


def portfolio_return(w_, expected_return):
    return np.dot(w_.T, expected_return)


def portfolio_variance(w_, cov_m):
    return np.dot(w_.T, cov_m).dot(w_)


def fromCov2Coef(cov_m, sigma):
    p = 1./sigma
    p = p.reshape(1, p.shape[0]) * p.reshape(p.shape[0], 1)
    cov_m = cov_m * p
    return cov_m


def hist_coef(cov_list):
    res = [fromCov2Coef(cov,
                        np.sqrt(cov.values[np.diag_indices(7)].astype(np.float)))
           for i, cov in cov_list]
    return res


def optimize_portfolio(inital_weight, covariance_matrix, implied_rate,
                       expected_return):
    num_currenies = expected_return.shape[0]
    weights_cons = {"type": "eq", "fun": lambda w_: weight_sum(w_)}
    carried_cons = {"type": "ineq",
                    "fun": lambda w_: portfolio_return(w_, implied_rate)}
    expected_return_cons = {"type": "ineq",
                            "fun": lambda w_: portfolio_return(w_, expected_return)}
    weights_bound = [(-0.5, 0.5)] * num_currenies

    result = minimize(lambda w_: portfolio_variance(w_, covariance_matrix),
                      inital_weight,
                      constraints=(weights_cons, carried_cons,
                                   expected_return_cons),
                      bounds=weights_bound)
    return result


def hedge_portfolio_variance(w_, cov_m):
    w = np.append(-1, w_)  # short postion on TWD
    return np.dot(w.T, cov_m).dot(w)


def hedge_portfolio_return(w_, expected_return):
    w = np.append(-1, w_)  # short postion on TWD
    return np.dot(w.T, expected_return)


def hedge_portfolio(inital_weight, covariance_matrix, implied_rate,
                    expected_return):
    # Note first col is the target currency
    s, h = sp.linalg.eigh(covariance_matrix)

    num_currenies = expected_return.shape[0] - 1
    carried_cons = {"type": "ineq",
                    "fun": lambda w_: hedge_portfolio_return(w_, implied_rate)}
    weights_bound = [(-0.5, 0.5)] * num_currenies
    result = minimize(lambda w_: hedge_portfolio_variance(w_, covariance_matrix),
                      inital_weight, constraints=(carried_cons),
                      bounds=weights_bound)
    return result
