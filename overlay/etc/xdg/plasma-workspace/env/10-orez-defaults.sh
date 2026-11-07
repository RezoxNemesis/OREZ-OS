#!/bin/sh
# OREZ system defaults (look-and-feel, colours, Start-menu favourites).
# Put /etc/xdg/orez first in the XDG config search path; per-user settings in
# ~/.config still win, so every choice stays changeable in Settings.
case ":${XDG_CONFIG_DIRS:-}:" in
  *:/etc/xdg/orez:*) ;;
  *) export XDG_CONFIG_DIRS="/etc/xdg/orez:${XDG_CONFIG_DIRS:-/etc/xdg}" ;;
esac
