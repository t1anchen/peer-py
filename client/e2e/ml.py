import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression,
    BayesianRidge,
)
from sklearn.svm import SVR, SVC
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import make_pipeline
import pickle
import codecs
import os
from log import client_logger


def overview(ctx):
    def detail(vn):
        v = ctx.get(vn)
        if v is not None:
            client_logger.debug(f"{vn} = {v}, shape {np.shape(v)}")
        else:
            client_logger.debug(f"{vn} = {v}")

    vns = [
        "X",
        "y",
        "X_train",
        "y_train",
        "X_test",
        "y_test",
        "cv_score",
        "score",
        "y_pred",
    ]
    client_logger.debug(f"ins_id = {ctx.get('ins_id')}")
    for vn in vns:
        detail(vn)


def configure(ctx, ins_id, opts: dict):
    start_time = opts["time"]
    interval = opts["sample_interval_nsecs"] + opts["round_interval_nsecs"]
    X = []
    uts = opts["result"]
    for i in range(len(uts)):
        X.append(start_time + i * interval)
    X = np.array([(x, y) for x, y in zip(X, uts)])
    # if "X" in ctx:
    #     X = np.vstack((ctx["X"], X))
    y = []
    for ut in np.array(uts):
        if ut >= 10:
            y.append(1)  # busy
        elif ut >= 1 and ut < 10:
            # either busy or idle
            y.append(int.from_bytes(os.urandom(1), "little") & 1)
        else:
            y.append(0)  # idle
    y = np.array(y)
    # if "y" in ctx:
    #     y = np.hstack((ctx["y"], y))
    ctx = {"ins_id": ins_id, "X": X, "y": y}
    return ctx


def train(ctx):
    # Prepare dataset
    X_train = ctx["X"]
    y_train = ctx["y"]
    # X_train, X_test, y_train, y_test = train_test_split(X, y)
    ctx["X_train"] = X_train
    ctx["y_train"] = y_train
    # ctx["X_test"] = X_test
    # ctx["y_test"] = y_test

    # Training with different models
    models = {
        "linear": LinearRegression(),
        "svr": SVR(),
        "logistic": LogisticRegression(),
        "bayesian": BayesianRidge(),
    }
    ctx["models"] = {}
    for model_name, model in models.items():
        client_logger.info(f"model {model_name} is training ...")
        model.fit(X_train, y_train)
        ctx["models"][model_name] = pickle.dumps(model)

    return ctx


def cv_score(ctx):
    X_train = ctx["X_train"]
    y_train = ctx["y_train"]
    ctx["cv_score"] = {}
    for model_name, model in ctx["models"].items():
        model = pickle.loads(model)
        client_logger.info(f"model {model_name} is scoring ...")
        model_score = cross_val_score(model, X_train, y_train)
        ctx["cv_score"][model_name] = model_score
    return ctx


def predict(ctx):
    X_test = ctx["X_test"]
    y_test = ctx["y_test"]
    ctx["y_pred"] = {}
    ctx["score"] = {}
    for model_name, model in ctx["models"].items():
        model = pickle.loads(model)
        client_logger.info(f"model {model_name} is predicting ...")
        y_pred = model.predict(X_test)
        client_logger.info(f"y_pred of model {model_name} is {y_pred}")
        model_score = model.score(X_test, y_test)
        client_logger.info(f"model {model_name} score is {model_score}")
        ctx["score"][model_name] = model_score
        y_pred = np.round(y_pred)
        ctx["y_pred"][model_name] = y_pred
    return ctx
