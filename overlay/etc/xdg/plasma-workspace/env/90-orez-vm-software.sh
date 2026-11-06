#!/bin/sh
# OREZ OS test-only KWin software compositor experiment.
# Sourced before the Plasma session; visible at this path and documented.
# Normal live USB and installed OREZ never set this variable.
case " $(cat /proc/cmdline 2>/dev/null) " in
  *" orez.verify=1 "*)
    export KWIN_COMPOSE=Q
    ;;
esac
