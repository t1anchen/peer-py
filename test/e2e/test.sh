#!/bin/sh

CURDIR=$(dirname "$0")

$CURDIR/../../venv/bin/python $CURDIR/testci.py
$CURDIR/../../dev-stop.sh
