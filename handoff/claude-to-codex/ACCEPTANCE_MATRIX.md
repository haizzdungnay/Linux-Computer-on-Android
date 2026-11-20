# Acceptance Matrix

## Nghiệm thu sau triển khai — 2026-11-19

| Nhóm | Trạng thái mới nhất |
|---|---|
| Giao diện đang chạy | Đã cấu hình và chụp ảnh thực tế: Arc-Dark, Papirus, Whisker, top panel/bottom dock, font/DPI |
| Menu cảm ứng / kéo cửa sổ / Home Resume | **PASS**, người dùng xác nhận “Cả ba hoạt động” |
| Ứng dụng thiết yếu | **PASS** cho terminal, file manager, editor lưu file, PDF/JPG, ZIP giải nén, Settings, Task Manager, clipboard |
| Browser HTTPS | **PASS NetSurf**; **BLOCKED Firefox ESR** vì lỗi font trong sandbox PRoot |
| APT/dpkg | **PASS**, giao dịch cũ tự hoàn tất; audit sạch, khóa nhả |
| Cold Start / reboot / APK | **NOT VERIFIED**, để phiên sau |
| DPI thoải mái / bàn phím vật lý / dùng lâu dài | Chưa nghiệm thu riêng |

[Bằng chứng, gói cài, cấu hình và rollback](DESKTOP_COMPLETION_2026-11-19.md). Các hàng D1–T2 và gate phía dưới là trạng thái trước triển khai, được giữ làm lịch sử.

**Evidence cutoff:** 2026-11-19. `PASS (historical)` is not current acceptance. `NOT VERIFIED` means evidence is missing; it does not mean failure. Package presence alone does not prove app operation.

| ID | Acceptance item | Status | Evidence / gap |
|---|---|---|---|
| D1 | Debian 13 ARM64 installed | PASS | Read-only `/etc/os-release`, architecture and package inventory; Debian `trixie`, `arm64`. |
| D2 | XFCE 4.20 core packages present | PASS | Read-only Debian package query for XFCE components. |
| D3 | Desktop rendered on tablet | PASS (historical, 2026-11-18) | Owner confirmed visible desktop and panels. No current visual confirmation in 2026-11-19 handoff audit. |
| D4 | Touch menu and terminal interaction | PASS (historical, 2026-11-18) | Owner confirmed touch menu, terminal `echo hello`, and window drag. Not re-tested during handoff. |
| D5 | Current `:2` session visibly usable | NOT VERIFIED | Process/environment and WM property observed; no current screen evidence or owner confirmation. Other experimental sessions remain. |
| D6 | Resume existing XFCE via script | PASS (historical direct test) | Script returned `RESUME_REQUESTED: existing XFCE on :2; no desktop process started.` This validates resume request only at that time. |
| D7 | Android Home-screen shortcut is tappable and resumes | NOT VERIFIED | Owner later reported setup succeeded; script/icon exist. No fresh tap verification or user-visible confirmation in handoff. |
| D8 | Cold start from no session | NOT VERIFIED | Not tested. Do not stop current sessions to create a test condition. Resume-only script does not cold-start. |
| D9 | Reboot recovery / startup | NOT VERIFIED | No reboot or boot-recovery test. |
| D10 | Standalone Kotlin launcher installed and works | NOT VERIFIED / package absent | Debug APK/source exist; `dev.local.linuxdesktop.launcher` absent in device package inventory. No APK installed. |
| P1 | Essential GUI packages installed | PARTIAL | Core app APT batch completed and listed packages queried. Package presence only; GUI operation and representative file tests not run. |
| P2 | APT/dpkg clean and usable | FAIL / unresolved at last observation | Appearance install interrupted. Last audit found APT lock, Papirus broken, packages unpacked/unconfigured and pending triggers. No recovery performed; current status must be rechecked only after authorization. |
| P3 | Firefox ESR available and HTTPS workflow works | NOT VERIFIED | `firefox-esr` absent in last package query. Browser launch/download/HTTPS not tested. |
| P4 | PDF and archive opening works | NOT VERIFIED | Atril and Engrampa packages installed in core batch, but no PDF/ZIP/RAR content test or MIME handler test. |
| U1 | Mint-style appearance configured | NOT STARTED | Existing saved settings show default/empty GTK/icon theme and no wallpaper setting. Theme transaction interrupted; no visual settings applied. |
| U2 | Appearance validated on tablet and signed off | NOT STARTED | Requires M1 gate, healthy package DB, separate authorization, reversible profile and direct owner inspection. |
| S1 | Existing XFCE config backup available | PASS (limited) | Tar exists; recorded SHA-256 `debf6dc6510598e9044bc3b1fe54d034613d3a1711d9f958c014264a8c31ce13`. Saved files only; live-copied, not atomic. |
| S2 | Snapshot is complete/consistent rollback | NOT VERIFIED | In-memory state not captured; XFCE could write during copy. Never restore over active profile. |
| W1 | Legacy lifecycle manager safe for tablet | NOT VERIFIED; DO NOT USE | Source ownership/reconciliation concerns, tests and manager API appear inconsistent, and no current suite run. Wrappers must not be used on live sessions. |
| T1 | Current automated test suite passes | NOT VERIFIED | Tests were not run during this handoff. Historical report of 36 tests, 17 failures and 1 error not freshly reproduced. |
| T2 | Workspace is version-controlled | FAIL / absent | `git rev-parse --is-inside-work-tree` exited 128; no Git repository. No commits or pushes. |

## M1 gate — preserve working desktop

**Overall status: NOT VERIFIED.**

Required evidence: owner confirms current visible session and interaction; safe isolated cold-start evidence without stopping protected sessions; exact known-good profile and commands recorded; backup limitations disclosed. Historical desktop test and resume-only script do not satisfy the current-session/cold-start criteria. If safe cold-start cannot be done without affecting protected sessions, leave M1 NOT VERIFIED and defer rather than manufacture a test state.

## M2 gate — appearance and GUI apps

**Overall status: NOT STARTED.**

Blocked pending M1 acceptance and safe resolution of interrupted APT state. No appearance was applied. Future completion requires reviewed minimal package plan, reversible separate profile, validation on device, app/file-handler tests, and owner visual confirmation. No acceptance may be inferred from installed package names.

## Evidence rules

- Attach date, command or direct user observation, and actual result to every future status change.
- Keep historical PASS distinct from current PASS.
- If a device action is unsafe, unauthorized or unavailable, record NOT VERIFIED; do not weaken checks or claim success.
- Resume, cold start, reboot recovery, Android widget tap, and standalone APK are separate test cases.
