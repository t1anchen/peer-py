#!/bin/sh

CURDIR=$(dirname "$0")

PYTHONDONTWRITEBYTECODE=1 \
$CURDIR/../../venv/bin/python $CURDIR/client.py \
--create 2 \
--training-rounds 160 \
--predicting-rounds 40

PYTHONDONTWRITEBYTECODE=1 $CURDIR/../../venv/bin/python $CURDIR/plot.py
$CURDIR/../../dev-stop.sh
