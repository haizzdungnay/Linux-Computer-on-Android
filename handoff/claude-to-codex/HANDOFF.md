# Project Technical Handoff: Claude Code to Codex

> **Cập nhật sau triển khai, 2026-11-19:** XFCE `:2` đã áp dụng Arc-Dark/Papirus/Whisker/dock; APT hoàn tất và audit sạch. Người dùng xác nhận menu cảm ứng, kéo cửa sổ và Home Resume. NetSurf HTTPS đạt; Firefox ESR có lỗi font trong sandbox. Xem [báo cáo mới nhất và rollback](DESKTOP_COMPLETION_2026-11-19.md). Phần còn lại của file giữ nguyên làm lịch sử bàn giao trước triển khai.

**Prepared:** 2026-11-19  
**Workspace:** `C:\Users\PC\linux-desktop`  
**Device:** Xiaomi Pad 7 Pro, HyperOS / Android 16, Termux + PRoot-Distro + Debian 13 ARM64 + Termux:X11 + XFCE.

## Goal

Deliver a practical portable Linux workstation for reading/reviewing code and GitHub changes; basic debugging, linting/testing, Git/Python/SSH/terminal work; browser/cloud AI access; and files/documents. Desired UI: customized Linux Mint XFCE style, landscape/touch friendly, with reliable one-tap Android Resume and eventually explicit cold-start behavior. Requirements differ by milestone: do not represent Resume as cold start, reboot survival, or standalone APK integration.

## Executive status

- Debian 13 ARM64 and XFCE 4.20 are already installed. A desktop did render and accept touch/input on the physical tablet on 2026-11-18, according to prior user-confirmed tests in `TEST_REPORT.md`.
- At final read-only device audit on 2026-11-19, Termux:X11 server `:2` and `:3` and multiple XFCE/PRoot processes remained. `:2` still had the expected software GL, compositor-off XFCE component processes and X11 WM property in earlier verification. Do not infer current visual UI from processes alone. No screen evidence or user visual confirmation was obtained during this handoff.
- Current known-good profile is `/root/.ld-test/xfce-config`; relevant running processes use `DISPLAY=:2`, `LIBGL_ALWAYS_SOFTWARE=1`. Keep current session intact.
- A private tar backup of saved config exists at `snapshots/xfce-config-20261119T103201/xfce-config.snapshot.tar`, SHA-256 `debf6dc6510598e9044bc3b1fe54d034613d3a1711d9f958c014264a8c31ce13`. It contains saved files only, not in-memory state, and was live-copied while XFCE could write; not an atomic snapshot. Do not restore over a running profile.
- Termux:Widget v0.15.0 package is installed. Script and custom PNG icon exist at expected paths; a live resume-script test previously passed. User later said Home-screen shortcut setup succeeded. That statement is user-reported, not independently rechecked in this handoff. No cold-start path is verified.
- **A package install started during this handoff was interrupted by the user.** Core XFCE apps finished installing. Next `apt-get -y --no-install-recommends install arc-theme papirus-icon-theme fonts-noto fonts-noto-cjk` was rejected/interrupted while active. Fresh subsequent read-only audit showed an apt process still running, several appearance packages unpacked but unconfigured, Papirus in a broken status, pending triggers and APT lock. This is a real outstanding filesystem/package-database change. No clean recovery was performed. Do not start another APT operation or claim a clean package DB until the process and lock are safely resolved under user authorization.
- Desktop visual design and daily app launch/HTTPS workflows are not accepted. Existing configuration remains the original saved config; no theme/wallpaper/panel configuration was intentionally written in this handoff.
- Android Kotlin project and debug APK output exist, but launcher package is not installed. APK is not the currently working one-tap path.
- Workspace is not a Git repository. No commit/push made.

## Technical architecture and proven behavior

Android runs Termux under app UID `10528`; PRoot-Distro provides Debian ARM64 filesystem/process view while Debian processes still execute with Termux's Android UID. PRoot is not a security boundary. Termux:X11 has one viewer activity attached to its server session. Debian X11 access requires shared `/tmp` (`proot-distro login --isolated --shared-tmp debian`) and `DISPLAY=:2`.

Historical debugging found hardware GL/Mesa `libgallium` initialization can stall under PRoot + Termux:X11. The known workaround is `LIBGL_ALWAYS_SOFTWARE=1` and start XFWM with `xfwm4 --compositor=off`; do not experiment with GPU acceleration or re-enable the compositor as part of recovery. On 2026-11-18 a manual component startup under isolated D-Bus succeeded; users confirmed menu touch, terminal echo, and window drag. Exact historical command provenance and the distinction from current scripts are in `WORKING_COMMANDS.md`.

`scripts/xfce-components.sh` is a reference, not production-ready: it creates config/cache/run/log under `/root/.local/linux-desktop`, which differs from the known profile; it starts components in its own dbus session; it uses a trap that sends TERM to tracked child PIDs; it refuses an existing WM by probing root properties. Do not run it on an active display. Historical desktop process command line was a one-off `dbus-run-session` shell launching `xfsettingsd`, `xfwm4 --compositor=off`, `xfdesktop`, `xfce4-panel`, terminal. The shell current file has evolved and is not proof that the exact historical command is safe now.

## Milestone overview

| Milestone | Status | Evidence / caveat |
|---|---|---|
| Debian ARM64 + XFCE installed | PASS (historical/install records and current read-only dpkg audit) | Debian 13 trixie; XFCE 4.20 components present. |
| Manual graphical desktop | PASS historically, 2026-11-18 | User confirmed desktop visible, menu touch, `echo hello` output, terminal drag; do not claim current screen. |
| Current active `:2` XFCE process set | Process presence confirmed | Read-only audit finds matching X11/XFCE processes; no present-day visual/touch acceptance. |
| Resume shell script | Direct resume previously passed | It checks existing XFCE, does not start a desktop/server. See its fail-closed checks. |
| Termux:Widget installation | Installed | Android package present, `versionCode=1001`; upstream release v0.15.0 noted in earlier evidence. |
| Home-screen shortcut | User-reported successful after prior inconclusive picker attempt | Script/icon are present. Tap flow has not been independently validated after the report. |
| XFCE appearance | NOT ACCEPTED | Current saved profile had empty GTK/icon theme and wallpaper setting; no visual acceptance. Appearance package transaction interrupted. |
| Essential GUI apps | Partial installation only | Core app APT transaction completed in this handoff; installed does not prove graphical operation. See DEVICE_STATE. |
| Firefox ESR / HTTPS | NOT VERIFIED | Debian `firefox-esr` was absent at latest audit before interruption. |
| Android standalone launcher | NOT INSTALLED | Kotlin source and debug APK exist; `dev.local.linuxdesktop.launcher` absent on device. |
| Cold-start/reboot | NOT VERIFIED | No cold start or reboot exercised. No permission for cleanup was given. |

## Project history and decisions

The initial Android lifecycle-manager design was assessed as unsafe/incomplete. The project pivoted to preserving a working XFCE session and a minimal resume-only script, then workstation UI/app usability. Keep legacy manager files for reference; they are not a prerequisite to a usable desktop. Do not revive a broad lifecycle rewrite without a concrete need and a separately approved plan.

Previous narrower instructions explicitly protected Ubuntu, display `:1`, active sessions, Android state, and prohibited broad process termination, unidentified socket deletion, reboot, screen-size changes and APK changes. This handoff does not lift those boundaries. The new task also forbids implementation/cleanup/package installation. None is authorized by creating handoff files.

## Critical caveats for next agent

1. First reconcile package-manager state safely. Last device read found active `apt-get` PID `2081` running the appearance transaction and PRoot/package-related processes. This finding is time-sensitive; verify again non-destructively. Do not kill, force-stop, run `dpkg --configure -a`, or start competing APT work. If the APT command is still live, wait/ask user; if outcome unclear, obtain explicit permission for repair and document precise transaction plan first.
2. User cancellation returned an explicit tool interruption. Do not resume the interrupted `apt-get` silently. A previous API denial is not permission for another install attempt.
3. Protect every existing display/session. `:2` has known-good XFCE but also additional experimental entries; `:3` is live. An older `xfwm4` under PRoot exists on `:2` too. Do not assume a process belongs to the current session from name alone.
4. Existing source manager has lifecycle/ownership issues and tests are internally inconsistent. No test suite was executed during this handoff. Do not claim historical test results are current.
5. Ask the tablet owner to confirm the current visible desktop before changes, and obtain user visual signoff on any redesign. Do not mark visual usability PASS from ADB/process output or screenshots alone.

## Handoff documents

- [DEVICE_STATE.md](DEVICE_STATE.md): fresh observed device, package and process data, including interrupted APT state.
- [WORKING_COMMANDS.md](WORKING_COMMANDS.md): historical commands/workarounds and safe, read-only checks.
- [FILE_MAP.md](FILE_MAP.md): current workspace architecture/source inventory.
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md): actionable blockers and risks.
- [NEXT_STEPS.md](NEXT_STEPS.md): gated roadmap.
- [SECURITY_BOUNDARIES.md](SECURITY_BOUNDARIES.md): preserve state, permission and process constraints.
- [ACCEPTANCE_MATRIX.md](ACCEPTANCE_MATRIX.md): evidence-qualified test status.
