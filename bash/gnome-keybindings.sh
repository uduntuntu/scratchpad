#!/bin/bash
# Restore GNOME custom keybindings for Screenshot and Speaker Test

# Define keybinding paths
SS_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/screenshot/"
SPK_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/speaker-test/"

# Apply the list
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['$SS_PATH', '$SPK_PATH']"

# Screenshot tool (Super+Shift+S)
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$SS_PATH name 'Screenshot tool'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$SS_PATH command 'gnome-screenshot -i'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$SS_PATH binding '<Super><Shift>s'

# Speaker Test 7.1 (Super+Shift+Ctrl+V)
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$SPK_PATH name 'Speaker Test 7.1'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$SPK_PATH command 'speaker-test -c8 -r48000 -t sine -l1 -D default'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$SPK_PATH binding '<Super><Shift><Control>v'

echo "✅ GNOME custom keybindings restored!"
echo
echo "Current custom keybindings:"
echo "---------------------------"
for KB in $SS_PATH $SPK_PATH; do
  echo "[$KB]"
  gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KB name
  gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KB command
  gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KB binding
  echo
done

