#!/bin/sh

choice=$(wpctl status \
  | awk '/Sinks:/{flag=1;next}/Sources:/{flag=0}flag && /[0-9]+\./' \
  | sed -E 's/^[^0-9]*([0-9]+\.)/\1/' \
  | rofi -dmenu -p "Audio output")

if [ -n "$choice" ]; then
    id=$(echo "$choice" | cut -d. -f1)
    name=$(echo "$choice" | cut -d. -f2- | sed 's/^[[:space:]]*//')
    wpctl set-default "$id"
    notify-send "🔊 Default sink:" "$name"
fi
