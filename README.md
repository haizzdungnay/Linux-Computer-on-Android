# Linux Computer on Android

Công cụ cài đặt và khởi chạy nhanh gọn **Linux Desktop** (Debian 13 ARM64 + XFCE) trên điện thoại / máy tính bảng Android thông qua **Termux**, **PRoot** và **Termux:X11** — **không cần root Android**.

> **Lưu ý trạng thái hiện tại:** Phiên XFCE `:2` đang hoạt động và đã kiểm chứng giao diện, dock, Firefox và input bàn phím. Tuy nhiên, quy trình **cold start**, **reboot** và **APK Android Launcher** riêng vẫn chưa kiểm chứng end-to-end; vui lòng đọc kỹ phần [Lưu ý vận hành & bảo mật](#lưu-ý-vận-hành--bảo-mật) trước khi sử dụng.

---

## Tính năng & trạng thái đã xác minh (2026-11-20)

- **Môi trường Linux:** Debian 13 ARM64 chạy qua PRoot trên Termux (không cần root, giữ nguyên container Ubuntu nếu có).
- **Giao diện Desktop (XFCE trên `DISPLAY=:2`):**
  - Sử dụng theme **Mojave-Dark-solid** và **WhiteSur**.
  - Tự động co giãn theo kích thước Termux:X11 (toàn màn hình `1600×1068`).
  - Dock 9 ứng dụng với chế độ ẩn thông minh (vùng gọi lại 12 px).
- **Trình duyệt:** Firefox hoạt động với sandbox mặc định (kèm cấu hình/patch hỗ trợ PRoot trong `scripts/`).
- **Nhập liệu (bàn phím & touchpad Xiaomi):**
  - KeyInterceptor của Termux:X11 nhận `Alt+Tab` hai chiều trong XFCE.
  - Tắt pointer capture để cuộn hai ngón; đặt con trỏ bằng touchpad và chạm phím **R** để nhấp phải.
- Chi tiết kiểm chứng và rollback xem tại:
  - [MOJAVE_FIREFOX_2026-11-20.md](handoff/claude-to-codex/MOJAVE_FIREFOX_2026-11-20.md)
  - [XIAOMI_INPUT_2026-11-20.md](handoff/claude-to-codex/XIAOMI_INPUT_2026-11-20.md)
  - Ảnh dock hiện tại: [desktop-visible.png](artifacts/dock-reveal-20261120/desktop-visible.png)

---

## Cấu trúc dự án

```text
linux-desktop/
├── android/                  # Ứng dụng Android Launcher (Kotlin / Gradle)
│   └── app/src/
│       ├── main/java/dev/local/linuxdesktop/launcher/
│       │   ├── MainActivity.kt       # Giao diện & điều phối launcher
│       │   ├── TermuxCommands.kt     # Gọi lệnh sang Termux qua RUN_COMMAND
│       │   └── CommandResult.kt      # Mô hình kết quả thực thi lệnh
│       └── test/                     # Unit test (CommandResultTest.kt)
│
├── scripts/                  # Script cài đặt, cấu hình & điều phối Linux Desktop
│   ├── desktop.py            # Trình quản lý phiên (start / stop / status / resume)
│   ├── start-linux.sh        # Wrapper gọi `desktop.py start`
│   ├── stop-linux.sh         # Wrapper gọi `desktop.py stop`
│   ├── status-linux.sh       # Wrapper gọi `desktop.py status`
│   ├── xfce-components.sh    # Khởi chạy từng thành phần XFCE
│   ├── minimal-launcher/
│   │   └── linux-resume.sh   # Script resume nhanh cho launcher tối giản
│   ├── configure-tablet-xfce.py  # Cấu hình bố cục XFCE cho tablet
│   ├── style-tablet-xfce.py      # Áp dụng theme Mojave/WhiteSur & dock
│   ├── xfce-effects.py           # Cấu hình hiệu ứng XFCE / picom
│   ├── picom-xrender.conf        # Cấu hình compositor picom (xrender)
│   ├── firefox-tablet.py         # Cấu hình Firefox cho môi trường tablet
│   ├── check-firefox-seccomp.c   # Kiểm tra seccomp cho Firefox trên PRoot
│   └── proot-firefox-sandbox.patch
│
├── tests/                    # Kiểm thử Python cho lifecycle & bảo mật
│   ├── test_lifecycle.py
│   └── test_manager_security.py
│
├── snapshots/                # Bản sao lưu cấu hình XFCE, Termux:X11 XML & Firefox sandbox
├── artifacts/                # Ảnh chụp màn hình, log chẩn đoán & tài nguyên UI theo ngày
├── handoff/                  # Tài liệu bàn giao kỹ thuật & trạng thái thiết bị
│   └── claude-to-codex/
│
├── INSTALL_REPORT.md         # Báo cáo tình trạng cài đặt
├── TEST_REPORT.md            # Báo cáo kết quả kiểm thử & giới hạn
├── LIFECYCLE_AUDIT.md        # Kiểm tra vòng đời tiến trình
├── TROUBLESHOOTING.md        # Hướng dẫn sao lưu, khôi phục & xử lý sự cố
└── LICENSE
```

---

## Thành phần chính

### 1. Bộ script điều phối & tối ưu Desktop (`scripts/`)
- **Quản lý vòng đời:** `scripts/desktop.py` (cùng các wrapper `start-linux.sh`, `stop-linux.sh`, `status-linux.sh`) quản lý các lệnh `start`, `stop`, `status`, `resume`.
- **Tối ưu giao diện Tablet:** `configure-tablet-xfce.py`, `style-tablet-xfce.py` và `xfce-effects.py` tự động hóa việc thiết lập panel/dock, theme Mojave/WhiteSur và hiệu ứng hiển thị.
- **Tối ưu Firefox trên PRoot:** `firefox-tablet.py`, `check-firefox-seccomp.c` và `proot-firefox-sandbox.patch`.

### 2. Android Launcher (`android/`)
- Ứng dụng Android viết bằng Kotlin (`dev.local.linuxdesktop.launcher`) sử dụng quyền `RUN_COMMAND` của Termux để kích hoạt các script khởi chạy/khôi phục phiên Linux từ màn hình chính Android.
- **Lưu ý:** APK debug thử nghiệm (`android/app/build/outputs/apk/debug/app-debug.apk`) chỉ phục vụ kiểm thử nội bộ, **không cài để sử dụng chính thức** khi phần quản lý vòng đời (cold start / ownership) chưa được xác minh hoàn toàn. Hiện chưa có bản phát hành `linux-desktop-launcher.apk`.

---

## Lưu ý vận hành & bảo mật

- **Không tự ý chạy wrapper legacy trên phiên đang sống:** `scripts/desktop.py` và `scripts/xfce-components.sh` chưa được xác minh end-to-end cho luồng cold start mới; không chạy đè lên phiên XFCE `:2` đang hoạt động, không xóa socket/lock hoặc gửi signal tới tiến trình không rõ ownership.
- **Ranh giới bảo mật PRoot:** PRoot **không phải** sandbox bảo mật; các chương trình Debian chạy với quyền Android của Termux — không chạy phần mềm không tin cậy.
- **Quyền `RUN_COMMAND` của Termux:** Thiết lập `allow-external-apps=true` cho phép mọi ứng dụng có quyền `RUN_COMMAND` thực thi lệnh trong Termux. Chỉ cấp quyền này cho launcher đáng tin cậy.

---

## Tài liệu tham khảo thêm

- Tình trạng cài đặt: [INSTALL_REPORT.md](INSTALL_REPORT.md)
- Kết quả kiểm thử & giới hạn: [TEST_REPORT.md](TEST_REPORT.md)
- Kiểm tra vòng đời tiến trình: [LIFECYCLE_AUDIT.md](LIFECYCLE_AUDIT.md)
- Sao lưu, khôi phục & xử lý lỗi: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
