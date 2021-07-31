from flask import Flask
from flask import jsonify
from .learn import dummy
import platform
from time import time
import subprocess
from random import randint
from .resource import *
from flask import g
from flask_caching import Cache
from .ssh import get_conn, disconn

app = Flask(__name__)
app.config.from_mapping({
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
})
cache = Cache(app)


@app.route("/")
def node_info():
    return {
        'machine': platform.machine(),
        'node': platform.node(),
        'platform': platform.platform(),
        'processor': platform.processor(),
        'system': platform.system()
    }


@app.route("/client")
def client_info():
    return {
        'mode': 'client',
        **node_info()
    }


@app.route("/server")
def server_info():
    return {
        'mode': 'server',
        **node_info()
    }


@app.route("/task/cpu/<int:timeout>")
def cpu_task(timeout=30):
    start_time = time()
    app.logger.info(f"cpu task started at {start_time}")
    cpu_task_log = ''
    proc = subprocess.Popen("openssl speed -elapsed", shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        "timeout": is_timeout
    }


@app.route("/resource/scale/<int:n_ins>")
def resource_scale(n_ins):
    start_time = time()
    dryrun = False
    new_instances = instance_create(n_ins, dryrun)
    end_time = time()
    with app.app_context():
        saved_instances = cache.get('instances')
        if saved_instances is None:
            saved_instances = {}
        for instance in new_instances:
            saved_instances[instance] = {
                'state': 'creating'
            }
        cache.set('instances', saved_instances)
    return {
        "name": "resource scale",
        "elapsed": end_time - start_time,
        "result": new_instances
    }


@app.route("/resource/<ins_id>/public_ip")
def resource_public_ip(ins_id):
    start_time = time()
    ret = instance_public_ip(ins_id)
    end_time = time()
    with app.app_context():
        saved_instances = cache.get('instances')
        if saved_instances is not None:
            saved_instances[ins_id]['public_ip'] = ret
            saved_instances[ins_id]['state'] = 'running'
        cache.set('instances', saved_instances)
    return {
        "name": "resource public ip",
        "elapsed": end_time - start_time,
        'result': ret
    }


@app.route("/resource")
def resource_all():
    saved_instances = cache.get('instances')
    if saved_instances is None:
        saved_instances = instance_desc()
        cache.set('instances', saved_instances)
    return {
        "name": "resources",
        "result": saved_instances
    }


@app.route("/resource/<ins_id>", methods=['DELETE'])
def resource_terminate(ins_id):
    start_time = time()
    ret = instance_terminate(ins_id)
    end_time = time()
    with app.app_context():
        saved_instances = cache.get('instances')
        if saved_instances is not None:
            saved_instances[ins_id]['state'] = 'terminating'
        cache.set('instances', saved_instances)
    return {
        "name": "resource terminate",
        "elapsed": end_time - start_time,
        "result": ret
    }


@app.route("/resource/<ins_id>/cpu")
def resource_cpu(ins_id):
    hostname = 'localhost'
    start_time = time()
    with app.app_context():
        saved_instances = cache.get('instances')
        if saved_instances is not None:
            hostname = saved_instances[ins_id]['public_ip']
    conn = get_conn(hostname)
    _, stdout, stderr = conn.exec_command('cat /proc/stat | grep cpu')
    stdout_str = stdout.read().decode()
    stderr_str = stderr.read().decode()
    disconn(conn)
    end_time = time()
    return {
        "name": "resource cpu",
        "result": stdout_str,
        "error": stderr_str
    }


@app.route("/learn")
def dummy_learn():
    return {
        "name": "dummy learn by scikit-learn",
        "result": dummy()
    }
