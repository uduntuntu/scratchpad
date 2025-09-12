#!/bin/sh
xrandr \
  --output DP-4 --primary --mode 3840x2160 --pos 0x0 --rotate normal \
  --output DP-0 --mode 1920x1080 --pos 3840x0 --rotate left \
  --output DP-2 --mode 1920x1080 --pos 4920x0 --rotate normal

