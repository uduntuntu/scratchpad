#!/bin/sh
iwctl station wlan0 show \
  | sed 's/\x1b\[[0-9;]*m//g' \
  | sed 's/^ *//;s/  */ /g' \
  | awk '
    /^Connected network/ {ssid=$3}
    /^IPv4 address/      {ip=$3}
    /^RSSI/              {rssi=$2}
    END {
        if (!ssid) { print "📴 offline"; exit }
        bar="▂▄▆█"
        if      (rssi > -50) lvl=4
        else if (rssi > -60) lvl=3
        else if (rssi > -70) lvl=2
        else if (rssi > -80) lvl=1
        else lvl=0
        printf(" %s %s %s %s dBm\n", substr(bar,1,lvl), ssid, ip, rssi)
    }'

