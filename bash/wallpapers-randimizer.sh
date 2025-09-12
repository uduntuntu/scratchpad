#!/bin/sh
# Select 3 random pictures from folder (as many as displays)
WALLPAPERS=$(find /usr/share/backgrounds/gnome/ -type f | shuf -n 3)

# set background pictures for each display
feh --bg-fill $WALLPAPERS

