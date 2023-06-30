#!/bin/sh

PLUGIN_NAME=security_mesh

XDG_CONFIG_HOME="${XDG_CONFIG_HOME-$HOME/.config}"
KICAD_BASE="${1-$XDG_CONFIG_HOME/kicad}"
PLUGIN_DIR="$KICAD_BASE/scripting/plugins/$PLUGIN_NAME"

rm -rf "$PLUGIN_DIR"
mkdir -p "$PLUGIN_DIR"

cp -r * $PLUGIN_DIR/

