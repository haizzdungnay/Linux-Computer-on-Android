# Gated Next Steps

> **Sau triển khai 2026-11-19:** giao diện và app thiết yếu đã hoàn thiện trên `:2`; cảm ứng/menu/Resume đã được người dùng xác nhận. Đọc [báo cáo và rollback](DESKTOP_COMPLETION_2026-11-19.md). Việc tiếp theo: Firefox/web hiện đại trong PRoot, rồi Cold Start/reboot/APK trong phạm vi được giao mới. Các gate M1/M2 bên dưới giữ làm lịch sử; không cần lặp lại APT recovery hoặc redesign đã làm.

**Status date:** 2026-11-19. This is a roadmap, not authorization to perform device changes. Existing process, package, and display safeguards in `SECURITY_BOUNDARIES.md` override convenience.

## Gate 0 — retain current state

1. Preserve Debian XFCE, Termux, Ubuntu, Android, all X11/PRoot sessions, saved configuration and workspace artifacts. No process signals, session start/stop, socket/lock deletion, reboot, APK install, display mutation, or cleanup.
2. APT/dpkg is unresolved after interrupted theme/font install. Do not start package commands. After explicit authorization, first perform narrowly scoped, non-mutating inspection of relevant process identity and package lock/audit state. If a legitimate APT process is active, allow it to finish; do not kill it. If state remains ambiguous, stop and report evidence.
3. Confirm the config archive hash before using it as a reference. Do not restore over the live profile.

## M1 — preserve and establish baseline

**Current:** NOT VERIFIED.

1. Ask owner to confirm directly that current desktop is visible and interactive. Process lists, X11 properties, previous-day tests and screenshots alone do not establish current acceptance.
2. Keep the current session untouched. A cold-start acceptance test requires a safely isolated empty test environment and separate explicit approval for any operation that changes or stops a session. Do not manufacture an empty state by terminating current processes.
3. If safe cold-start evidence cannot be produced without violating protections, document it as NOT VERIFIED and defer it. Do not substitute `linux-resume.sh` success; that script resumes only an already-running desktop.
4. Keep current private saved-profile backup. It is not atomic; if a new snapshot is authorized, use a unique destination, capture only XFCE config, compare file lists and hashes, and never overwrite the existing archive.
5. Update root `README.md` / `TEST_REPORT.md` only with evidence-backed additive corrections. Keep historical tests labeled and preserve older results.

**M1 exit:** current-session user confirmation plus safely isolated cold-start test, or an explicit documented NOT VERIFIED result if safe test is unavailable. M2 remains gated until M1 is accepted by the owner.

## M2 — appearance, only after M1 gate

**Current:** NOT STARTED. No visual settings were applied.

1. Obtain explicit approval before package database repair/install or live-session/configuration changes. First resolve interrupted APT state safely; do not start competing APT/dpkg operations or remove locks.
2. Inspect installed package state and simulate proposed minimal Debian stable package changes. Choose only desired packages; do not install GNOME/KDE or broad recommends. The interrupted Arc/Papirus/Noto transaction is not evidence of successful installation.
3. Build reversible configuration in a separate, uniquely named XFCE profile based on saved snapshot. Do not replace `/root/.ld-test/xfce-config`, modify `:1`, alter display size/density, or apply to unknown session.
4. Use existing XFCE panel support rather than adding a heavy dock. Keep touch targets, readable scale, clear contrast and a low-resource palette. Wallpaper source and license must be clear. Validate XML and desktop entries before any approved launch.
5. Apply only once target session ownership and rollback path are unambiguous. If application requires signaling/stopping/starting an uncertain process, stop and request approval for that precise action.
6. Have owner check the tablet directly: visual hierarchy, theme, icons, wallpaper, panel/dock layout, touch targets, menu, terminal, window drag/close, keyboard/mouse as available. Record per-item evidence; no visual PASS from package presence alone.

## Later workstation acceptance (after M2)

- Verify core apps launch and open representative files: Mousepad, Ristretto, Atril PDF, Engrampa archive, Thunar archive plugin, task manager, screenshot, clipboard.
- Test file association and touch usability. Confirm HTTPS/browser and download workflow only after a browser choice/install is separately authorized and package state is healthy. Do not claim Firefox ESR until installed and exercised.
- Evaluate SSH/Git/Python workflows without exposing credentials. Use test repositories/data; do not store private keys in shared project artifacts.
- Record RAM/storage and responsiveness at representative use. Current RAM snapshot is constrained and fluctuating; do not extrapolate from package metadata.
- Run current targeted tests only after confirming what commands do; legacy manager tests/results need reconciliation. No device lifecycle tests without explicit scope and safe isolated setup.

## Android launcher / cold start

- Standalone APK is not installed and not part of the currently working Resume shortcut. Do not build/install/change it under current handoff scope.
- If later authorized as a separate task, reconcile Termux script paths, permission model, explicit intent contract and `RESUME` semantics; review Android lifecycle/security before APK changes. Require explicit APK installation approval.
- Distinguish Resume (open existing session), cold start (create session), and reboot recovery. Never claim one-tap cold start or reboot survival based on Resume-only evidence.
