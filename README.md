# Linux Computer on Android

Công cụ cài đặt và khởi chạy nhanh gọn **Linux Desktop** (Debian 13 ARM64 + XFCE) trên điện thoại / máy tính bảng Android thông qua **Termux**, **PRoot** và **Termux:X11** — **không cần root Android**.

> **Trạng thái hiện tại** — Widget **Linux Resume** mở phiên đang chạy hoặc khởi động XFCE từ đầu. Đường khởi động và đăng xuất đã thử trên phiên riêng trên tablet. Lần chuyển từ phiên thủ công và mở lại bằng chính widget Android cần thử sau khi đóng các ứng dụng đang mở.

---

## Cài đặt nhanh trên máy Android mới

### Cách 1: APK All-in-One (Không cần cài Termux hay Termux:X11)

APK `dev.local.linuxdesktop.launcher` tích hợp sẵn **PRoot ARM64** (`libproot.so`, `libproot-loader.so`, `libtalloc.so.2`), **X11 Server / Lorie Viewer** (`libXlorie.so`) và toàn bộ script cấu hình trong repo:

1. Tải file APK từ mục **Releases** trên GitHub (hoặc build trực tiếp bằng Gradle trong `android/` với `gradle :app:assembleDebug`).
2. Cài APK lên thiết bị Android ARM64 (`arm64-v8a`, Android 8.0+ / `minSdk 26`, `targetSdk 28`).
3. Mở **Linux Desktop** -> nhấn **Install Linux Desktop**:
   - Tự động tải Debian 13 (`trixie`) ARM64 rootfs từ `images.linuxcontainers.org`.
   - Giải nén, triển khai script desktop và chạy `apt-get install` (`xfce4`, `picom`, `firefox-esr`, fonts, `sassc`...), cài theme **WhiteSur-Dark**, **WhiteSur-dark icons** và hình nền **Monterey**.
4. Nhấn **Start & Open Desktop** để khởi chạy X11 server nội bộ + phiên Debian XFCE và mở màn hình desktop ngay trong app.

> **Lưu ý kiểm thử APK độc lập:** APK All-in-One đã được biên dịch (`assembleDebug`) và kiểm thử unit test (`testDebugUnitTest`). Quá trình cài đặt & khởi chạy end-to-end trên một máy Android sạch chưa cài Termux cần được thử nghiệm trực tiếp trên thiết bị.

### Cách 2: Cài qua Termux + `scripts/install.sh`

Nếu thiết bị đã cài **Termux** (và **Termux:X11** / **Termux:Widget**), mở Termux và chạy:

```sh
pkg update -y && pkg install -y git
git clone https://github.com/haizzdungnay/Linux-Computer-on-Android.git ~/linux-desktop
cd ~/linux-desktop
sh scripts/install.sh
```

Các tùy chọn hỗ trợ của [scripts/install.sh](scripts/install.sh):
- `sh scripts/install.sh --dry-run`: Xem trước toàn bộ lệnh sẽ chạy mà không thay đổi hệ thống.
- `sh scripts/install.sh --skip-pkgs`: Bỏ qua bước cài gói `pkg` / `apt-get`, chỉ triển khai lại các script & cấu hình.
- `sh scripts/install.sh --skip-themes`: Bỏ qua bước clone/cài theme WhiteSur & hình nền Monterey.

Sau khi cài xong, khởi chạy hoặc khôi phục phiên desktop bằng:

```sh
~/.shortcuts/linux-resume.sh
```

---

## Tính năng & trạng thái đã xác minh (2026-11-20)

- **Môi trường Linux:** Debian 13 ARM64 chạy qua PRoot trên Termux (không cần root, giữ nguyên container Ubuntu nếu có).
- **Giao diện Desktop (XFCE trên `DISPLAY=:2`):**
  - GTK3 và Xfwm4 dùng **WhiteSur-Dark** với điểm nhấn xanh, bộ icon **WhiteSur-dark**, hình nền **Monterey** tím/xanh và ba nút cửa sổ bên trái.
  - Tự động co giãn theo kích thước Termux:X11 (toàn màn hình `1600×1068`).
  - Dock 9 ứng dụng tự ẩn, rê chuột đến giữa mép dưới để gọi lại. Thanh trên có đồng hồ, nút âm lượng Linux, phần trăm pin Android và nút nguồn Linux.
  - Whisker có **Bật hiệu ứng** và **Tắt hiệu ứng** cho Picom XRender. Khi bật, hai thanh có blur nền, cửa sổ có bóng và fade. Thunar ở chế độ cửa sổ thường có độ đục 91% và blur nền.
  - **Đăng xuất và tắt Linux** yêu cầu đóng các cửa sổ ứng dụng trước. Ở phiên do widget khởi chạy, đăng xuất dừng Debian XFCE, Termux:X11, PulseAudio và các helper của phiên. Bấm lại **Linux Resume** trên Android để khởi động lại. Dùng nút nguồn tablet cho chế độ ngủ và tắt Android.
- **Trình duyệt:** Firefox hoạt động với sandbox mặc định (kèm cấu hình/patch hỗ trợ PRoot trong `scripts/`).
- **Nhập liệu (bàn phím & touchpad Xiaomi):**
  - KeyInterceptor của Termux:X11 nhận `Alt+Tab` hai chiều trong XFCE.
  - Tắt pointer capture để cuộn hai ngón; đặt con trỏ bằng touchpad và chạm phím **R** để nhấp phải.
- Chi tiết kiểm chứng và rollback xem tại:
  - [WhiteSur, ảnh/video và rollback](handoff/claude-to-codex/WHITESUR_2026-11-20.md)
  - [Mốc Mojave trước khi chuyển và cấu hình Firefox](handoff/claude-to-codex/MOJAVE_FIREFOX_2026-11-20.md)
  - [XIAOMI_INPUT_2026-11-20.md](handoff/claude-to-codex/XIAOMI_INPUT_2026-11-20.md)
  - [Ảnh desktop hiện tại](artifacts/whitesur-full-20261120/desktop-thunar.png)

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
│   ├── style-tablet-xfce.py      # Cấu hình Mojave trước đây và kiểm tra danh tính phiên sống
│   ├── whitesur-tablet-xfce.py   # Áp dụng, kiểm tra và hoàn tác Xfconf cho WhiteSur
│   ├── whitesur-panel.css       # Nền panel/dock riêng, chữ và icon giữ độ đục
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
- **Giao diện tablet:** `whitesur-tablet-xfce.py` quản lý cấu hình WhiteSur của profile sống. `xfce-effects.py` bật/tắt Picom riêng qua Whisker. Các script `configure-tablet-xfce.py` và `style-tablet-xfce.py` lưu quy trình giao diện cũ.
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
