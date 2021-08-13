import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression,
    BayesianRidge,
)
from sklearn.svm import SVR, SVC
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import make_pipeline
import pickle
import codecs
import os
from log import client_logger
import json


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
    ctx["X"] = X
    ctx["y"] = y
    return ctx


def train(ctx):
    # Prepare dataset
    if ctx["offline"]:
        X_train = load_from_local(ctx["ins_id"], "X_train")
        y_train = load_from_local(ctx["ins_id"], "y_train")
    else:
        X_train = ctx["X"]
        y_train = ctx["y"]
    # X_train, X_test, y_train, y_test = train_test_split(X, y)
    ctx["X_train"] = X_train
    ctx["y_train"] = y_train
    # ctx["X_test"] = X_test
    # ctx["y_test"] = y_test

    # Training with different models
    models = {
        # "linear": LinearRegression(),
        "svc": SVC(kernel="poly"),
        "logistic": LogisticRegression(solver="liblinear"),
        "knn": KNeighborsClassifier(n_neighbors=6),
        "ann": MLPClassifier(activation="relu", alpha=0.005)
        # "bayesian": BayesianRidge(),
    }
    ctx["models"] = {}
    for model_name, model in models.items():
        # client_logger.info(f"model {model_name} is training ...")
        model.fit(X_train, y_train)
        ctx["models"][model_name] = pickle.dumps(model)

    return ctx


def cv_score(ctx):
    X_train = ctx["X_train"]
    y_train = ctx["y_train"]
    ins_id = ctx["ins_id"]
    ctx["cv_score"] = {}
    for model_name, model in ctx["models"].items():
        model = pickle.loads(model)
        model_score = cross_val_score(model, X_train, y_train)
        client_logger.info(
            f"ins {ins_id} model {model_name} cv_score {model_score}"
        )
        ctx["cv_score"][model_name] = model_score
    return ctx


def predict(ctx):
    ins_id = ctx["ins_id"]
    if ctx["offline"]:
        X_test = load_from_local(ins_id, "X_test")
        y_test = load_from_local(ins_id, "y_test")
    else:
        X_test = ctx["X_test"]
        y_test = ctx["y_test"]
    ctx["y_pred"] = {}
    ctx["score"] = {}
    ctx["roc_auc_score"] = {}
    ctx["confusion_matrix"] = {}
    for model_name, model in ctx["models"].items():
        model = pickle.loads(model)
        y_pred = model.predict(X_test)
        model_score = model.score(X_test, y_test)
        ctx["score"][model_name] = model_score
        try:
            ras = roc_auc_score(y_test, y_pred)
        except ValueError:
            ras = 0
        try:
            acc_score = accuracy_score(y_test, y_pred)
        except ValueError:
            acc_score = 0
        ctx["roc_auc_score"][model_name] = ras
        cm = confusion_matrix(y_test, y_pred)
        ctx["confusion_matrix"][model_name] = cm
        ctx["accuracy"][model_name] = acc_score
        client_logger.info(
            f"ins {ins_id} model {model_name} score {model_score} accuracy {acc_score} roc_auc_score {ras} confiusion_matrx {cm}"
        )
        y_pred = np.round(y_pred)
        ctx["y_pred"][model_name] = y_pred
    save(ctx)
    return ctx


def save(ctx):
    def gen_fname(stem, suffix=".txt"):
        prefix = f"{ctx['ins_id']}"
        os.makedirs(f"data/{prefix}", exist_ok=True)
        return f"data/{prefix}/{stem}{suffix}"

    np.savetxt(gen_fname("X_train"), ctx["X_train"])
    np.savetxt(gen_fname("y_train"), ctx["y_train"])
    np.savetxt(gen_fname("y_test"), ctx["y_test"])
    np.savetxt(gen_fname("X_test"), ctx["X_test"])
    for model in ctx["models"].keys():
        np.save(gen_fname(f"model-{model}", ".npy"), ctx["models"][model])
        for metric in ["y_pred", "score", "roc_auc_score", "confusion_matrix"]:
            stem = f"{metric}-{model}"
            y = ctx[metric][model]
            if len(np.shape(ctx[metric][model])) == 0:
                y = np.array([y])
            np.savetxt(gen_fname(stem), y)


def select_best(ctx):
    models = [k for k in ctx["models"].keys()]
    evaluations = []
    for model in models:
        evaluations.append(
            {
                "ins_id": ctx["ins_id"],
                "model": model,
                "score": ctx["score"][model],
                "roc_auc_score": ctx["roc_auc_score"][model],
            }
        )
        client_logger.info(f"ins_id = {ctx['ins_id']}")
    for evaluation in evaluations:
        evaluation["total"] = evaluation["score"] + evaluation["roc_auc_score"]
    best_score = sorted(evaluations, key=lambda item: item["total"])[-1]
    return (best_score["model"], best_score["score"])


def load_from_local(ins_id: str, selector, prefix=None, suffix=".txt"):
    if prefix is None:
        prefix = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
        )
    instances = []
    for p in os.listdir(prefix):
        if os.path.isdir(prefix + p):
            instances.append(p)
    if ins_id not in instances:
        return None
    path = os.path.join(prefix, ins_id)
    if type(selector) == str:
        path = os.path.join(path, selector, suffix)
        return np.loadtxt(path)
    elif type(selector) == list:
        ret = []
        for token in selector:
            ret.append(np.loadtxt(os.path.join(path, token, suffix)))
        return ret
    else:
        return None
