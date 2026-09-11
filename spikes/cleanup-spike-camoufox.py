#!/usr/bin/env python3
"""One-off: remove the stray spike directory from the /opt/data root.

Per AGENTS.md, one-off scripts do not belong at the /opt/data root; these were
copied into the project at spikes/ before removal.
"""
import os
import shutil

p = "/opt/data/spike_camoufox"
if os.path.isdir(p):
    shutil.rmtree(p)
    print("removed stray spike dir:", p)
else:
    print("already absent:", p)

for junk in ("/tmp/tc_err3.log", "/tmp/tc_err4.log", "/tmp/tc_err5.log"):
    if os.path.exists(junk):
        os.remove(junk)
        print("removed temp log:", junk)
