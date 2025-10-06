#!/bin/bash
set -euo pipefail

TMP_WS="scratchpad-windows"
PREV_WS_FILE="$HOME/.local/tmp_scratchpad_prev_ws"

# Current workspace
CUR_WS=$(i3-msg -t get_workspaces | jq -r '.[] | select(.focused==true) | .name')
echo "$CUR_WS" > "$PREV_WS_FILE"

# --- Check if overview workspace exists and is focused ---
if i3-msg -t get_workspaces | grep "\"name\":\"$TMP_WS\"" | grep "\"focused\":true" &>/dev/null; then
    # --- Close overview: collect all windows inside the overview workspace ---
    mapfile -t scratchpad_windows < <(
        i3-msg -t get_tree \
        | jq -r '.. | objects | select(.type=="workspace" and .name=="'"$TMP_WS"'") 
            | .. | objects | select(.window != null) | .id'
    )

    # Move each back to scratchpad
    for wid in "${scratchpad_windows[@]}"; do
        i3-msg "[con_id=$wid] focus; move scratchpad"
    done

    exit 0
fi

# --- Show overview workspace ---
# Collect all floating scratchpad windows (orphans/off-screen)
mapfile -t scratchpad_windows < <(
    i3-msg -t get_tree \
    | jq -r '.. | objects | select(.floating=="user_on" and .window != null) | .id'
)

num_windows=${#scratchpad_windows[@]}
if (( num_windows == 0 )); then
    notify-send "Scratchpad" "No floating scratchpad windows found"
    exit 0
fi

# Switch/create overview workspace
i3-msg "workspace $TMP_WS"
sleep 0.1

# Step 1: move all windows floating to overview workspace
for wid in "${scratchpad_windows[@]}"; do
    i3-msg "[con_id=$wid] move container to workspace $TMP_WS; floating enable"
done

# Step 2: attach windows into horizontal tiling
first=true
for wid in "${scratchpad_windows[@]}"; do
    if [ "$first" = true ]; then
        i3-msg "[con_id=$wid] focus; floating disable"
        first=false
        last_wid=$wid
    else
        i3-msg "[con_id=$last_wid] focus; splith"
        i3-msg "[con_id=$wid] focus; floating disable"
        last_wid=$wid
    fi
done

# Step 3: apply layout toggle for neat overview
i3-msg -t run_command "layout toggle split"


