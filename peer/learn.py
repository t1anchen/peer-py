import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_validate


def dummy():
    X, y = make_regression(n_samples=1000, random_state=0)
    lr = LinearRegression()
    result = cross_validate(lr, X, y)
    return result['test_score'].tolist()
