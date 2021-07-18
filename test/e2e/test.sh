#!/bin/sh

CURDIR=$(dirname "$0")

$CURDIR/01-list_res.sh
$CURDIR/02-terminate.sh
$CURDIR/../../dev-stop.sh
