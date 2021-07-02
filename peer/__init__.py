from flask import Flask
from flask import jsonify
from .learn import dummy

app = Flask(__name__)


@app.route("/")
def hello_world():
    return {
        "seq": [i for i in range(10)],
        "name": "meow"
    }


@app.route("/learn")
def dummy_learn():
    return {
        "name": "dummy learn by scikit-learn",
        "result": dummy()
    }
