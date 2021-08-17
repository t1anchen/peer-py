#!/bin/sh

CURDIR=$(dirname "$0")

PYTHONDONTWRITEBYTECODE=1 \
$CURDIR/../../venv/bin/python $CURDIR/client.py \
--create 1 \
--training-rounds 400 \
--predicting-rounds 100

PYTHONDONTWRITEBYTECODE=1 $CURDIR/../../venv/bin/python $CURDIR/plot.py
$CURDIR/../../dev-stop.sh
