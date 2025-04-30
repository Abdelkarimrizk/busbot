#!/bin/bash

cd /root/busbot

source /root/busbot/venv/bin/activate

echo "[Start] Starting at $(date)" >> log.txt

while true; do
	echo "[Run] $(date)" >> log.txt
	python3 bus_tracking.py
	echo "[Crash] Crashed at $(date)" >> log.txt
	sleep 5
done
