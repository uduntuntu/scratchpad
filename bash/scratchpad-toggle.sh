#!/bin/bash
TMP_WS="__scratchpad"

# Get current and previous workspace
CUR_WS=$(i3-msg -t get_workspaces | jq -r '.[] | select(.focused==true) | .name')
PREV_WS_FILE="$HOME/.local/tmp_scratchpad_prev_ws"
if [ -f "$PREV_WS_FILE" ]; then
    PREV_WS=$(cat "$PREV_WS_FILE")
else
    PREV_WS="$CUR_WS"
fi

# Check if workspace exists
i3-msg -t get_workspaces | grep "\"name\":\"$TMP_WS\"" &>/dev/null
if [ $? -eq 0 ]; then
    # Workspace exists → toggle mode
    if [ "$1" = "tab-select" ]; then
        # optional: fallback to rofi selection
        windows=$(i3-msg -t get_tree | jq -r '.. 
          | select(.type?"window":false) 
          | select(.workspace.name=="'"$TMP_WS"'") 
          | "\(.name) (\(.id))"')
        selected=$(echo "$windows" | rofi -dmenu -i -p "Scratchpad:")
        if [ -n "$selected" ]; then
            wid=$(echo "$selected" | grep -oE '\([0-9]+\)' | tr -d '()')
            i3-msg "[con_id=$wid] move workspace $PREV_WS; floating enable; focus"
            for other in $(i3-msg -t get_tree | jq '.. | select(.type?"window":false) | select(.workspace.name=="'"$TMP_WS"'") | .id'); do
                i3-msg "[con_id=$other] move scratchpad"
            done
            i3-msg "workspace $PREV_WS"
        fi
    fi
else
    # Workspace does not exist → bring scratchpad windows here
    echo "$CUR_WS" > "$PREV_WS_FILE"
    i3-msg "workspace $TMP_WS"
    idx=0
    for wid in $(i3-msg -t get_tree | jq '.. | select(.scratchpad_state=="hidden") | .id'); do
        # move window, floating, slightly offset for click
        i3-msg "[con_id=$wid] move container to workspace $TMP_WS; floating enable; move position $((50+idx*30)) $((50+idx*30))"
        idx=$((idx+1))
    done
fi

