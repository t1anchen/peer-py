#!/bin/sh

CURDIR=$(dirname "$0")

PYTHONDONTWRITEBYTECODE=1 \
$CURDIR/../../venv/bin/python $CURDIR/client.py \
--create 2 \
--training-rounds 40 \
--predicting-rounds 10
# $CURDIR/../../dev-stop.sh
