# Linux Desktop trên Termux

## Cập nhật hiện tại — 2026-11-20

XFCE `:2` dùng Mojave-Dark-solid và WhiteSur từ đúng repository người dùng gửi. Firefox đã vào Google với sandbox mặc định. Desktop co giãn theo Termux:X11; fullscreen hiện `1600×1068`, người dùng xác nhận vừa màn hình. Dock chín ứng dụng dùng ẩn thông minh, vùng gọi lại 12 px; người dùng xác nhận hiện lại và dùng được sau sửa ngày 20/11. Xem [báo cáo, kiểm chứng và rollback](handoff/claude-to-codex/MOJAVE_FIREFOX_2026-11-20.md), [ảnh dock hiện tại](artifacts/dock-reveal-20261120/desktop-visible.png). Cold Start/reboot/APK riêng vẫn chưa kiểm chứng.

**Bàn phím Xiaomi:** KeyInterceptor của Termux:X11 nhận Alt+Tab hai chiều trong XFCE. Tắt pointer capture để cuộn hai ngón. Đặt con trỏ bằng touchpad rồi chạm nút **R** để nhấp phải. [Báo cáo input và hoàn tác](handoff/claude-to-codex/XIAOMI_INPUT_2026-11-20.md)

Các đoạn M1/M2 dưới đây ghi lại trạng thái **trước** yêu cầu hoàn thiện desktop hiện tại, không phải tình trạng mới nhất.

**Trạng thái: M1 NOT VERIFIED; M2 NOT STARTED.** Bằng chứng lịch sử ngày 2026-11-18 xác nhận phiên XFCE thủ công `:2` hiển thị và tương tác được khi đó; khảo sát read-only gần nhất được cung cấp ngày 2026-11-19 chỉ xác nhận process/config, không xác nhận hình ảnh hiện tại. Không dừng, khởi động lại hoặc sửa phiên hiện có. Snapshot cấu hình đã tạo riêng tại `snapshots/xfce-config-20261119T103201/xfce-config.snapshot.tar`; archive chỉ gồm file cấu hình đã lưu và không đảm bảo chứa thiết lập còn trong bộ nhớ. Cold start trong môi trường trống chưa thử an toàn. M1 chưa đạt điều kiện nghiệm thu; M2 chưa bắt đầu.

Quy trình thủ công từng xác minh ngày 2026-11-18 dùng PRoot chia sẻ `/tmp` (`--shared-tmp`) để client thấy socket X11, `DISPLAY=:2`, D-Bus riêng (`dbus-run-session`), `LIBGL_ALWAYS_SOFTWARE=1`, rồi chạy theo thứ tự `xfsettingsd`, `xfwm4 --compositor=off`, `xfdesktop`, `xfce4-panel`, `xfce4-terminal`. Đây là thiết lập/thứ tự đã thử tại thời điểm đó, không phải lệnh cold-start hiện đã chứng minh an toàn. Lần thử đặt `XDG_CONFIG_HOME=/root/.ld-test/xfce-config`; snapshot cấu hình được lưu tại `snapshots/xfce-config-20261119T103201/xfce-config.snapshot.tar`. Có thể còn cài đặt trong bộ nhớ chưa lưu; không khôi phục snapshot lên phiên đang chạy.

Không coi manager legacy là vô hiệu hay an toàn: `scripts/desktop.py` có các lệnh `start`, `stop`, `status`, `resume`, nhưng ownership/lifecycle và tích hợp launcher chưa được xác minh cho pivot này. Không chạy wrapper legacy hoặc `scripts/xfce-components.sh` trên phiên đang tồn tại; script component chưa được xác minh end-to-end, dùng XDG `/root/.local/linux-desktop/{config,cache,run,logs}` (khác đường dẫn lần thử), và có trap gửi TERM cho PID con. Trước cold start, xác định chắc display mục tiêu và ownership process; nếu không chắc, dừng và xin phép. Không xóa socket/lock hoặc signal process không rõ. Chưa cài theme/package, chưa áp dụng cấu hình XFCE thử nghiệm, chưa cài APK launcher. Không tuyên bố mục tiêu một chạm. Xem trạng thái và giới hạn trong `TEST_REPORT.md`.

Workspace: `C:\Users\PC\linux-desktop`. Debian 13 ARM64 chạy qua PRoot, không cần root Android. Container Ubuntu có sẵn được giữ nguyên. PRoot không phải ranh giới bảo mật: chương trình Debian chạy với quyền Android của Termux; không chạy phần mềm không tin cậy.

Quyền Termux RUN_COMMAND cho phép app được cấp quyền chạy lệnh trong Termux. Cấu hình `allow-external-apps=true` áp dụng cho mọi app có quyền này. Chỉ cấp quyền cho launcher đáng tin cậy. Hướng dẫn sao lưu/khôi phục và cảnh báo trong `TROUBLESHOOTING.md`; tình trạng cài đặt trong `INSTALL_REPORT.md`.

Source Android: `C:\Users\PC\linux-desktop\android`. APK debug thử nghiệm: `C:\Users\PC\linux-desktop\android\app\build\outputs\apk\debug\app-debug.apk`; **không cài để sử dụng** khi manager còn bị chặn. Không có APK phát hành `linux-desktop-launcher.apk`. Kết quả và giới hạn tại `TEST_REPORT.md`.
