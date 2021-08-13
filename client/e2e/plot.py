import os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve, plot_roc_curve
from pprint import pprint
from log import client_logger
import matplotlib.pyplot as plt
import pickle


def prepare(ctx):
    instances = []
    models = ["svc", "logistic", "knn", "ann"]
    ctx["models"] = models
    prefix = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    ctx["prefix"] = prefix
    for p in os.listdir(prefix):
        if os.path.isdir(os.path.join(prefix, p)):
            instances.append(p)
    ctx["instances"] = instances
    for ins_id in instances:
        ins = {}
        ins["ins_id"] = ins_id
        client_logger.info(f"loading {ins_id}")
        ins["X_train"] = np.loadtxt(f"data/{ins_id}/X_train.txt")
        ins["y_train"] = np.loadtxt(f"data/{ins_id}/y_train.txt")
        ins["X_test"] = np.loadtxt(f"data/{ins_id}/X_test.txt")
        ins["y_test"] = np.loadtxt(f"data/{ins_id}/y_test.txt")
        ins["y_pred"] = {}
        ins["models"] = {}
        for model in models:
            ins["y_pred"][model] = np.loadtxt(
                f"data/{ins_id}/y_pred-{model}.txt"
            )
            ins["models"][model] = pickle.loads(
                np.load(f"data/{ins_id}/model-{model}.npy")
            )
        ctx[ins_id] = ins
    return ctx


def plotting_roc_curve(ctx):
    instances = ctx["instances"]
    models = ctx["models"]
    prefix = ctx["prefix"]
    for ins_id in instances:
        client_logger.info(f"plotting {ins_id}")
        ins = ctx[ins_id]
        X_test = ins["X_test"]
        y_test = ins["y_test"]
        ins["roc_curve"] = {}
        fig, ax_ = plt.subplots()
        for model in models:
            y_pred = ins["y_pred"][model]
            ins["roc_curve"][model] = roc_curve(y_test, y_pred)
            clf = ins["models"][model]
            plot_roc_curve(clf, X_test, y_test, ax=ax_)
        ctx[ins_id] = ins
        fig.savefig(os.path.join(prefix, f"{ins_id}/roc_curve.png"))
    return ctx


def main():
    ctx = {}
    ctx = prepare(ctx)
    ctx = plotting_roc_curve(ctx)


main()
