#!/bin/bash
until ping -c1 google.com &>/dev/null 2>&1; do
  echo "DNS not ready, retrying..."; sleep 2
done
echo "DNS is working!"
