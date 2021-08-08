#!/bin/sh

CURDIR=$(dirname "$0")

PYTHONDONTWRITEBYTECODE=1 $CURDIR/../../venv/bin/python $CURDIR/client.py --create 0
# $CURDIR/../../dev-stop.sh
