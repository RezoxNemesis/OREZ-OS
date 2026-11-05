# Performance targets and honest hardware limits

Owner requirement: a responsive normal desktop with **6 GiB RAM**, and excellent
practical performance on the actual Ryzen 5 5600 / RTX 3050 6 GB / 16 GiB DDR4 /
NVMe system. These are release targets, not measurements already achieved by a
complete installed OS. Native container tests omit boot/login and many services.

## Budgets to qualify before release

| Scenario | Target and measurement |
|---|---|
| Fresh desktop idle | Target ≤1.5 GiB resident working set after 5 minutes; report kernel/cache separately and record actual enabled services |
| 6 GiB normal desktop | Terminal, file manager, settings, modest browser workload and 1080p local video remain interactive without OOM kills; measure p95 input/application response and dropped video frames |
| Launcher/settings interactions | Target p95 ≤150 ms input-to-visible-response on the target display; API response time alone is not this measurement |
| 1080p playback | Target <1% dropped frames during a 10-minute sample; report codec, resolution, backend, CPU/GPU utilization and audio underruns |
| 16 GiB development workload | Browser, editor, builds and an optional bounded Android guest remain usable; record workload, wall time and sustained memory pressure rather than claiming unlimited multitasking |
| Sustained reliability | No application/desktop hangs, OOM kills or session loss in an 8-hour mixed-use soak, then a multi-day pilot; record failures and recovery |
| Gaming | Per-game frame-time percentiles and 1% lows at stated settings/resolution, compared on the same hardware/driver/power state; no invented FPS targets |

Targets may be adjusted only from recorded hardware evidence with an explicit
decision. They are not guaranteed service levels. Browser tabs, unbounded apps,
large video projects, models or Android games can exhaust any fixed RAM budget.

## Engineering approach

- Keep boot/login paths small. No automatic AI models, Android guest, file
  indexer storm, updater duplication or phone services without a visible user
  setting. Android, AI and decorative effects must remain optional.
- Use the supported kernel and distro NVIDIA packages. Verify hardware video
  decoding and compositor acceleration per codec/application; do not infer them
  from a successful software-rendered window.
- Offer opaque panels/reduced motion and an explicit performance profile. Avoid
  polling and animations in idle UI. Respect laptop/desktop power and thermal
  limits; record actual temperatures/throttling on the target PC.
- Qualify a bounded zram/swap policy and memory-pressure handling in disposable
  VMs before enabling it. Preserve useful caches; do not add periodic cache
  purges, unsafe sysctls, blanket security-service removal or permanent maximum
  clocks as supposed optimizations.
- Treat the RTX 3050's **6 GB VRAM** as a real limit. Correct drivers, supported
  acceleration and workload sizing can recover wasted performance. Software
  cannot create VRAM, guarantee access to fused-off units, remove firmware power
  limits safely, or turn this card into a higher-tier GPU. No firmware flashing,
  voltage unlock or unverified overclock is part of OREZ defaults.
- Measure 6 GiB/16 GiB profiles in actual booted VMs, then the physical PC. A
  container cap/CPU software renderer is useful component evidence but cannot
  validate Windows comparisons or real game/GPU performance.

## Current code and evidence

`orezctl performance` provides a one-shot read-only report of available RAM,
CPU/memory/I/O pressure and the available native power profile. It adds no
resident monitor or tuning daemon. `orezctl power` opens KDE Power Management;
the owner chooses supported power settings and can restore them there.

The Android manager chooses 2 GiB on hosts below 8 GiB, otherwise 3 GiB, with
an explicit 2/3/4 GiB selector and 1/2/4 virtual CPU validation. Starting a guest
requires enough available memory to leave at least 2 GiB for the host. This is
a conservative admission check, not a guarantee against later memory pressure.
The runtime is never started automatically. Security controls remain enabled.

**Measurement correction:** this workspace's rootless Docker daemon reports
`MemoryLimit=false`, `CgroupDriver=none`. Previous 2/4 GiB fixtures and the new
6 GiB request were configured values, not enforced limits. Native interactions
remain real, but none proves a low-RAM full OS. Visible cgroup data describe the
shared 16 GiB environment. The runner now records enforcement and refuses a
resource-qualification run when `OREZ_REQUIRE_RESOURCE_LIMITS=1` and enforcement
is unavailable. A 2 GiB allocation and D-Bus responsiveness samples are component
stress evidence only; they do not establish input-to-photon latency or FPS.

Next optimization gates: booted-VM idle service inventory; measured pressure and
zram/swap experiments; compositor/video acceleration; consistent frame-time,
energy and thermal comparisons on the real PC; suspend/resume and 8-hour soak.
Keep the fastest configuration only when correctness, security, energy and
regression results support it. No optimization gains are claimed yet.
