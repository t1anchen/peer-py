#!/bin/sh

sudo apt update && sudo apt install stress && while true;do stress --cpu 1 --io 4 --timeout $((1 + $RANDOM % 10))s;sleep 1;done
