import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.model_selection import cross_validate
import pickle
import codecs


def dummy():
    X, y = make_regression(n_samples=1000, random_state=0)
    lr = LinearRegression()
    result = cross_validate(lr, X, y)
    return result["test_score"].tolist()


def overview(cache, ins_id):
    learn_ctx = cache.get("learn")
    ins_learn: dict = learn_ctx.get(ins_id)
    if "model" in ins_learn:
        del ins_learn["model"]
    ins_learn["X_train"] = ins_learn["X_train"].tolist()
    ins_learn["y_train"] = ins_learn["y_train"].tolist()
    return ins_learn


def configure(cache, ins_id, opts: dict):
    start_time = opts["time"]
    interval = opts["sample_interval_nsecs"] + opts["round_interval_nsecs"]
    X = []
    uts = opts["result"]
    for i in range(len(uts)):
        X.append(start_time + i * interval)
    X = np.array([(x, y) for x, y in zip(X, uts)])
    y_train = []
    for ut in np.array(uts):
        if ut > 1:
            y_train.append(1)
        else:
            y_train.append(0)
    y_train = np.array(y_train)
    learn_ctx = cache.get("learn") or {}
    learn_ctx[ins_id] = {"X_train": X, "y_train": y_train}
    cache.set("learn", learn_ctx)
    return X, uts


def train(cache, ins_id, model_name):
    model = LinearRegression()
    learn_ctx = cache.get("learn")
    ins_learn = learn_ctx.get(ins_id)
    X = ins_learn.get("X_train")
    y_train = ins_learn.get("y_train")
    model.fit(X, y_train)
    ins_learn["model"] = pickle.dumps(model)
    learn_ctx[ins_id] = ins_learn
    cache.set("learn", learn_ctx)
    return model


def score(cache, ins_id):
    learn_ctx = cache.get("learn")
    ins_learn = learn_ctx.get(ins_id)
    model = pickle.loads(ins_learn.get("model"))
    X = ins_learn.get("X_train")
    y_train = ins_learn.get("y_train")
    model_score = model.score(X, y_train)
    ins_learn["score"] = model_score
    learn_ctx[ins_id] = ins_learn
    cache.set("learn", learn_ctx)
    return model_score


def predict(model, X):
    return list(model.predict(X))
