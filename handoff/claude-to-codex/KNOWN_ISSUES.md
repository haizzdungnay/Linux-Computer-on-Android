# Known Issues and Open Risks

> **Cập nhật 2026-11-19:** lỗi APT/pending theme đã hết khi giao dịch cũ tự hoàn tất. Giao diện, app và Home Resume đã được kiểm chứng theo [báo cáo mới](DESKTOP_COMPLETION_2026-11-19.md). Vấn đề hiện tại là Firefox tab crash do font trong sandbox PRoot; dùng NetSurf cho HTTPS cơ bản. Các stop/gate M1–M2 bên dưới là lịch sử trước yêu cầu triển khai mới; giới hạn bảo vệ Ubuntu, `:1`, dữ liệu và phiên chưa xác minh vẫn giữ.

**Evidence cutoff:** 2026-11-19. Device/process/package observations are time-sensitive; do not treat as current without an authorized, read-only recheck.

## Stop-before-action items

1. **Interrupted Debian APT transaction.** Core-app installation completed. A later appearance transaction was interrupted while active. Last read-only audit found APT lock held, Papirus package in broken status, multiple theme/font packages unpacked but not configured, and `fontconfig`/`libc-bin` triggers pending. PRoot PID 2081 still showed the appearance `apt-get` invocation at the last process snapshot; exact child/lock ownership was not resolved. No recovery ran. Do not start APT/dpkg, configure packages, remove locks, or signal a process until the package transaction is known quiescent and the owner explicitly authorizes a specific recovery. See `DEVICE_STATE.md`.
2. **Multiple live sessions and unknown ownership.** Termux:X11 `:2` and `:3` existed, with multiple PRoot/XFCE experiments. A second older `xfwm4` and unrelated PRoot shells existed. PID observations are volatile and do not establish session ownership. Do not stop/restart/signal any process or delete sockets/locks.
3. **Current GUI not visually verified.** The user confirmed a manual desktop test on 2026-11-18. On 2026-11-19 process and X11 property checks did not prove current rendered UI or touch usability. No current screenshot or visual confirmation was obtained.
4. **M1/M2 gates remain open.** M1 is NOT VERIFIED: direct current-session confirmation and a safely isolated cold-start test were not completed. The running session must not be stopped merely to create a test state. M2 is NOT STARTED under the approved pivot plan; do not apply appearance changes until M1 gate is met.

## Package and app status

- Core GUI package transaction installed the requested app batch; package presence was checked before the appearance transaction. GUI launch, file associations, PDF/ZIP opening, browser HTTPS/download, and sustained resource use remain untested.
- `firefox-esr`, `openssh-client`, `python3-venv`, `unzip`, `zip`, and `rsync` were absent in the last package query. This is historical state, not a fresh query.
- Appearance packages are not known-good. Do not claim Noto fonts, Arc theme, or Papirus are configured/usable.
- APT core-app batch installed 125 packages, fetched 87.8 MB, and reported ~412 MB additional disk use. Atril/Engrampa pulled substantial WebKit/GStreamer dependencies. Review simulated dependency changes before any future install.
- A package setup emitted `procps: Applying updated sysctl configuration` and `grep: /proc/1/environ: No such file or directory`; no global Android display change was intended. This was not followed by a security/system-setting audit.

## Resume and lifecycle

- `scripts/minimal-launcher/linux-resume.sh` is resume-only. A prior direct test succeeded against then-running XFCE `:2`; it does not start X11/XFCE or survive reboot by itself. Home-screen placement/tap success is user-reported, not independently verified.
- `scripts/xfce-components.sh` differs from the observed working profile (`/root/.local/linux-desktop/config` vs `/root/.ld-test/xfce-config`) and its trap sends TERM to tracked children. Do not run against the active display.
- `scripts/desktop.py` and wrappers are legacy lifecycle experiments, not validated session control. Source has process ownership/reconciliation risks and wrappers can affect existing state. Do not invoke `start-linux.sh`, `stop-linux.sh`, or `status-linux.sh` on the tablet.
- Android launcher source expects fixed `$HOME/.local/linux-desktop/{start,stop,status}-linux.sh` paths, while workspace wrappers are under `scripts/`. Source action enum has `START`, `STOP`, `STATUS`, not `RESUME`. APK package is absent from tablet; standalone launcher is not the working shortcut.
- Historical test count from prior report (36 total, 17 failures, 1 error) was cited but not freshly reproduced. Current tests appear inconsistent with manager source/API; no test suite ran for this handoff. Do not use historical results as current test status.

## Backup and evidence limits

- XFCE tar backup SHA-256: `debf6dc6510598e9044bc3b1fe54d034613d3a1711d9f958c014264a8c31ce13`. It contains saved configuration files only and was copied while XFCE might write; it is not an atomic or complete session backup. Do not restore it over a live profile.
- Saved profile has default/empty theme and icon-theme settings, two panels, and no wallpaper property. This describes archived files, not necessarily all in-memory/current UI state.
- Android global display was temporarily changed to `1600x1068` earlier, then reset. Last observed values were physical `2136x3200`, density `440`; never change them for this work.
- `com.termux.widget` was force-stopped during earlier troubleshooting despite a broad no-process-termination boundary. Do not repeat. It was later present in package inventory.
- Workspace has no Git metadata. No reliable working-tree diff or historical file baseline exists. Preserve artifacts; do not clean build caches, temp APKs, or files.
