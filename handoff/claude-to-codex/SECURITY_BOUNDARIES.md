# Security and Preservation Boundaries

> **Phạm vi mới 2026-11-19:** người dùng đã cho phép hoàn thiện giao diện và cài ứng dụng trên phiên `:2`. Công việc đó đã thực hiện, APT sạch và Home Resume được xác nhận; xem [báo cáo triển khai](DESKTOP_COMPLETION_2026-11-19.md). Các câu cấm mọi cài đặt/chỉnh cấu hình bên dưới mô tả nhiệm vụ bàn giao cũ. Việc đã được giao không mở rộng sang reset, Ubuntu, `:1`, GPU, reboot, APK, xóa khóa hoặc tác động tiến trình chưa xác minh.

**As of:** 2026-11-19. These boundaries record the project owner's explicit limits and observed risk. Handoff documentation does not expand permission.

## Never assume permission

- Do not stop, start, restart, signal, force-stop, or kill any process or session. Includes PRoot, XFCE, Termux:X11, Termux:Widget, APT/dpkg and unknown shells.
- Do not delete sockets, lock files, PID files, state files, caches, APKs, build artifacts, snapshots, or other workspace/device files as cleanup.
- Do not reboot, reset Android, or change Android display resolution/density, display configuration, SELinux, bootloader, root status, or permissions.
- Do not alter Ubuntu, display `:1`, running display `:2`, display `:3`, or any experimental/unknown session.
- Do not install/remove/upgrade Debian or Termux packages, recover dpkg, or install an APK without authorization for that exact action. APT state was interrupted and last observed locked/broken.
- Do not modify, rebuild, sign, install, or replace existing/custom Android APKs. No launcher package is installed; debug APK on disk is not authorization to install.
- Do not treat prior approval, command success, a task plan, or this handoff as permission for a different action. Ask before any irreversible, outward-facing or live-state operation.

## Protected device state

- Android tablet: Xiaomi Pad 7 Pro (`f422eebd`), Termux app UID `10528`.
- Keep Debian 13 and Ubuntu containers intact. PRoot root is not Android root and is not an Android security boundary; Linux GUI processes run under Termux's Android app identity.
- Preserve all Termux data and settings. Do not edit `termux.properties` or broaden `allow-external-apps`.
- Preserve live Termux:X11 `:2` and `:3`, XFCE/PRoot experiments, unknown shells, and their shared `/tmp` resources. Process names, ancestry snippets, PIDs, or display numbers alone do not prove ownership. PIDs are volatile and reusable.
- Never change Android global display size/density. Last observed physical values were `2136x3200` and density `440`; separate X11 virtual geometry `1280x960` is not Android global resolution.

## Package-manager boundary

Last read-only audit after user interruption found an APT process and lock, `papirus-icon-theme` in a broken state, packages unpacked but unconfigured, and pending triggers. This is time-sensitive and not a current lock-owner assertion. Do not:

- invoke `apt`, `apt-get`, `dpkg --configure`, package removal, or repair while status is unresolved;
- remove a lock file, signal the observed PID, kill a process, or start a competing package transaction;
- infer that interruption means apt exited cleanly or the package DB is safe.

A future operator needs explicit user authorization for a specific recovery. Inspect current state without mutation; if package-manager activity remains, allow legitimate completion. If uncertain, stop and report; do not improvise recovery.

## Script and command boundaries

- `scripts/desktop.py` plus `start-linux.sh`, `stop-linux.sh`, `status-linux.sh` are legacy lifecycle code. Do not execute against tablet sessions. Even status may involve manager state/locks.
- `scripts/xfce-components.sh` is not the historically working command. Its config root differs and its trap sends TERM to tracked children. Do not run it against live `:2`.
- `scripts/minimal-launcher/linux-resume.sh` validates and opens an existing XFCE session only. Prior success does not grant permission to launch a new server/session or weaken validation.
- ADB and PRoot commands are not automatically read-only. Check exact command semantics, quoting, target identity, and side effects first. Avoid broad `ps`/`pgrep` pipelines followed by action. A historical `proot-distro ps` call may prune stale registry entries; do not assume it is observational.
- Read-only checks can still expose private paths, environment variables, command lines, logs, or user data. Collect the minimum required and redact secrets from handoff.

## Configuration and backups

- Existing profile: `/root/.ld-test/xfce-config`; do not overwrite or restore into it while active.
- Snapshot: `snapshots/xfce-config-20261119T103201/xfce-config.snapshot.tar`. Saved files only; live-copied while XFCE could write, so not atomic and does not capture in-memory state. Do not delete, replace, or treat as complete rollback.
- Any future authorized experiment should use a new, unique, private profile and a separately reviewed rollback plan. Never silently overwrite later user edits during rollback.
- Workspace is not a Git repo. There is no Git diff/clean-tree proof. Do not run destructive cleanup or initialize/version files without user request.

## Permission and acceptance gates

- M1 remains NOT VERIFIED until owner confirms the current visible session and safe cold-start evidence exists; do not terminate current session to obtain it.
- M2 remains NOT STARTED until M1 gate and separate required package/config approvals. Do not use existing package interruption as a reason to continue install.
- Historical UI tests are not current visual confirmation. Do not label current usability PASS from process output, package presence or previous-day confirmation.
- Cold start, resume, reboot recovery, widget placement and standalone APK are distinct outcomes. State precisely which one was exercised.
