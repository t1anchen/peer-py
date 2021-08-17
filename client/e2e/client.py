import requests
import time
import json
from ml import *
import sys
import os
import argparse
from log import client_logger
from collections import Counter

ENDPOINT = "http://localhost:5000"
# client_cache = {}
# DRY_RUN_MODE = os.environ["DRY_RUN_MODE"] == "1"


def create(opts: dict):
    n_create = opts["create"]
    if n_create > 0:
        client_logger.info("Creating new instances")
        res = requests.get(ENDPOINT + f"/resource/scale/{n_create}").json()
        instances = res["result"]
        client_logger.debug(instances)
        client_logger.info("Waiting for initializing new instances ...")
        wait(90)
        for instance in instances:
            pub_ret = requests.get(
                ENDPOINT + f"/resource/{instance}/public_ip"
            ).json()


def list_running(opts: dict):
    # get active instance
    client_logger.info(f"Getting info for active instances ...")
    res = requests.get(ENDPOINT + "/resource").json()
    opts["active_instances"] = [
        k
        for k in res["result"].keys()
        if res["result"][k]["state"] == "running"
    ]
    client_logger.debug(res)
    return opts


def train_sample(opts):
    active_instances = opts["active_instances"]
    sample_interval_nsecs = opts["sample_interval_nsecs"]
    round_interval_nsecs = opts["round_interval_nsecs"]
    rounds = opts["training_rounds"]
    opts["train_samples"] = {}
    if opts["offline"]:
        return list_cache(opts)
    for instance in active_instances:
        res = requests.post(
            ENDPOINT + f"/resource/{instance}/cpu",
            data=json.dumps(
                {
                    "sample_interval_nsecs": sample_interval_nsecs,
                    "round_interval_nsecs": round_interval_nsecs,
                    "rounds": rounds,
                }
            ),
            headers={"content-type": "application/json"},
        ).json()
        opts["train_samples"][instance] = res["result"]
    opts = list_cache(opts)
    for instance in active_instances:
        cpu_uts = opts[instance].get("cpu_ut", [])
        cpu_uts.append(opts["train_samples"][instance])
        opts[instance]["cpu_ut"] = cpu_uts
    return opts


def list_cache(opts):
    # list cache
    # global client_cache
    res = requests.get(ENDPOINT + "/cache").json()
    client_logger.info(f"cache = {res['result']}")
    for k, v in res["result"].items():
        opts[k] = v
    return opts


def model_train(opts: dict):
    # global client_cache
    # client_logger.info(f"opts = {opts}")
    active_instances = opts["active_instances"]
    client_logger.debug(f"opts = {opts}")
    for ins_id in active_instances:
        client_logger.info(f"Training model for For instance {ins_id}")
        ins = opts[ins_id]
        client_logger.debug(f"ins = {ins}")
        ctx = {"ins_id": ins_id, "offline": opts["offline"]}
        if opts["offline"]:
            ctx["offline"] = True
        else:
            for ut in ins["cpu_ut"]:
                ctx = configure(ctx, ins_id, ut)
        ctx = train(ctx)
        ctx = cv_score(ctx)
        # overview(ctx)
        opts[ins_id]["ml_ctx"] = ctx


def predict_sample(opts):
    # global client_cache
    active_instances = opts["active_instances"]
    sample_interval_nsecs = opts["sample_interval_nsecs"]
    round_interval_nsecs = opts["round_interval_nsecs"]
    rounds = opts["predicting_rounds"]
    is_dry_run = opts["dry_run"]
    client_logger.info(f"Getting new data from remote ...")
    ret = {}
    for instance in active_instances:
        res = requests.post(
            ENDPOINT + f"/resource/{instance}/cpu",
            data=json.dumps(
                {
                    "sample_interval_nsecs": sample_interval_nsecs,
                    "round_interval_nsecs": round_interval_nsecs,
                    "rounds": rounds,
                }
            ),
            headers={"content-type": "application/json"},
        ).json()
        opts[instance]["cpu_ut"].append(res["result"])


def model_predict(opts: dict):
    # global client_cache
    is_dry_run = opts["dry_run"]
    active_instances = opts["active_instances"]
    if not opts["offline"]:
        predict_sample(opts)
    client_logger.info(f"Predicting ...")
    for ins_id in active_instances:
        cpu_ut_size = len(opts[ins_id]["cpu_ut"])
        client_logger.info(f"cpu_ut_size = {cpu_ut_size}")
        ut = opts[ins_id]["cpu_ut"][-1]
        ctx = opts[ins_id]["ml_ctx"]
        new_ctx = configure({}, ins_id, ut)
        ctx["X_test"] = new_ctx["X"]
        ctx["y_test"] = new_ctx["y"]
        ctx = predict(ctx)
        # overview(ctx)
        # best_algo, best_score = [
        #     (k, v)
        #     for k, v in sorted(
        #         ctx["mean_accuracy_score"].items(), key=lambda item: abs(np.sum(item[1]) - 1)
        #     )
        # ][0]
        best_algo, best_score = select_best(ctx)
        y_pred = ctx["y_pred"][best_algo]
        client_logger.info(
            f"ins_id = {ins_id} best_algo = {best_algo}, best_score = {best_score}, y_pred = {y_pred}"
        )
        if is_idle(y_pred):
            if not is_dry_run:
                client_logger.info(f"instance {ins_id} is terminating")
                ter_ret = requests.delete(
                    ENDPOINT + f"/resource/{ins_id}"
                ).json()
            else:
                client_logger.info(f"instance {ins_id} will be terminated")


def terminate_all(opts: dict):
    active_instances = opts["active_instances"]
    is_dry_run = opts["dry_run"]
    for instance in active_instances:
        if not is_dry_run:
            client_logger.info(f"instance {instance} is terminating")
            ter_ret = requests.delete(ENDPOINT + f"/resource/{instance}").json()
        else:
            client_logger.info(f"instance {instance} will be terminated")


def wait(timeout: int):
    click = 0
    while click < timeout:
        localtime = time.localtime()
        print(f"remaining {(timeout - click):02d} secs", end="\r")
        click += 1
        time.sleep(1)
    print()


def is_idle(y_pred):
    counted = {k: v for k, v in Counter(y_pred).items()}
    labels = sorted(k for k in counted.keys())
    if len(labels) > 1 and counted[0] > counted[1]:
        return True
    elif len(labels) == 1 and 0 in labels:
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--offline", action="store_true", default=False)
    parser.add_argument("--sample-interval-nsecs", type=float, default=0.2)
    parser.add_argument("--round-interval-nsecs", type=int, default=0)
    parser.add_argument("--training-rounds", type=int, default=80)
    parser.add_argument("--predicting-rounds", type=int, default=20)
    opts = vars(parser.parse_args())
    client_logger.info("==== total start ====")
    start_time = time.time()
    create(opts)

    if opts["create"] > 0:
        client_logger.info("simulating stress")
        wait(90)

    opts = list_running(opts)
    opts = train_sample(opts)

    model_train(opts)
    model_predict(opts)
    end_time = time.time()
    client_logger.info(f"==== total elapsed {end_time - start_time}s ====")

    # if opts["enable_termination"]:
    #     opts = terminate_all(opts)


main()
