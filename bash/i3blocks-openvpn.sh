#!/bin/bash
# i3blocks OpenVPN status + IP

ip=$(ip -4 addr show tun0 2>/dev/null | awk '/inet / {print $2}' | cut -d/ -f1)

if [ -n "$ip" ]; then
    echo "🔒 $ip"
    echo "🔒 $ip"
    echo "#00FF00"
else
    echo "🔓 OFF"
    echo "🔓 OFF"
    echo "#FF0000"
fi

