# Codex Start Here

## Cập nhật sau tiếp quản — đọc trước

Mới nhất 2026-11-20: Mojave-Dark-solid / WhiteSur, Firefox vào Google bằng PRoot riêng có bản vá upstream, sandbox hiệu lực mức 6. Viewer co giãn, fullscreen `1600×1068`; người dùng đã xác nhận tỷ lệ/cỡ chữ. Dock sửa sang ẩn thông minh + vùng gọi lại 12 px, người dùng xác nhận dùng được. Phiên thử `:3` đã được đóng theo chấp thuận riêng của người dùng để tránh giành viewer; giữ :2 và :1/Ubuntu. Đọc [MOJAVE_FIREFOX_2026-11-20.md](MOJAVE_FIREFOX_2026-11-20.md) trước; báo cáo Arc/NetSurf bên dưới là lịch sử.

Các trạng thái/gate phía dưới là bản bàn giao cũ. Yêu cầu mới của người dùng đã cho phép cấu hình và cài ứng dụng trong phiên đang có; Cold Start, reboot và APK riêng vẫn chưa kiểm chứng. Không chạy lại script thay panel một lần hoặc manager legacy.

**Workspace:** `C:\Users\PC\linux-desktop`  
**Handoff snapshot:** 2026-11-19; device checks reflect final read-only audit in this session.  
**Repository:** Not a Git repository (`git rev-parse --is-inside-work-tree` returned exit 128). No commit or push.

## Current situation

- Tablet `f422eebd`, Xiaomi Pad 7 Pro (`24091RPADG`), Android 16/API 36, HyperOS `OS3.0.303.0.WOYMIXM`, arm64. ADB connected.
- Termux, Termux:X11 and Termux:Widget installed. A live XFCE profile is running against X11 `:2` with `LIBGL_ALWAYS_SOFTWARE=1`, `xfwm4 --compositor=off`, and `XDG_CONFIG_HOME=/root/.ld-test/xfce-config`. Another X server `:3` and multiple older PRoot/XFCE experiments are also present. Their owners/roles are not all established. **Do not stop or signal any process.**
- The prior user reported successful Home-screen Resume shortcut setup. Current Termux `.shortcuts/linux-resume.sh` and icon exist. This does not establish cold start, reboot startup, or standalone APK behavior. The actual XFCE profile remains without installed appearance changes; an interrupted APT install left `dpkg` in a broken/unfinished state. See `DEVICE_STATE.md` and `KNOWN_ISSUES.md`.
- Debian XFCE previously passed physical tablet tests on 2026-11-18: visible desktop/panels, touch menu, terminal `echo hello`, and touch window dragging. Historical acceptance is not present-day visual confirmation.

## First actions

1. Read `SECURITY_BOUNDARIES.md`, then `DEVICE_STATE.md` and `KNOWN_ISSUES.md` before any device interaction.
2. **Do not run APT, `dpkg --configure`, repair, or reinstallation commands yet.** An APT theme/font command was interrupted after package downloads/unpacking; `dpkg --audit` reported Papirus as broken, several packages unpacked/unconfigured and triggers pending, while the original APT process remained running at last process audit. Do not launch another package transaction. Verify exact current process/package state after receiving authorization and ensuring APT is quiescent without killing it.
3. Preserve existing sessions. `:1` resources, Ubuntu, Debian, and live/experimental sessions are not disposable. No process cleanup, reboot, resolution/density changes, socket deletion, Android APK install or reset.
4. Resume user-facing work in this order: preserve existing XFCE profile; safely recover/verify package DB with authorization and APT lock owner known; install only minimal desired apps/themes in reviewed Debian stable batches; configure a separate reversible XFCE profile; validate real UI on tablet and ask user visual confirmation.
5. Treat `scripts/desktop.py` as legacy/research code, not trusted session control. `scripts/minimal-launcher/linux-resume.sh` is resume-only and not cold-start code. Do not deploy/run manager lifecycle scripts on tablet.

## Milestone status

- Historical manual XFCE session: PASS on 2026-11-18, only as recorded historical evidence.
- Current X11/XFCE process presence: confirmed read-only on 2026-11-19; current screen contents/touch not verified.
- Termux:Widget shortcut: installed script+icon verified on device, and direct resume previously tested; user reports home-screen shortcut setup succeeded. Recheck by user-visible tap before calling it verified.
- Appearance and application phase: incomplete; package transaction interrupted. Do not mark design or GUI apps accepted.
- Standalone APK: source/build output exists; package not installed on device.
- Cold start/reboot: NOT VERIFIED.

See [HANDOFF.md](HANDOFF.md) for project story and individual handoff documents for exact evidence and next steps.
