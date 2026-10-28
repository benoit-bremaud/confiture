#!/bin/sh
while true; do
  "$HOME/pi3cam/bin/python" "$HOME/pi3cam/pi3cam.py" >> "$HOME/pi3cam/pi3cam.log" 2>&1
  sleep 10
done
