# Mojave, Firefox và dock — 2026-11-20

## Kết quả đã kiểm chứng

Xiaomi Pad 7 Pro `f422eebd`, XFCE `:2`, HOME `/root`, profile `/root/.ld-test/xfce-config`, UID `10528`. Giữ software rendering và compositor tắt.

- Firefox đã tải Google và tìm kiếm “Debian Linux”; người dùng xác nhận nút Firefox mở Google được.
- Termux:X11 dùng chế độ `scaled`, scale `200`, fullscreen `true`, stretch `false`. Khi đổi fullscreen, desktop tự đổi `1600×1023` / `1600×1068`. Người dùng xác nhận vừa màn hình, chữ/nút ổn.
- Ngày 20/11 sửa dock khó gọi lại: **Intelligently (`1`)**, vùng gọi lại **12 px**, hiện sau **100 ms**, ẩn sau **600 ms**. Dock hiện trên desktop, ẩn khi cửa sổ che lên. Kiểm tra đưa trỏ cách mép dưới 7 px đã gọi lại được; người dùng xác nhận **“Đã hiện lại, dùng được”**.
- Dock neo giữa cạnh dưới, chín launcher thật: Files, Firefox, Mousepad, Terminal, Settings, Task Manager, App Finder, Ristretto, Atril. Icon 48 px; dock thực tế `578×65` tại desktop `1600×1068`.
- Resume trực tiếp đã đạt ngày 19/11; helper Firefox được bảo đảm chạy khi Resume. Cold Start/reboot/APK riêng chưa kiểm chứng.

Ảnh: [dock trên desktop](../../artifacts/dock-reveal-20261120/desktop-visible.png), [dock gọi lại trên Firefox](../../artifacts/dock-reveal-20261120/browser-revealed.png), [Google tìm kiếm](../../artifacts/firefox-20261119/google-search.png). Kiểm chứng dock: [verification.txt](../../artifacts/dock-reveal-20261120/verification.txt).

## Giao diện và nguồn

| Thành phần | Cấu hình / nguồn |
|---|---|
| GTK / XFWM | `Mojave-Dark-solid`, [Mojave-gtk-theme](https://github.com/vinceliuice/Mojave-gtk-theme), commit `eff102568e7aa712e7cb1f246002731a1ac32c2f` |
| Icon | `WhiteSur-dark`, [WhiteSur-icon-theme](https://github.com/vinceliuice/WhiteSur-icon-theme), commit `73d8040da51a9ed74e47c7366e7e9ff437601a5c` |
| Font | Noto Sans / Noto Sans Mono 11; DPI 120 |
| Top panel | 38 px, luôn hiện; task list dạng icon, Menu, đồng hồ, tray, Clipman |
| Whisker | Tối, `350×520`, nhóm bằng icon, tìm kiếm và Favorites thật |
| Wallpaper | `/root/.local/share/backgrounds/planet-space-129992.jpg`, [nguồn](https://wallpaperscraft.com/wallpaper/planet_space_universe_129992) |

Wallpaper là ảnh thay thế, khác ảnh mẫu; ảnh crop giữ tỷ lệ rồi zoom theo desktop. Dock dùng khối tối đặc và góc vuông vì compositor đang tắt. Không giả icon Chrome/YouTube hoặc chỉ báo hệ thống. Thẩm mỹ tổng thể hình nền/góc dock chưa được người dùng nghiệm thu riêng; chức năng dock, tỷ lệ và cỡ chữ đã được xác nhận.

Mojave cần thêm `sassc`, `libsass1`; các công cụ build Termux dùng gói đã có. `dpkg --audit` sạch ở lượt kiểm tra ngày 19/11.

## Firefox: nguyên nhân và bản sửa

Firefox ESR `153.7.0esr` trước đó crash tab với `unable to find a usable font (serif)`. PRoot stock nuốt `SIGSYS` do sandbox Firefox tạo, khiến thao tác broker thất bại. Port bản vá upstream [7bf5cfe6c83da1b4a881b119352383df9761c4a6](https://github.com/termux/proot/commit/7bf5cfe6c83da1b4a881b119352383df9761c4a6) lên PRoot `v5.1.107.86`; chỉ Firefox dùng binary riêng.

Native Termux: `/data/data/com.termux/files/home/.local/share/linux-desktop/firefox-sandbox/` chứa `proot`, `loader`, `loader32`, bản vá, source tar, script và kiểm tra seccomp. PRoot của desktop giữ nguyên.

Kiểm tra BPF thực tế:

```text
Stock PRoot:   handler=0 result=-1   denied=-1 errno=13 seccomp=2  (FAIL)
Patched PRoot: handler=1 result=4242 denied=-1 errno=13 seccomp=2  (PASS)
```

`about:support` báo Content/Media Sandbox bật, mức cấu hình và mức hiệu lực đều `6`; user namespaces không được Android hỗ trợ. Tiến trình con có seccomp filter bổ sung. Không hạ mức sandbox hoặc đặt biến tắt sandbox. [Bằng chứng](../../artifacts/firefox-20261119/final-browser-check.txt), [ảnh sandbox](../../artifacts/firefox-20261119/sandbox-level.png).

`scripts/firefox-tablet.py` là helper native và client trong Debian. Socket nằm trong thư mục riêng quyền `0700`, chỉ nhận URL HTTP(S); không nhận shell command. Helper dựng môi trường mới và xác minh phiên/UID trước khi mở Firefox. Bước này tránh `MOZ_FAKE_NO_SANDBOX=1` mà `proot-distro` mặc định thêm vào môi trường. Profile Firefox hiện có được giữ; `user.js` chỉ đặt trang chủ Google.

Dock/Menu, MIME HTTP/HTTPS và XFCE WebBrowser dùng helper này. Nếu helper không còn chạy, bấm Home Resume; helper chỉ phục vụ desktop đã có. Không coi đây là cold-start manager.

Lệnh kiểm tra chạy trong Debian đúng phiên:

```sh
python3 /root/.local/share/linux-desktop/style-tablet-xfce.py --check
python3 /root/.local/share/linux-desktop/firefox-tablet.py --check
```

Lệnh native Termux, kiểm tra cả seccomp:

```sh
python /data/data/com.termux/files/home/.local/share/linux-desktop/firefox-sandbox/firefox-tablet.py --check
```

Build đã dùng source `proot-v5.1.107.86.tar.gz`, áp `scripts/proot-firefox-sandbox.patch` bằng `patch -p1` trong source root, rồi:

```sh
make -C src -j2 CC=clang LD=clang STRIP=llvm-strip OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump PROOT_WITH_LIBANDROID_SHMEM=true PROOT_UNBUNDLE_LOADER=/data/data/com.termux/files/usr/libexec/proot
```

Đặt binary và hai loader cùng bản `.86` trong thư mục riêng nêu trên. Không chạy `make install`. Source, patch, binary và loader đã lưu trong archive Firefox dưới đây.

## Phiên thử :3

Đổi fullscreen làm viewer Termux:X11 nối nhầm phiên Openbox thử nghiệm `:3`. Source bản cài `caa7553` dùng một viewer và các server cùng gửi Binder kết nối. Người dùng đã **cho phép đóng riêng :3**. Đã kiểm tra command/UID rồi gửi TERM đúng PID `841` ngày 19/11; X server `:2` giữ nguyên. Không tự khởi động lại :3; không đụng :1/Ubuntu. [Bằng chứng đóng phiên đã được phép](../../artifacts/mojave-20261119/authorized-close-test-display3.txt).

## File và sao lưu

- Source Windows: `scripts/style-tablet-xfce.py`, `scripts/firefox-tablet.py`, `scripts/proot-firefox-sandbox.patch`, `scripts/check-firefox-seccomp.c`, `scripts/minimal-launcher/linux-resume.sh`.
- Debian: `/root/.local/share/linux-desktop/`; CSS tại profile `gtk-3.0/gtk.css`, launcher tại `xfce4/panel/`, helper tại `/root/.local/share/xfce4/helpers/firefox-tablet.desktop`.
- Trước sửa dock: `/root/.local/share/linux-desktop/backups/20261120-dock-reveal/before.tar`, gồm CSS, XML panel và script trước sửa; `state.json` ghi mode cũ `2`.
- Bản đang chạy: cùng thư mục, `working.tar.gz`; chứa XFCE/CSS/launcher, theme/icon, wallpaper và script, không chứa profile Mozilla/cookie/lịch sử.
- Windows đã nhận và kiểm tra nội dung + SHA256 trùng thiết bị:
  - `snapshots/xfce-dock-20261120-before.tar`
  - `snapshots/xfce-style-20261120-working.tar.gz`
  - `snapshots/firefox-sandbox-20261120-working.tar.gz`
- Cấu hình viewer: `snapshots/termux-x11-20261120-working.xml`; bản trước thay đổi tại `snapshots/termux-x11-before-responsive-20261119.xml`. [Hash và đường dẫn native](../../artifacts/dock-reveal-20261120/backup-manifest.json).

Không giải nén XML/XFCE đè lên phiên đang chạy. Rollback dock qua Xfconf và CSS đã backup; khôi phục toàn profile khi phiên/xfconfd đã dừng có kiểm soát. Khôi phục preference Termux:X11 bằng CLI/app thay vì ghi đè XML đang được app giữ trong bộ nhớ. Các archive `20261119-working` là mốc cũ trước Firefox/dock/co giãn mới.

Ngày 20/11 chỉ restart panel sau khi xác minh ownership; settings, WM và desktop giữ PID. Người dùng đã xác nhận dock gọi lại được sau sửa. Workspace không có Git; chưa commit/push.
