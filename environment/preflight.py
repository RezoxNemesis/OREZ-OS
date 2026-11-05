#!/usr/bin/env python3
"""Read-only inventory; never fabricates KVM, GPU, networking or Android support."""
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

tools = ['docker','qemu-system-x86_64','qemu-img','xorriso','mksquashfs','java','node','npm','python3','vlc','brave-browser','glxinfo','vulkaninfo']
report = {
    'architecture':platform.machine(), 'uid':os.getuid(),
    'tools':{name:shutil.which(name) for name in tools},
    'kvm_device_exists':Path('/dev/kvm').exists(),
    'kvm_usable_by_current_user':os.access('/dev/kvm',os.R_OK|os.W_OK),
    'graphics_render_nodes':[str(p) for p in Path('/dev/dri').glob('renderD*')],
    'nvidia_devices':[str(p) for p in Path('/dev').glob('nvidia[0-9]*')],
    'free_workspace_gib':round(shutil.disk_usage('.').free/2**30,1),
    'host_security_policy_unchanged':True,
    'limits':'Presence is not a successful VM boot, sandboxed browser launch, NVIDIA test or Android Play Store install.'
}
if shutil.which('docker'):
    try:
        info = json.loads(subprocess.check_output(['docker','info','--format','{{json .}}'], text=True, timeout=15))
        report['docker_resource_enforcement'] = {k:info.get(k) for k in ['MemoryLimit','CgroupDriver','CgroupVersion','Warnings']}
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report['docker_resource_enforcement'] = {'unverified':type(error).__name__}
report['cgroup_scope'] = 'Visible hierarchy may be shared; do not infer child limits from these values.'
for name in ['memory.max','memory.current','cpu.max']:
    path=Path('/sys/fs/cgroup')/name
    if path.exists():report[name]=path.read_text().strip()
print(json.dumps(report,indent=2))
