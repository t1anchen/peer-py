#!/bin/sh

kill -15 `lsof -n -i :5000 | awk 'NR == 2 {print $2}'`
echo "dev-stop"
