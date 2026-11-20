# XFCE và ứng dụng thiết yếu — 2026-11-19

> Mốc lịch sử trước Mojave/Firefox/co giãn. Trạng thái mới nhất và bản sửa dock ngày 20/11: [MOJAVE_FIREFOX_2026-11-20.md](MOJAVE_FIREFOX_2026-11-20.md).

## Kết quả hiện tại

Đã triển khai trên Xiaomi Pad 7 Pro qua ADB `f422eebd`, Debian 13 ARM64, phiên X11 `:2` đang có. Không tạo desktop thứ hai. Người dùng xác nhận **“Cả ba hoạt động”** cho chạm Whisker Menu, kéo cửa sổ và shortcut Resume từ Home trong phiên này.

Yêu cầu mới của người dùng cho phép hoàn thiện giao diện và cài ứng dụng ngay trên phiên hiện có; thay thế gate cũ yêu cầu Cold Start trước M2. Cold Start, reboot và APK riêng vẫn để sau. Các tài liệu bàn giao trước báo cáo này là lịch sử, gồm cả trạng thái APT và các giới hạn phê duyệt của nhiệm vụ bàn giao cũ.

**Giới hạn còn lại:** Firefox ESR đã cài, mở được cửa sổ nhưng tab crash vì `unable to find a usable font (serif)` trong PRoot. NetSurf tải được HTTPS và là trình duyệt mặc định cho web cơ bản. NetSurf không thay thế Firefox/Chrome cho ứng dụng web JavaScript phức tạp; cloud AI chưa được nghiệm thu.

## Cấu hình thực sự đã áp dụng

| Thành phần | Giá trị / vị trí |
|---|---|
| Profile đang dùng | `/root/.ld-test/xfce-config` |
| HOME | `/root`, giữ profile hiện có |
| Display | `:2`; GTK có thể chuẩn hóa thành `:2.0`, cùng server/screen |
| Render | `LIBGL_ALWAYS_SOFTWARE=1`; `xfwm4 --compositor=off`, xfconf `use_compositing=false` |
| Theme / icon | `Arc-Dark` / `Papirus-Dark` |
| Font / DPI | `Noto Sans 12`, `Noto Sans Mono 12`, XFCE DPI `120`, cursor `32` |
| Wallpaper | `/usr/share/backgrounds/xfce/xfce-blue.jpg`, gói XFCE sẵn có |
| Top panel | Cao `44`, icon `28`, Whisker + task list + tray + clock + Clipman |
| Bottom dock | XFCE panel cao `64`, icon `44`, luôn hiện; NetSurf / Terminal / Thunar / Settings / Mousepad |
| Clock | `Asia/Ho_Chi_Minh` |
| Terminal | Xfconf `/run-custom-command=true`, `/custom-command=/bin/bash`; tránh shell `nologin` của tài khoản Termux |
| Thư mục làm việc | `/root/Work`; file mẫu tại `/root/Work/desktop-check` |

Core XFCE vẫn thuộc PRoot cũ. Panel mới, ứng dụng từ dock và browser dùng UID Debian **10528**, tài khoản ánh xạ `aid_u0_a528`, không dùng UID giả `0`. HOME `/root` được giữ để dùng đúng profile; đây không phải Android root và PRoot không cung cấp cách ly quyền Android.

D-Bus trước đó từ chối UID giả root của client từ PRoot khác. Thêm `/etc/dbus-1/session.d/90-linux-desktop-termux.conf` chỉ cho phép UID `10528`, giữ xác thực `EXTERNAL`, không dùng wildcard/ANONYMOUS. Công cụ cấu hình đổi UID client về đúng UID Termux trước khi dùng `xfconf-query`.

Panel cũ không biết plugin mới cài và không nạp lại danh sách plugin từ xfconf trong bộ nhớ. Đã xác minh UID, profile, PRoot tracer và PID D-Bus của panel trước khi dùng `xfce4-panel --quit`, ghi cấu hình rồi thay riêng panel qua Appfinder thuộc PRoot cũ. Sau cài SVG loader, dùng `xfce4-panel --restart` để nạp icon. X server, window manager và desktop giữ nguyên; không dừng phiên Linux.

Resume sửa nhỏ: panel sau thay/nạp lại có thể đổi parent. Script vẫn bắt buộc UID, DISPLAY, profile, software rendering và PRoot tracer trùng phiên đã xác minh; giữ kiểm tra supervisor chung của settings/WM/desktop và PID/name của WM từ X11.

## Gói cài trong phiên

APT appearance cũ vẫn sống khi tiếp nhận, đang tạo cache icon Papirus rất chậm và chạy hai lượt theo postinst. Đã để giao dịch đó tự hoàn tất. Không kill, không xóa khóa, không chạy repair hoặc giao dịch cài cạnh tranh. Sau khi process kết thúc, kiểm tra khóa bằng `fcntl` và `dpkg --audit` sạch rồi mới cài tiếp.

Lệnh cài thực tế từ repository Debian đang cấu hình, không thêm nguồn:

```sh
apt-get -y --no-install-recommends install firefox-esr xdotool librsvg2-common unzip zip tumbler
apt-get -y --no-install-recommends install netsurf-gtk
```

Đã mô phỏng trước cài. Tổng cộng **14 gói mới**, không gỡ hoặc nâng cấp gói hiện có:

- `firefox-esr`, `libevent-2.1-7t64`, `librsvg2-common`, `libtumbler-1-0t64`, `libxdo3`, `tumbler`, `tumbler-common`, `unzip`, `xdotool`, `zip`.
- `netsurf-gtk`, `netsurf-common`, `fonts-dejavu`, `fonts-dejavu-extra`.

Arc/Papirus/Noto hoàn tất bởi giao dịch cũ. Whisker, Clipman, Mousepad, Atril, Ristretto, Engrampa, Task Manager, Thunar, Terminal và Settings đã có; không cài lại. SVG loader sửa icon Papirus thiếu hình. Tumbler cung cấp dịch vụ thumbnail cho Ristretto/Thunar; truy vấn D-Bus `GetFlavors` đạt.

## Nghiệm thu thực tế

| Mục | Đã cài | Đã cấu hình | Chạy / kiểm chứng | Bằng chứng trong `artifacts/desktop-20261119/` |
|---|---|---|---|---|
| XFCE / dark theme / dock | Có | Có | Đạt, ảnh thực tế và xác nhận cảm ứng | `workstation-final.png`, `tablet-window-menu.png` |
| Whisker | Có | Có | Mở menu, người dùng xác nhận chạm được | `whisker-ready.png`, `user-acceptance.md` |
| NetSurf | Có | Mặc định HTTPS, dock | Tải `https://example.com/`, nội dung và khóa HTTPS hiện; mở lại được từ dock | `netsurf-https.png` |
| Firefox ESR | Có | Giữ sandbox mặc định | **BLOCKED:** cửa sổ mở, tab crash; không đạt HTTPS | `browser-initial.png`, `firefox-font-fix.txt`, `browsers-final-diagnosis.txt` |
| Terminal | Có | Bash và font | Lệnh chạy từ terminal và từ dock; `id -u=10528` | `terminal-pass.png`, `dock-terminal-pass.txt` |
| Thunar | Có | Launcher / thư mục Work | Mở thư mục mẫu, thấy file; mở lại từ dock | `files-pass.png`, `dock-apps.png` |
| Mousepad | Có | Launcher / MIME | Mở, nhập, Ctrl+S; đọc lại nội dung file khớp | `editor-pass.png`, `editor-clipboard-check.txt` |
| Atril | Có | MIME PDF | Render đúng chữ của PDF mẫu, 1 trang | `pdf-pass.png` |
| Ristretto | Có | MIME JPG/PNG | Render ảnh JPG; thiếu thumbnail lúc đầu, sau đó đã cài Tumbler | `image-pass.png`, `viewers-open.png` |
| Engrampa | Có | MIME ZIP | Liệt kê file ZIP và giải nén; nội dung trích xuất khớp | `archive-and-associations-check.txt` |
| Settings | Có | Launcher | Hiện cửa sổ, mở lại từ dock | `settings-pass.png`, `dock-apps.png` |
| Task Manager | Có | Menu có sẵn | Hiện danh sách tiến trình và số liệu CPU/RAM | `core-apps.png` |
| Clipman | Có | Plugin top panel | Lưu đúng nội dung copy từ Mousepad | `clipboard-history.png` |
| Resume | Có | Chỉnh kiểm tra parent của panel | Direct script đạt; người dùng xác nhận bấm Home shortcut đạt | `resume-after-ui.txt`, `user-acceptance.md` |
| Package DB | Có | Giao dịch kết thúc | `dpkg --audit` rỗng, khóa apt/dpkg nhả | `final-device-check.txt` |

Một số ảnh đầu còn icon thay thế hoặc cảnh báo thumbnail vì chụp trước bổ sung SVG loader/Tumbler. Ảnh cuối thể hiện cấu hình hiện tại. Kiểm tra app dùng điều khiển X11 trên thiết bị thật, không suy PASS từ test Windows.

Crash Firefox: report ghi sandbox level `6`; thử duy nhất `gfx.e10s.font-list.shared=false` không sửa được, đã phục hồi mặc định. Không đặt `--no-sandbox`, `MOZ_DISABLE_*SANDBOX`, không hạ `security.sandbox.*`. Nguyên nhân sâu của lỗi mở font trong PRoot chưa xác định; log sandbox có hoạt động seccomp và các crash font. Firefox đã đóng qua giao diện sau chẩn đoán. Không lấy HTTPS của NetSurf làm PASS cho Firefox.

## File đã sửa / thêm

- Windows: `scripts/configure-tablet-xfce.py` mới; `scripts/minimal-launcher/linux-resume.sh` sửa kiểm tra parent của panel. Không sửa legacy lifecycle manager.
- Device: `/root/.local/share/linux-desktop/configure-tablet-xfce.py` bản đồng nhất source; `--check` là kiểm tra chạy lại, không ghi cấu hình.
- Device profile: `xfce4/xfconf/xfce-perchannel-xml/{xsettings,xfwm4,xfce4-panel,xfce4-desktop,xfce4-terminal}.xml`, launcher `15`, `23`, `24`, `xfce4/helpers.rc`, `mimeapps.list`; XFCE còn tự lưu các thiết lập runtime của ứng dụng.
- Device: `/root/.local/share/xfce4/helpers/netsurf.desktop`; D-Bus rule nêu trên; Termux `/data/data/com.termux/files/home/.shortcuts/linux-resume.sh`.
- Hồ sơ Firefox mới do chính Firefox tạo dưới `/root/.ld-test/xfce-config/mozilla/firefox/`; không đưa browser profile/minidump vào bản sao lưu giao diện cuối.
- File chạy một lần và terminalrc thử nghiệm lỗi thời đã **chuyển vào backup**, không để launcher cũ có thể vô tình chạy lại. XFCE Terminal 1.1.4 dùng Xfconf; terminalrc không phải source cấu hình hiện tại.

## Bản sao lưu / phục hồi

Trên Debian:

- `/root/.local/share/linux-desktop/backups/20261119-before-ui/xfce-config.tar` — trước mọi thay đổi giao diện, SHA-256 `73e34daac42fffe400db4f278f5218bbabcb8465db6a9445330456f48d7f951b`.
- `/root/.local/share/linux-desktop/backups/20261119-tablet-ui/xfce-config.tar` — trước ghi bộ thiết lập, SHA-256 `0de49b161b457d49f584beab805da5ada2315b835a4ea6afaa89b0b75bb9ffb1`.
- `/root/.local/share/linux-desktop/backups/20261119-tablet-ui/tablet-ui-working.tar` — giao diện đang dùng; gồm XFCE, Thunar và MIME, không gồm Mozilla. SHA-256 `c99923724b34d3d1016135d1bb08b8b39a0b244abe5227b129209e72c0c52e28`.
- Cùng thư mục có export xfconf trước sửa, package inventory, bản rule/helper đã áp dụng và các file thử nghiệm đã ngừng dùng.

Trên Termux: `/data/data/com.termux/files/home/.local/share/linux-desktop/backups/20261119-ui/linux-resume.sh` là shortcut nguyên bản trước sửa.

Bản Windows tại `snapshots/xfce-config-20261119-before-ui.tar`, `snapshots/xfce-config-20261119-tablet-ui-before.tar`, `snapshots/xfce-config-20261119-working.tar`; hash đã đối chiếu với thiết bị. Giữ nguyên snapshot cũ `xfce-config-20261119T103201/`.

Phục hồi có chọn lọc:

1. Tạo thư mục kiểm tra riêng bằng `mktemp -d`; giải nén archive vào đó và so sánh trước. Các archive đều có thư mục `xfce-config/` ở đầu.
2. Muốn phục hồi toàn bộ file cấu hình: chỉ thực hiện khi không còn XFCE hoặc xfconfd dùng profile này; không ghi đè khi phiên vẫn chạy. Sao lưu các chỉnh sửa mới của người dùng trước, rồi giải nén archive đã chọn vào `/root/.ld-test` bằng `tar --no-same-owner -xf <archive> -C /root/.ld-test`. File launcher mới còn dư không được tham chiếu bởi layout cũ; không cần dọn xóa.
3. Khôi phục riêng Resume bằng bản Termux backup sau khi so sánh với script hiện tại; giữ mode `700`. Bản cũ yêu cầu panel cùng parent nên không phù hợp panel đang chạy sau lần thay này; phục hồi cùng layout/session tương ứng.
4. Rule D-Bus và helper NetSurf là file mới. Nếu quay về thiết lập trước toàn bộ, giữ bản sao rồi đổi đuôi rule từ `.conf` sang `.disabled` trước phiên mới; không gỡ rule khi phiên hiện tại còn cần nó.
5. Rollback giao diện không cần gỡ các gói đã cài. Snapshot lấy từ file đang sống, không phải ảnh bộ nhớ/backup nguyên hệ thống; thay đổi chưa lưu lúc chụp có thể không nằm trong archive.

## Lệnh kiểm tra đã chạy đạt

Từ Windows PowerShell, ADB dùng executable tại `C:\Users\PC\AppData\Local\Android\Sdk\platform-tools\adb.exe`. Mẫu vào Debian:

```powershell
& 'C:\Users\PC\AppData\Local\Android\Sdk\platform-tools\adb.exe' -s f422eebd shell 'run-as com.termux env PATH=/data/data/com.termux/files/usr/bin:/system/bin /data/data/com.termux/files/usr/bin/proot-distro login --isolated --shared-tmp debian -- python3 /root/.local/share/linux-desktop/configure-tablet-xfce.py --check'
```

Kết quả: `PASS: live XFCE settings verified on :2; compositor off; backup: /root/.local/share/linux-desktop/backups/20261119-tablet-ui`.

Resume hiện có, chỉ mở lại phiên đang chạy:

```powershell
& 'C:\Users\PC\AppData\Local\Android\Sdk\platform-tools\adb.exe' -s f422eebd shell 'run-as com.termux env PATH=/data/data/com.termux/files/usr/bin:/system/bin /data/data/com.termux/files/usr/bin/sh /data/data/com.termux/files/home/.shortcuts/linux-resume.sh'
```

Kết quả: `RESUME_REQUESTED: existing XFCE on :2; no desktop process started.`

Không sử dụng PID trong các log làm đầu vào lệnh kill/restart về sau. Không chạy lại `configure-tablet-xfce.py` không tham số trên profile đã tùy chỉnh: script chặn nếu backup đã tồn tại; dùng `--check`.

## Giới hạn và việc tiếp theo

- Cảm ứng menu, kéo cửa sổ và shortcut Home đã được người dùng xác nhận. Độ thoải mái về DPI/cỡ nút, bàn phím vật lý và dùng lâu dài chưa được nghiệm thu riêng.
- Firefox/JavaScript web hiện đại là việc còn lại cần chẩn đoán giới hạn PRoot; NetSurf chỉ đáp ứng web cơ bản.
- Cold Start, reboot và APK Android riêng chưa kiểm chứng, không phải điều kiện hoàn thiện giao diện phiên này. Không sửa manager legacy, không chạy test suite cũ làm gate.
- Android vẫn `2136x3200`, density `440`; X11 vẫn `1280x960`. Không đổi `wm size`/density, không thử GPU, không can thiệp `:1`, Ubuntu hoặc server `:3`.
- Wi-Fi, Bluetooth, độ sáng và pin do HyperOS quản lý; không cài NetworkManager. Ứng dụng GTK vẫn ghi cảnh báo thiếu accessibility bus; không tắt cơ chế hỗ trợ tiếp cận. Nghiệm thu trên đây không bao gồm công cụ đọc màn hình.
- Workspace không có Git: không commit/push, không tuyên bố clean tree. Các thay đổi và bằng chứng lưu tại các đường dẫn nêu trên.
