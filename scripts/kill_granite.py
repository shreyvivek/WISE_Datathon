"""Run inside the container: stop any running granite_server (the container has no pkill)."""
import os, signal
for p in os.listdir("/proc"):
    if p.isdigit() and int(p) != os.getpid():
        try:
            if "granite_server" in open(f"/proc/{p}/cmdline").read():
                os.kill(int(p), signal.SIGTERM)
        except Exception:
            pass
