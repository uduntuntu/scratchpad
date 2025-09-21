#!/bin/sh
# Toggle all outputs to "DP-4", "DP-2", "DP-0" … workspaces and back

STATEFILE="${XDG_RUNTIME_DIR:-/tmp}/i3-minimized.state"
DEBUG=0
[ "$1" = "--debug" ] && DEBUG=1

notify() {
    if [ $DEBUG -eq 1 ]; then
        notify-send "i3-minimized" "$*"
    fi
}

if [ -f "$STATEFILE" ]; then
    # --- Restore ---
    while read -r out ws; do
        [ -n "$ws" ] || continue
        notify "Restoring '$ws' on $out"
        i3-msg "focus output $out; workspace $ws" >/dev/null
    done < "$STATEFILE"
    rm -f "$STATEFILE"
    notify "Restored workspaces"
else
    # --- Save current and minimize ---
    : > "$STATEFILE"
    for out in $(i3-msg -t get_outputs | jq -r '.[] | select(.active) | .name'); do
        ws=$(i3-msg -t get_workspaces | jq -r ".[] | select(.output==\"$out\" and .visible) | .name")
        if [ -z "$ws" ]; then
            notify "WARN: $out has no visible workspace"
            continue
        fi
        echo "$out $ws" >> "$STATEFILE"
        notify "Saving '$ws' on $out → workspace '$out'"

        # 1. Fokus outputille
        i3-msg "focus output $out" >/dev/null
        # 2. Luo ja fokusoi uusi workspace nimellä output
        i3-msg "workspace $out" >/dev/null
    done
    notify "Switched to minimized mode"
fi

