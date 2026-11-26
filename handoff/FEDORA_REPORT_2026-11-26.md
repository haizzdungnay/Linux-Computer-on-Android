# Báo cáo triển khai Fedora 45 ARM64 + XFCE trên Xiaomi Pad 7 Pro

**Ngày:** 2026-11-26  
**Thiết bị:** Xiaomi Pad 7 Pro (`adb -s f422eebd`, `aarch64`, màn hình `2136×3200`, density `440`)  
**Workspace nguồn:** `c:\Users\PC\linux-desktop`  

---

## 1. Nguồn gốc image & viewer (SHA-256)

| Thành phần | Nguồn / Gói | Phiên bản | Kích thước | SHA-256 |
| --- | --- | --- | --- | --- |
| Container `fedora45` | `registry.fedoraproject.org/fedora:45` (`aarch64`) | Fedora Linux 45 Container Image (`dnf5 5.4.8.0`) | Layer `70,439,009` bytes | OCI index: `sha256:806e6bc4b2f302baca3b0f53382416888f6ad46476063a2b47e72fc29968ae25`<br>ARM64 manifest: `sha256:7b52f8ed7b0d68cb985fe542a3c270d763e3c7e2641d3e8ad3d93dffe56c93ca`<br>ARM64 layer: `sha256:649bd1afa6083293e14362e6359512948a9686b2e67976d950d2f56c2e59e1c` |
| VNC Viewer APK | `artifacts/fedora45-20261126/AVNC-3.3.1.apk` *(cài cục bộ, bỏ qua trên Git)* | `com.gaurav.avnc` `3.3.1` (`versionCode=53`, `minSdk=21`, `targetSdk=36`) | `7,425,866` bytes | `61cb507e9f334f0276eacc8e9574bae6934d18e59c96b49f900a1183637d8f88` |

> **Bảo mật VNC:** Mật khẩu `VncAuth` ngẫu nhiên 8 ký tự chỉ lưu nội bộ (`chmod 600`) tại `fedora45:/root/.local/share/fedora45-desktop/vnc.passwd` và cấu hình profile `"Fedora"` (`127.0.0.1:5907`) trong AVNC; không ghi mật khẩu vào log hay báo cáo. File APK tạm `/sdcard/Download/AVNC-3.3.1.apk` trên tablet đã được xóa sau khi cài.

---

## 2. Các gói chính đã cài trong `fedora45`

- **Desktop XFCE 4.20 & X11/VNC:** `xfce4-session-4.20.4-2.fc45.aarch64`, `xfwm4-4.20.0-5.fc45.aarch64`, `xfdesktop-4.20.2-2.fc45.aarch64`, `xfce4-panel-4.20.8-4.fc45.aarch64`, `xfce4-settings-4.20.5-2.fc45.aarch64`, `xfce4-terminal-1.2.0-2.fc45.aarch64`, `Thunar-4.20.10-2.fc45.aarch64`, `tigervnc-x11-server-1.16.2-9.fc45.aarch64`, `wmctrl`, `zenity`, `dbus-daemon`, `pulseaudio-utils-17.0-11.fc45.aarch64`, `gdk-pixbuf2-2.44.8-3.fc45.aarch64`, `glycin-libs-2.2.6-1.fc45.aarch64`, `libglvnd-gles-1.7.0-10.fc45.aarch64`
- **Quản lý gói GUI (`dnf5daemon`):** `dnfdragora-2.99.4-3.fc45.noarch`, `dnf5daemon-server-5.4.8.0-2.fc45.aarch64`, `polkit-127-5.fc45.aarch64`
- **Văn phòng & lập trình:**
  - `libreoffice-writer-26.8.3.1-2.fc45.aarch64`, `libreoffice-calc-26.8.3.1-2.fc45.aarch64`, `libreoffice-impress-26.8.3.1-2.fc45.aarch64`, `libreoffice-gtk3`
  - Microsoft VS Code ARM64 RPM: `code-1.148.0-1795525969.el8.aarch64` (repo `/etc/yum.repos.d/vscode.repo`)

---

## 3. Kiến trúc cô lập & bảo toàn môi trường cũ

Tất cả tài nguyên của Fedora 45 được tách riêng hoàn toàn khỏi Debian/Ubuntu và Termux:X11 hiện có:

- **Container:** `proot-distro login --isolated --bind <runtime>:/tmp fedora45` (thư mục runtime riêng `$PREFIX/tmp/f45-work-*`, chế độ `0700`, không dùng `--shared-tmp`).
- **Display & Viewer:** `Xvnc :7` chỉ lắng nghe loopback `127.0.0.1:5907` (`1600×1068`, `-depth 24`, `-dpi 120`, `-SecurityTypes VncAuth`), kết nối qua `com.gaurav.avnc` (`vnc://?ConnectionName=Fedora`).
- **Profile & Cache:** `XDG_CONFIG_HOME=/root/.config/fedora45-xfce`, `XDG_CACHE_HOME=/root/.cache/fedora45-xfce`, `XDG_RUNTIME_DIR=/tmp/xdg-run`.
- **Audio:** Tiến trình `pulseaudio` riêng (`module-sles-sink sink_name=fedora_tablet`) gắn vào vòng đời phiên, lắng nghe trên cổng TCP loopback ngẫu nhiên với `pulse-cookie` 256 byte per-session.
- **Khóa đơn phiên:** [fedora-workstation.py](../scripts/fedora45/fedora-workstation.py) dùng `fcntl.flock` trên `~/.local/share/fedora45-desktop/workstation.lock`, `start_new_session=True`, và `reap_pgid()` trong `finally:`.
- **Script triển khai:**
  - Termux: [fedora.sh](../scripts/fedora45/fedora.sh) (`~/.shortcuts/fedora.sh`), [fedora.sh.png](../scripts/fedora45/fedora.sh.png) (`~/.shortcuts/icons/fedora.sh.png`), [fedora-workstation.py](../scripts/fedora45/fedora-workstation.py) (`~/.local/share/fedora45-desktop/fedora-workstation.py`) — tách riêng khỏi `linux-resume.sh` của Debian.
  - Bên trong `fedora45:/root/.local/share/fedora45-desktop/`: [fedora-session.sh](../scripts/fedora45/fedora-session.sh), [bwrap-shim.py](../scripts/fedora45/bwrap-shim.py), [system-dbus.conf](../scripts/fedora45/system-dbus.conf), [fedora-power.py](../scripts/fedora45/fedora-power.py)
  - Polkit & Desktop entries: [49-fedora45-dnf5.rules](../scripts/fedora45/49-fedora45-dnf5.rules), [fedora-power.desktop](../scripts/fedora45/fedora-power.desktop) (`Tắt Fedora`), [code.desktop](../scripts/fedora45/code.desktop) (`SHELL=/bin/bash`)

### Kiểm tra bảo toàn sau khi hoàn tất
- `proot-distro list`: vẫn giữ nguyên `debian`, `fedora45`, `ubuntu`.
- Socket Termux:X11 `:2` vẫn nguyên vẹn: `srwxrwxrwx. 1 u0_a528 u0_a528 0 Nov 18 16:21 /data/data/com.termux/files/usr/tmp/.X11-unix/X2`.
- Hiển thị Android không đổi: `Physical size: 2136x3200`, `Physical density: 440`.
- `~/.shortcuts/linux-resume.sh` và `~/.termux/termux.properties` không bị chỉnh sửa.

---

## 4. Kết quả kiểm thử chức năng

| Hạng mục | Kết quả | Bằng chứng / Ghi chú |
| --- | --- | --- |
| Cold start & auto-login AVNC | Đạt | Desktop XFCE `1600×1068` tự kết nối AVNC sạch ([01-desktop-avnc.png](../artifacts/fedora45-20261126/01-desktop-avnc.png)) |
| Bấm song song nhiều lần (`3× fedora.sh`) | Đạt | `Xvnc :7 count: 1`, `proot fedora45 count: 1` |
| Âm thanh PulseAudio | Đạt | Sink `fedora_tablet` (`module-sles-sink.c`, `s16le 2ch 44100Hz`), `pactl set-sink-volume` `50%/100%` + `paplay` -> `PAPLAY_OK` |
| `dnf` CLI (`install` / `remove tree`) | Đạt | `DNF_CLI_RC=0` |
| `dnfdragora` GUI (`install` & `remove tree`) | Đạt | Cài qua UI `Transaction completed ✓` (`tree-2.3.1-2.fc45.aarch64`, [02-dnfdragora.png](../artifacts/fedora45-20261126/02-dnfdragora.png)) và gỡ qua UI (`DNFDRAGORA_REMOVE_OK`) |
| Microsoft VS Code ARM64 | Đạt | Mở, sửa & lưu `/root/fedora-test-ws/hello.txt` (`edited in vscode on fedora45`), terminal tích hợp chạy `bash` (`Fedora release 45 (Forty Five)`) ([03-vscode.png](../artifacts/fedora45-20261126/03-vscode.png)) |
| XFCE Settings & Thunar | Đạt | Settings + 4 panel con (`Appearance`, `Display`, `Keyboard`, `Mouse`) mở ổn (`SUBPANEL_OK`); Thunar `/root/fedora-test-ws` hiển thị sidebar, path bar & file `hello.txt` sạch ([04-settings-thunar.png](../artifacts/fedora45-20261126/04-settings-thunar.png)) |
| LibreOffice Writer 26.8 | Đạt | Giao diện soạn thảo `26.8.3.1` hiển thị đầy đủ thanh công cụ & trang giấy ([05-libreoffice.png](../artifacts/fedora45-20261126/05-libreoffice.png)) |
| Tắt an toàn (**Tắt Fedora**) | Đạt | Khi có Mousepad chưa lưu: `fedora-power.py --yes` trả mã `2` (`KEPT_OPEN`) giữ phiên; sau khi đóng app: `LOGOUT_SENT`, `{"running": false}`, không còn tiến trình Fedora |

---

## 5. Benchmark tại `1600×1068` & khuyến nghị viewer

| Chỉ số | Giá trị đo | Ghi chú |
| --- | --- | --- |
| Cold start (3 lần) | `19.74s`, `19.48s`, `18.43s` | **Trung vị: `19.48s`** (tới `xfce-ready` + VNC lắng nghe + mở AVNC) |
| Resume khi phiên đang chạy (3 lần) | `2.26s`, `1.97s`, `1.86s` | **Trung vị: `1.97s`** |
| Idle CPU hệ thống sau sửa `0555` | **`92.1%` idle** (`7.9%` active trên `800%cpu`, `top -b -n 2 -d 3`) | Không có tiến trình XFCE/PRoot nào lọt top 12 CPU ngoài `pulseaudio` (`3.3%` của 1 core) |
| RAM thiết bị lúc idle sạch (`free -h`) | Total `7.4Gi`, Used `5.1Gi`, Free `228Mi`, Buff/Cache `2.0Gi`, Available `1.9Gi`, Swap used `3.1Gi / 8.0Gi` | Tổng RSS 26 tiến trình Fedora 45: **`522,920 KB` (`~510.7 MiB`)** (lớn nhất: `Xvnc` 73.0 MB, `xfce4-session` 59.6 MB, `pulseaudio` 53.0 MB, `xfdesktop` 48.3 MB, `Thunar --daemon` 34.9 MB, `xfce4-panel` 33.8 MB) |
| Burst VS Code (gõ 300 ký tự + cuộn 40 lần) | `11.90s` (`95.3%` Android CPU tổng) | *Đo trước khi áp dụng bản vá `chmod 0755` cho `rootfs` (khi còn lỗi `IN_ATTRIB` làm nền CPU cao)* |

### Khuyến nghị viewer
- **Giữ AVNC + Xvnc (`127.0.0.1:5907`) làm mặc định:** Khởi chạy 1 chạm độc lập hoàn toàn với Termux:X11 `:2`, không tranh chấp focus/biến `DISPLAY`, hỗ trợ cảm ứng trực tiếp, bàn phím vật lý, clipboard VNC và giữ nguyên tỷ lệ `1600×1068` sắc nét.
- **Termux:X11 (tùy chọn nâng cao sau này nếu cần FPS cao):** Chỉ nên dùng trên một display mới riêng biệt (ví dụ `:4` với app/activity tách biệt, tuyệt đối không chạm `:1`/`:2`/`:3`), vì VNC hiện tại đã gọn, ổn định và không ảnh hưởng phiên Debian.

---

## 6. Các vấn đề PRoot đặc thù đã xử lý

1. **Bão `inotify IN_ATTRIB` do quyền `/` `0555` (Nguyên nhân gốc làm Thunar đơ & CPU cao):** Image container Fedora 45 tạo thư mục gốc `/` ở chế độ `0555` (`dr-xr-xr-x`). Khi `proot --change-id=0:0` thực thi `faccessat("/", W_OK)`, PRoot `fake_id0` tạm `chmod` thành `0755` rồi trả lại `0555`, phát ra ~10.000 sự kiện `IN_ATTRIB` (`0x40000004`) mỗi giây tới `Thunar`/`xfdesktop`, làm nghẽn vòng vẽ GTK3 của Thunar và tăng tải CPU. Đã sửa bằng `chmod 0755` trên `fedora45/rootfs` và thêm `ensure_writable_rootfs()` trong [fedora-workstation.py](../scripts/fedora45/fedora-workstation.py) để tự bảo vệ sau mỗi lần nâng cấp gói `filesystem`.
2. **Deadlock `%transfiletriggerin` của `dnf5` trong PRoot:** Cài bộ icon quá lớn khiến `proot 5.1.107.86` giữ fd pipe khiến `dnf5` treo ở `pipe_write`. Đã bỏ qua `papirus-icon-theme`, cài theo lô nhỏ và chạy cập nhật cache trực tiếp.
3. **`glycin` + `bwrap` trong Fedora 45:** `gdk-pixbuf2` gọi `bwrap --unshare-all` vốn lỗi dưới PRoot. Đã thêm [bwrap-shim.py](../scripts/fedora45/bwrap-shim.py) (đưa vào `PATH` của phiên, không sửa `/usr/bin/bwrap`) để `glycin` fallback sạch sang chế độ không sandbox, kết hợp `GLYCIN_DISABLE_SANDBOX=1`.
4. **GTK4 (`dnfdragora`) thiếu GLES:** Đã cài `libglvnd-gles` và đặt `GSK_RENDERER=cairo` trong [fedora-session.sh](../scripts/fedora45/fedora-session.sh).
5. **Dọn nhóm tiến trình & D-Bus:** Đã thêm `NO_AT_BRIDGE=1`, ẩn autostart `xfce-polkit.desktop`, và thêm `reap_pgid()` vào `finally:` của [fedora-workstation.py](../scripts/fedora45/fedora-workstation.py) để tránh daemon con sống sót khi tắt phiên *(lưu ý: `reap_pgid()` được xác minh theo code; lần khởi động lại cuối dùng lệnh dọn trước khi mở phiên mới)*. Do cơ chế `SO_PEERCRED` của PRoot, mọi lệnh điều khiển D-Bus (`fedora-power.py`, `dnfdragora`) cần chạy từ bên trong phiên đang chạy (icon Desktop / Menu / Terminal trong Fedora), không gọi trực tiếp từ `proot-distro login` bên ngoài.

---

## 7. Danh sách kiểm tra thực tế trên tablet (dành cho bạn)

Các mục dưới đây cần thao tác trực tiếp bằng tay trên Xiaomi Pad 7 Pro vì không thể giả lập trọn vẹn qua ADB:

- [ ] Thêm widget **Termux:Widget** ra màn hình chính Android, rút cáp USB và bấm **`fedora.sh`** khi Debian `:2` **đang chạy** và khi Debian `:2` **đã tắt**, xác nhận cả hai trường hợp đều mở thẳng vào AVNC mà không làm ảnh hưởng Debian `:2`.
- [ ] Gõ thử tiếng Việt / tiếng Anh trong **VS Code** và **LibreOffice Writer** bằng bàn phím rời / cảm ứng, thử cuộn bằng ngón tay hoặc trackpad xem độ mượt thực tế.
- [ ] Mở âm thanh từ Fedora để kiểm tra âm lượng thực tế qua loa ngoài / tai nghe của Xiaomi Pad 7 Pro.
- [ ] Tắt màn hình tablet (sleep vài phút) rồi mở lại, xác nhận AVNC tự kết nối lại mượt với phiên Fedora đang chạy.
- [ ] Mở một file có chỉnh sửa chưa lưu (ví dụ Mousepad/Writer), bấm icon **Tắt Fedora** trên Desktop để kiểm tra hộp thoại tiếng Việt xác nhận giữ phiên; sau đó lưu/đóng rồi bấm **Tắt Fedora** lại để tắt sạch.
