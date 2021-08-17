#!/bin/sh

CURDIR=$(dirname "$0")

PYTHONDONTWRITEBYTECODE=1 \
$CURDIR/../../venv/bin/python $CURDIR/client.py \
--dry-run \
--create 0 \
--training-rounds 40 \
--predicting-rounds 10

PYTHONDONTWRITEBYTECODE=1 $CURDIR/../../venv/bin/python $CURDIR/plot.py
$CURDIR/../../dev-stop.sh
