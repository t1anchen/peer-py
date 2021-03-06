from flask import Flask, request
from flask import jsonify
import platform
from time import time, sleep
import subprocess
from random import randint
from .resource import *
from flask import g
from flask_caching import Cache
from .ssh import get_conn, disconn
from datetime import datetime
import numpy as np
from flask.logging import default_handler
import logging

app = Flask(__name__)
app.config.from_mapping(
    {
        "DEBUG": True,
        "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
        "CACHE_DEFAULT_TIMEOUT": 3600 * 2,
    }
)

default_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] [server_side:%(module)s:%(funcName)s:L%(lineno)d] %(message)s"
    )
)
cache = Cache(app)


@app.route("/")
def node_info():
    return {
        "machine": platform.machine(),
        "node": platform.node(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "system": platform.system(),
    }


@app.route("/client")
def client_info():
    return {"mode": "client", **node_info()}


@app.route("/server")
def server_info():
    return {"mode": "server", **node_info()}


@app.route("/task/cpu/<int:timeout>")
def cpu_task(timeout=30):
    start_time = time()
    app.logger.info(f"cpu task started at {start_time}")
    cpu_task_log = ""
    proc = subprocess.Popen(
        "openssl speed -elapsed",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    is_timeout = False
    try:
        outs, errs = proc.communicate(timeout)
    except subprocess.TimeoutExpired:
        is_timeout = True
        proc.kill()
        outs, errs = proc.communicate()
    app.logger.info(outs.decode())
    app.logger.info(errs.decode())
    end_time = time()
    app.logger.info(f"cpu task ended at {end_time}")
    elapsed = (end_time - start_time).seconds
    app.logger.info(f"elasped {elapsed} seconds")
    return {
        "name": "cputask",
        "result": min(elapsed, timeout),
        "unit": "seconds",
        "timeout": is_timeout,
    }


@app.route("/resource/scale/<int:n_ins>")
def resource_scale(n_ins):
    start_time = time()
    is_dry_run = False
    new_instances = instance_create(n_ins, is_dry_run)
    end_time = time()
    with app.app_context():
        saved_instances = cache.get("instances")
        if saved_instances is None:
            saved_instances = {}
        for instance in new_instances:
            saved_instances[instance] = {"state": "creating"}
            cache.set(instance, {"state": "creating"})
        cache.set("instances", saved_instances)
    return {
        "name": "resource scale",
        "elapsed": end_time - start_time,
        "result": new_instances,
    }


@app.route("/resource/<ins_id>/public_ip")
def resource_public_ip(ins_id):
    start_time = time()
    ret = instance_public_ip(ins_id)
    end_time = time()
    with app.app_context():
        saved_instances = cache.get("instances")
        if saved_instances is not None:
            saved_instances[ins_id]["public_ip"] = ret
            saved_instances[ins_id]["state"] = "running"
            cache.set("instances", saved_instances)
        ins = cache.get(ins_id)
        if ins is not None:
            ins["public_ip"] = ret
            ins["state"] = "running"
            cache.set(ins_id, ins)
    return {
        "name": "resource public ip",
        "elapsed": end_time - start_time,
        "result": ret,
    }


@app.route("/resource")
def resource_all():
    with app.app_context():
        saved_instances = instance_desc()
        cache.set("instances", saved_instances)
        for ins_id in saved_instances.keys():
            ins = saved_instances[ins_id]
            ins["state"] = "running"
            cache.set(ins_id, ins)
    return {"name": "resources", "result": saved_instances}


@app.route("/resource/<ins_id>", methods=["DELETE"])
def resource_terminate(ins_id):
    start_time = time()
    ret = instance_terminate(ins_id)
    end_time = time()
    with app.app_context():
        saved_instances = cache.get("instances")
        if saved_instances is not None:
            saved_instances[ins_id]["state"] = "terminating"
            cache.set("instances", saved_instances)
    return {
        "name": "resource terminate",
        "elapsed": end_time - start_time,
        "result": ret,
    }


@app.route("/resource/<ins_id>/cpu", methods=["POST"])
def resource_cpu(ins_id):
    req_ctx: dict = request.get_json(force=True) or {}
    print(req_ctx)
    sample_interval_nsecs = req_ctx.get("sample_interval_nsecs", 3)
    round_interval_nsecs = req_ctx.get("round_interval_nsecs", 1)
    rounds = req_ctx.get("rounds", 5)
    # app.logger.info(cache)
    ins = cache.get(ins_id)
    cpu_ut = ins.get("cpu_ut", [])

    ut_test = {
        "time": time(),
        "sample_interval_nsecs": sample_interval_nsecs,
        "round_interval_nsecs": round_interval_nsecs,
        "rounds": rounds,
    }
    result = []

    # Prepare connection
    hostname = "localhost"
    if ins is not None:
        hostname = ins["public_ip"]
    conn = get_conn(hostname)

    # Shake
    for i in range(rounds):
        sleep(round_interval_nsecs)
        cpu_usage = _resource_cpu(
            conn, ins_id, sample_interval_nsecs, (i, rounds)
        )["result"]
        result.append(cpu_usage)
    ut_test["result"] = result

    # Disconn
    disconn(conn)

    cpu_ut.append(ut_test)
    ins["cpu_ut"] = cpu_ut
    cache.set(ins_id, ins)
    return {"name": "resource cpu sampling", "result": ut_test}


def _resource_cpu(conn, ins_id, interval_nsecs, progress):
    def cpu_sample(conn):
        _, stdout, stderr = conn.exec_command("cat /proc/stat | grep cpu")
        stdout_str = stdout.read().decode()
        stderr_str = stderr.read().decode()
        cpu_total_line = stdout_str.split("\n")[0]
        time_tokens = cpu_total_line.split()[1:]
        cpu_total_time = sum(int(t) for t in time_tokens)
        idle_time = int(time_tokens[3])
        return cpu_total_time, idle_time

    current_round, total_rounds = progress
    start_time = time()
    total1, idle1 = cpu_sample(conn)
    # app.logger.debug(f"total1 = {total1}, idle1 = {idle1}")
    sleep(interval_nsecs)
    total2, idle2 = cpu_sample(conn)
    # app.logger.debug(f"total2 = {total2}, idle2 = {idle2}")
    cpu_usage = (
        ((total2 - idle2) - (total1 - idle1)) * 1.0 / (total2 - total1) * 100.0
    )

    end_time = time()
    app.logger.info(
        f"[{current_round+1}/{total_rounds}] instance {ins_id} cpu ut {cpu_usage}% sample by {interval_nsecs} secs"
    )
    return {"name": "resource cpu", "result": cpu_usage}


@app.route("/cache")
def cache_list():
    ret = {}
    saved_instances = cache.get("instances")
    ret["instances"] = saved_instances
    for ins_id in saved_instances.keys():
        ret[ins_id] = cache.get(ins_id)
    return {"name": "cache list", "result": ret}


@app.route("/resource/<ins_id>/run", methods=["POST"])
def resource_run(ins_id):
    req_ctx = request.get_json(force=True)
    print(req_ctx)
    cmd = req_ctx["cmd"]
    hostname = "localhost"
    start_time = time()
    with app.app_context():
        saved_instances = cache.get("instances")
        if saved_instances is not None:
            hostname = saved_instances[ins_id]["public_ip"]
    conn = get_conn(hostname)
    _, stdout, stderr = conn.exec_command(cmd)
    stdout_str = stdout.read().decode()
    stderr_str = stderr.read().decode()
    disconn(conn)
    end_time = time()
    return {"name": "resource run", "result": stdout_str, "error": stderr_str}


@app.route("/pre_processing")
def pre_processing():
    saved_instances = cache.get("instances")
    X_train = {}
    if saved_instances is not None:
        active_instances = [k for k in saved_instances.keys()]
        for ins_id in active_instances:
            ins = cache.get(ins_id)
            X_train[ins_id] = []
            for ut in ins["cpu_ut"]:
                configure(cache, ins_id, ut)
    return {"name": "pre processing"}
