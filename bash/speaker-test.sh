#!/bin/bash
set -euo pipefail

# First argument = number of channels (default 2 if not given)
CH=${1:-2}
RATE=48000

speaker-test -c"$CH" -r"$RATE" -t sine -l1 -D default 2>&1 \
  | yad --text-info --center \
        --title="Speaker Test (${CH} channels)" \
        --width=600 --height=400 \
        --tail
