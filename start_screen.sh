#!/bin/bash

if ! screen -list | grep -q "busbot"; then
	screen -dmS busbot /root/busbot/start_busbot.sh
fi
