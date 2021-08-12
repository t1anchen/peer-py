#!/bin/sh

CURDIR=$(dirname "$0")

PYTHONDONTWRITEBYTECODE=1 \
$CURDIR/../../venv/bin/python $CURDIR/client.py \
--create 0 \
--training-rounds 80 \
--predicting-rounds 20
# $CURDIR/../../dev-stop.sh
