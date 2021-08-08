import requests
import time
import json
from ml import *
import sys
import os
import argparse
import logging

ENDPOINT = "http://localhost:5000"
client_cache = {}
# DRY_RUN_MODE = os.environ["DRY_RUN_MODE"] == "1"


def init_logger():
    client_logger = logging.getLogger("client")
    client_logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    fh = logging.FileHandler("client.log")
    ch.setLevel(logging.DEBUG)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    client_logger.addHandler(ch)
    client_logger.addHandler(fh)
    return client_logger


client_logger = init_logger()


def create(opts: dict):
    n_create = opts["create"]
    if n_create > 0:
        client_logger.info("[client:create] Creating new instances")
        res = requests.get(ENDPOINT + f"/resource/scale/{n_create}").json()
        instances = res["result"]
        client_logger.info(instances)
        client_logger.info(
            "[client:create] Waiting for initializing new instances ..."
        )
        wait(90)
        for instance in instances:
            pub_ret = requests.get(
                ENDPOINT + f"/resource/{instance}/public_ip"
            ).json()


def list_running(opts: dict):
    # get active instance
    client_logger.info(
        f"[client:list_running] Getting info for active instances ..."
    )
    res = requests.get(ENDPOINT + "/resource").json()
    opts["active_instances"] = [
        k
        for k in res["result"].keys()
        if res["result"][k]["state"] == "running"
    ]
    client_logger.info(res)
    return opts


def train_sample(opts):
    active_instances = opts["active_instances"]
    for instance in active_instances:
        res = requests.post(
            ENDPOINT + f"/resource/{instance}/cpu",
            data=json.dumps(
                {
                    "sample_interval_nsecs": 0.5,
                    "round_interval_nsecs": 1,
                    "rounds": 10,
                }
            ),
            headers={"content-type": "application/json"},
        ).json()
        res = requests.post(
            ENDPOINT + f"/resource/{instance}/cpu",
            data=json.dumps(
                {
                    "sample_interval_nsecs": 0.5,
                    "round_interval_nsecs": 0,
                    "rounds": 20,
                }
            ),
            headers={"content-type": "application/json"},
        ).json()
        # res = requests.post(
        #     ENDPOINT + f"/resource/{instance}/cpu",
        #     data=json.dumps(
        #         {
        #             "sample_interval_nsecs": 0.5,
        #             "round_interval_nsecs": 0,
        #             "rounds": 30,
        #         }
        #     ),
        #     headers={"content-type": "application/json"},
        # ).json()
    print(res)
    return list_cache(opts)


def list_cache(opts):
    # list cache
    global client_cache
    res = requests.get(ENDPOINT + "/cache").json()
    client_cache = res["result"]
    with open("sample.dat", "w+") as f:
        f.write(str(client_cache))
    return opts


def model_train(opts: dict):
    global client_cache
    client_logger.info(f"[client:model_train] client_cache = {client_cache}")
    active_instances = opts["active_instances"]
    # train
    client_logger.info(
        f"[client:model_train] Training models for active instaces ..."
    )
    for ins_id in active_instances:
        client_logger.info(f"For instance {ins_id}")
        ins = client_cache[ins_id]
        ctx = {}
        for ut in ins["cpu_ut"]:
            ctx = configure(ctx, ins_id, ut)
        ctx = train(ctx)
        ctx = cv_score(ctx)
        overview(ctx)
        client_cache[ins_id]["ml_ctx"] = ctx


def model_predict(opts: dict):
    global client_cache
    active_instances = opts["active_instances"]
    is_dry_run = opts["dry_run"]
    client_logger.info(
        f"[client:model_predict] Getting new data from remote ..."
    )
    for instance in active_instances:
        res = requests.post(
            ENDPOINT + f"/resource/{instance}/cpu",
            data=json.dumps(
                {
                    "sample_interval_nsecs": 0.5,
                    "round_interval_nsecs": 0,
                    "rounds": 20,
                }
            ),
            headers={"content-type": "application/json"},
        ).json()

    client_logger.info(f"[client:model_predict] Predicting ...")
    for ins_id in active_instances:
        ut = client_cache[ins_id]["cpu_ut"][-1]
        ctx = client_cache[ins_id]["ml_ctx"]
        new_ctx = configure({}, ins_id, ut)
        ctx["X_test"] = new_ctx["X"]
        ctx["y_test"] = new_ctx["y"]
        ctx = predict(ctx)
        overview(ctx)
        max_algo, max_score = [
            (k, v)
            for k, v in sorted(
                ctx["score"].items(), key=lambda item: abs(np.sum(item[1]) - 1)
            )
        ][0]
        client_logger.info(
            f"ins_id = {ins_id} max_algo = {max_algo}, max_score = {max_score}"
        )
        y_pred = ctx["y_pred"][max_algo]
        if np.sum(np.unique(y_pred)) == 0:
            if not is_dry_run:
                client_logger.info(
                    f"[client:model_predict] instance {instance} is terminating"
                )
                ter_ret = requests.delete(
                    ENDPOINT + f"/resource/{instance}"
                ).json()
            else:
                client_logger.info(
                    f"[client:model_predict] instance {instance} will be terminated"
                )


def terminate_all(opts: dict):
    active_instances = opts["active_instances"]
    is_dry_run = opts["dry_run"]
    for instance in active_instances:
        if not is_dry_run:
            client_logger.info(
                f"[client:terminate_all] instance {instance} is terminating"
            )
            ter_ret = requests.delete(ENDPOINT + f"/resource/{instance}").json()
        else:
            client_logger.info(
                f"[client:terminate_all] instance {instance} will be terminated"
            )


def wait(timeout: int):
    click = 0
    while click < timeout:
        localtime = time.localtime()
        print(f"[client:wait] remaining {(timeout - click):02d} secs", end="\r")
        click += 1
        time.sleep(1)
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", type=int, default=0)
    parser.add_argument("--dry-run", type=bool)
    opts = vars(parser.parse_args())
    client_logger.info("[client:main] total start")
    start_time = time.time()
    create(opts)

    client_logger.info("[client:main] simulating stress")
    wait(90)

    opts = list_running(opts)
    opts = train_sample(opts)

    model_train(opts)
    model_predict(opts)
    end_time = time.time()
    client_logger.info(f"[client:main] total elapsed {end_time - start_time}")

    # opts = terminate_all(opts)


main()
