# OREZ login trace wrapper

The live-only OREZ Wayland entry invokes this small wrapper before the exact
native Plasma D-Bus helper. It records a start marker, a limited set of
non-secret session-environment values, and the child's numeric exit status
through the system journal. It does not dump the environment, command line
secrets, process memory, credentials, or user files.

The wrapper invokes only
`/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed
/usr/bin/startplasma-wayland`. It returns the child's exact status; it does
not turn failure into success, change authentication, grant privileges,
enable automatic login, change compositor settings, or select another
desktop. Invalid wrapper arguments fail closed.

This is diagnostic instrumentation, not a login fix. In the next disposable
default-menu UEFI boot, compare these journal markers with SDDM's session
start/exit timestamps. If `wrapper_started` is absent, inspect SDDM's session
script boundary. If present, `plasma_session_child_exit` identifies the
helper's returned status. The compositor's independent exit must still be
captured. Remove this wrapper after root cause is established and normal login
passes repeated tests.

The wrapper is live-only and intentionally absent from the installed package
allowlist. No physical disk or real owner credential is involved.
