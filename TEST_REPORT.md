# Báo cáo kiểm thử

## Nghiệm thu mới nhất — 2026-11-19

Đã kiểm tra trực tiếp trên tablet: giao diện/dock, NetSurf HTTPS, terminal từ dock UID `10528`, Thunar, Mousepad mở/lưu, PDF/JPG, ZIP giải nén, Settings, Task Manager và clipboard. Người dùng xác nhận chạm menu, kéo cửa sổ và shortcut Resume từ Home đều hoạt động. `dpkg --audit` sạch; cấu hình live `--check` đạt. Firefox ESR: **BLOCKED**, tab crash vì font trong sandbox PRoot; không hạ sandbox. Cold Start/reboot/APK chưa kiểm chứng.

Bảng chi tiết và bằng chứng: [DESKTOP_COMPLETION_2026-11-19.md](handoff/claude-to-codex/DESKTOP_COMPLETION_2026-11-19.md). Toàn bộ kết quả M1/M2 và legacy bên dưới là lịch sử trước đợt triển khai này.

Ngày: 2026-11-18; cập nhật M1–M2: 2026-11-19. PASS chỉ khi có bằng chứng chạy thực tế; NOT VERIFIED không đồng nghĩa thất bại.

## Đính chính/pivot workstation M1–M2 — 2026-11-19

- Bằng chứng ngày 2026-11-18 trong mục “Nguyên nhân XFCE treo và cách chạy được” xác nhận phiên thủ công `:2` đã hiển thị và hoạt động tại thời điểm đó: D-Bus riêng qua `dbus-run-session`, `LIBGL_ALWAYS_SOFTWARE=1`, `xfwm4 --compositor=off`, thứ tự `xfsettingsd` → `xfwm4` → `xfdesktop` → `xfce4-panel` → `xfce4-terminal`. Người dùng xác nhận menu, gõ terminal và kéo cửa sổ ngày 2026-11-18. Điều này không xác minh launcher, wrapper `scripts/xfce-components.sh`, hay phiên hiện tại.
- Khảo sát chỉ đọc ngày 2026-11-19 thấy `termux-x11 :2` và `:3`; `xfsettingsd`, `xfwm4`, `xfdesktop`, `xfce4-panel` còn chạy. Không xác định quyền sở hữu các process; không signal hoặc dừng process. Danh sách process không chứng minh ảnh desktop hiện tại hoặc khả năng tương tác. Người dùng chưa xác nhận trực tiếp tình trạng hình ảnh/tương tác phiên hiện tại.
- Đọc environment qua `/proc/<pid>/environ` bị Android từ chối quyền (`Permission denied`). Không suy diễn các biến environment hiện tại. Hồ sơ cũ cho phiên đã kiểm chứng ghi `DISPLAY=:2`, `LIBGL_ALWAYS_SOFTWARE=1`, `XDG_CONFIG_HOME=/root/.ld-test/xfce-config`; cache/log/runtime riêng `/root/.ld-test/` đã dùng trong lần thử, nhưng không suy diễn chúng cho process đang chạy.
- Đọc chỉ trạng thái Debian `dpkg` read-only: `xfce4-whiskermenu-plugin`, `papirus-icon-theme`, `arc-theme`, `materia-gtk-theme`, `gtk2-engines-murrine`, `gtk2-engines-pixbuf` hiện không có trạng thái installed; `adwaita-icon-theme` có trạng thái `install ok installed`. Đây chưa phải khảo sát availability, dependency/dung lượng hay tương thích package; chưa chọn GTK theme. APK `com.termux` và `com.termux.x11` hiện cài; package launcher `dev.local.linuxdesktop.launcher` không cài. Không cài package/APK.
- Snapshot chỉ cấu hình `/root/.ld-test/xfce-config` được tạo trong workspace tại `snapshots/xfce-config-20261119T103201/xfce-config.snapshot.tar`, ACL thư mục giới hạn cho tài khoản Windows `TUNDUN\\PC`. Archive gồm 16 file thường (39,959 byte payload), không gồm cache/socket/runtime/log hay dữ liệu khác; SHA-256 archive `debf6dc6510598e9044bc3b1fe54d034613d3a1711d9f958c014264a8c31ce13`. Danh sách tương đối, kích thước và SHA-256 từng file trước/sau sao chép khớp. XFCE vẫn có thể ghi khi chạy nên archive không phải snapshot nhất quán tuyệt đối; thiết lập trong bộ nhớ chưa lưu có thể không được bao gồm. Không khôi phục archive lên phiên đang chạy.
- M1: **NOT VERIFIED**. Chưa có xác nhận trực tiếp phiên hiện tại và chưa cold start an toàn trong môi trường trống; không dừng phiên hiện có để tạo môi trường trống.
- M2: **NOT STARTED / NOT VERIFIED**. Chưa khảo sát package/theme hoàn tất, đọc tài liệu Debian/XFCE cho cấu hình mới, chuẩn bị cấu hình thử riêng hoặc áp dụng cấu hình. Không cài `xfce4-whiskermenu-plugin`, Papirus hay GTK theme; không đổi phiên/display.
- `scripts/xfce-components.sh` lưu thứ tự trên nhưng chưa được xác minh end-to-end. Script đặt XDG dưới `/root/.local/linux-desktop/{config,cache,run,logs}` (khác `/root/.ld-test/...` trong lần thử đã xác minh), chạy `dbus-run-session`, và trap gửi `TERM` đến PID con. Không chạy script trên phiên đang tồn tại. Điều kiện `--shared-tmp` cần thiết để PRoot client thấy X11 socket; lần thử đã xác minh dùng `proot-distro login --isolated --shared-tmp ...` và `DISPLAY=:2`. Cấu hình software GL và tắt compositor là điều kiện đã thử được; không thay GL toàn cục hay resolution.
- `scripts/desktop.py` có các nhánh hoạt động `start`, `stop`, `status`, `resume` tại thời điểm đọc `scripts/desktop.py:478-521`; vì vậy cảnh báo README cũ rằng manager bị vô hiệu không chính xác. Điều đó không chứng minh manager/launcher an toàn hoặc đã được xác minh; không chạy wrapper legacy trong pivot này.
- **Điều kiện trước cold start:** chỉ khi xác định chắc chắn display mục tiêu, owner của X11/WM và không có phiên khác bị ảnh hưởng; nếu có nghi ngờ thì dừng và xin phép cụ thể. Không xóa socket/lock, không signal process chưa xác minh. Snapshot không phải bản khôi phục tự động.

### M2 kiểm tra trực quan tablet (chưa chạy)

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Hình nền | NOT VERIFIED | Cấu hình mới chưa chuẩn bị/áp dụng. |
| Menu tối | NOT VERIFIED | Chưa cài/chọn theme hoặc xác minh menu. |
| Panel trên | NOT VERIFIED | Chưa thay đổi cấu hình đang chạy. |
| Dock giữa phía dưới | NOT VERIFIED | Chưa thay đổi cấu hình đang chạy. |
| Shortcut bên trái | NOT VERIFIED | Chưa cấu hình thử nghiệm. |
| Chữ/nút đủ lớn để chạm | NOT VERIFIED | Chưa kiểm tra trực quan. |
| Kéo/đóng cửa sổ | NOT VERIFIED | Lần thử lịch sử chỉ chứng minh kéo; xác nhận đóng cửa sổ cho cấu hình mới chưa có. |
| Cảm ứng | NOT VERIFIED | Chưa xác nhận phiên hiện tại/cấu hình mới. |
| Bàn phím/chuột | NOT VERIFIED | Chưa kiểm tra cấu hình mới. |

Không kết luận M1/M2 PASS từ các kết quả lịch sử. Các mục legacy TEST 01–13 bên dưới giữ nguyên làm lịch sử, không biểu thị nghiệm thu pivot.

| Kiểm tra | Kết quả |
|---|---|
| TEST 01: ADB và thiết bị | PASS: `f422eebd` device, Android 16/API 36, arm64-v8a. |
| TEST 02: Debian ARM64 | PASS: `uname -m` aarch64, Debian 13.7 trixie, `dpkg-query -W` xác nhận các gói yêu cầu. |
| TEST 03: XFCE | PASS (không có `xfce4-session`): xfwm4, xfdesktop, panel, terminal trên `:2`; xem mục nguyên nhân bên dưới. |
| TEST 04: Desktop trên Termux:X11 | PASS: ảnh chụp tablet 17:12. |
| TEST 05: Build/cài/icon | NOT VERIFIED |
| TEST 06: Mở bằng icon | NOT VERIFIED |
| TEST 07: Home/quay lại | NOT VERIFIED |
| TEST 08: Start đồng thời | NOT VERIFIED |
| TEST 09: Stop/Start | NOT VERIFIED |
| TEST 10: Reboot | NOT VERIFIED — cần xác nhận của người dùng trước khi reboot. |
| TEST 11: Không ADB/PC | NOT VERIFIED — cần xác nhận và thao tác của người dùng. |
| TEST 12: Cảm ứng/bàn phím | PASS (người dùng xác nhận trên tablet 2026-11-18): menu bằng cảm ứng, kéo cửa sổ, gõ terminal. Phiên chạy thủ công, chưa qua manager. |
| TEST 13: lỗi, dọn process và phục hồi khi HyperOS kết thúc phiên | NOT VERIFIED |

## Kiểm thử thủ công trên tablet — 2026-11-18

- Debian: `aarch64`, `/etc/debian_version` `13.7`; có `xfce4-session`, `dbus-launch`, `xdpyinfo`, `xfce4-terminal`.
- `:2`: trước khi chạy không có lock/socket filesystem; bind tạm thời thành công abstract X11 và TCP IPv4/IPv6. Đây là kiểm tra tại một thời điểm, không phải đặt chỗ.
- Termux:X11 chạy foreground qua ADB trên `:2`; Debian `xdpyinfo` kết nối được. Log X11 chỉ ghi cảnh báo keymap `xkbcomp`, nói rõ lỗi này không fatal.
- `proot-distro login --isolated --shared-tmp --env DISPLAY=:2 debian -- dbus-launch --exit-with-session xfce4-session` đang chạy foreground qua ADB. `xfce4-session` và D-Bus xuất hiện trong danh sách process. `xprop -root _NET_SUPPORTING_WM_CHECK` báo `no such atom on any window`; chưa xác minh window manager hoặc desktop.
- Đã gửi intent mở `com.termux.x11/.MainActivity`; Android báo activity đã ở top. Ảnh chụp sau đó xác minh cửa sổ X11 thử nghiệm thực sự hiển thị; cảm ứng và terminal chưa được xác minh. Các process thử nghiệm chưa được dừng; `:1` được giữ nguyên.

## Chẩn đoán XFCE trên tablet

- Socket filesystem `:2` trả `SO_PEERCRED` PID 15917, UID 10528, khớp X11 server thử nghiệm đang chạy. Socket abstract `:2` trả `ECONNREFUSED`; Debian kết nối qua `/tmp` được chia sẻ. `xfce4-session` PID 16050 có `DISPLAY=:2` và `DBUS_SESSION_BUS_ADDRESS`; `XDG_RUNTIME_DIR` và `XAUTHORITY` không có trong environment process. Không thấy `xfwm4`, `xfce4-panel` hoặc `xfdesktop` trong danh sách process; `xprop` không thấy `_NET_SUPPORTING_WM_CHECK`.
- `xmessage` tạo cửa sổ `Linux Desktop X11 test` được `xwininfo` liệt kê trên `:2` và kết thúc exit 0. Chưa nhận xác nhận trực quan hoặc cảm ứng từ người dùng; không coi exit 0 là bằng chứng nhìn thấy.
- Query D-Bus của phiên XFCE hiện tại trả `NoReply` hai lần. Hai bus tạm độc lập bằng `dbus-run-session` và `dbus-launch` trả lời `ListNames` từ bên trong phiên tương ứng; truy vấn bus thử nghiệm từ PRoot khác cũng trả `NoReply`. Nguyên nhân chưa xác định; kết quả không chứng minh bus bị hỏng đối với client trong cùng PRoot. Chưa restart hoặc dừng phiên cũ. `xfce4-session`, `xfwm4`, `xfce4-panel`, `xfdesktop4`, `dbus-x11` đều có trạng thái package `ii`.
- **Hiển thị X11: PASS.** Ảnh chụp tablet `C:\Users\PC\AppData\Local\Temp\linux-desktop-display-test-20261118164018.png` cho thấy cửa sổ `X11 DISPLAY TEST - DEBIAN - DISPLAY :2` trong Termux:X11. Ảnh có thể chứa nội dung thiết bị; không công bố. Dialog sau đó thoát mã 0, nhưng không có xác nhận thao tác từ người dùng: **cảm ứng NOT VERIFIED**.
- Bus thử `dbus-run-session` trả lời `ListNames`; `xfwm4` PID 21688 được chạy trong PRoot thử nghiệm, nhưng sau 20 giây chưa có `_NET_SUPPORTING_WM_CHECK`; panel và desktop không được chạy. Kiểm tra sau đó: PID 21688 vẫn đang chạy, chờ futex, parent 21682; `xfce4-session` PID 16050 cũng chờ futex. Đây là lỗi lần thử, chưa xác định nguyên nhân. `dbus-daemon` ghi cảnh báo không tăng được giới hạn FD nhưng đã trả lời query ban đầu.
- `xfwm4 --version`, `xfce4-session --version` và `xfce4-terminal --version` từng hết timeout 8 giây; `xfconf-query --version` thành công. Chạy lại `xfwm4 --version` ba lần mặc định và ba lần với biến GL thử nghiệm đều thành công; chưa chứng minh nguyên nhân hoặc cách sửa. **WM, panel, desktop XFCE và nhập terminal: NOT VERIFIED.**

## Nguyên nhân XFCE treo và cách chạy được — 2026-11-18 17:12 (lịch sử, không phải xác minh phiên hiện tại)

- **Nguyên nhân:** futex của `xfce4-session` PID 16050 và `xfwm4` PID 21688 nằm trong vùng BSS ngay sau `libgallium-25.0.7-2+deb13u1.so` (Mesa). Cả hai đã nạp `libGLX_mesa`, `libvulkan`. Tái hiện độc lập trên `:3`: `glxinfo -B` mặc định timeout 20 giây hai lần; `LIBGL_ALWAYS_SOFTWARE=1` xong sau 3 giây (llvmpipe); `GALLIUM_DRIVER=softpipe` xong ngay; `LIBGL_ALWAYS_INDIRECT=1` lỗi `BadValue`. Kết luận: khởi tạo GL phần cứng của Mesa treo trong PRoot + Termux:X11 (server quảng bá DRI3/Present). Không phải lỗi D-Bus, machine-id hay cấu hình session.
- Không có `/etc/machine-id`; `/var/lib/dbus/machine-id` hợp lệ (32 hex). Không có `~/.cache/sessions` hay `~/.config/xfce4` trong Debian; không có session cũ để xóa. `/tmp` chia sẻ chứa nhiều socket `dbus-*`, `.ICE-unix/*`, `.xfsm-ICE-*` từ 23–24/07 thuộc phiên khác; không chạm.
- Termux có runit service `tx11` và `tx11-xfce4` (không thuộc dự án này); không chạm.
- **Openbox trên `:3`** (server mới PID 841, env sạch, XDG riêng): `_NET_SUPPORTING_WM_CHECK` có sau 1 giây; xterm chạy. Viewer Termux:X11 là single-instance và vẫn hiển thị `:2`, nên hiển thị Openbox **NOT VERIFIED**.
- **XFCE không dùng `xfce4-session` trên `:2`**: `dbus-run-session` mới, `LIBGL_ALWAYS_SOFTWARE=1`, XDG config/cache riêng `/root/.ld-test/`, log riêng `/root/.ld-test/logs/`. Thứ tự `xfsettingsd`, `xfwm4 --compositor=off` (WM sẵn sàng sau 16 giây), `xfdesktop`, `xfce4-panel`, `xfce4-terminal`. Log chỉ có cảnh báo AT-SPI, thiếu `SESSION_MANAGER`, thiếu system bus, thiếu DPMS; không crash.
- Ảnh chụp `C:\Users\PC\AppData\Local\Temp\ld-xfce-2.png` (có thể chứa nội dung riêng, không công bố): panel trên với Applications, đồng hồ; dock dưới; cửa sổ `XFCE TEST TERMINAL :2` có viền, nút đóng, prompt `root@localhost:~#`.
- Quy trình lưu tại `scripts/xfce-components.sh`.

| Nghiệm thu đồ họa | Kết quả |
|---|---|
| T01 X11 hiển thị | PASS (ảnh chụp) |
| T02 Window manager | PASS: xfwm4 công bố `_NET_SUPPORTING_WM_CHECK` 0xe00032, viền cửa sổ trong ảnh |
| T03 Desktop | PASS: cửa sổ `Desktop` 1280x960 của xfdesktop; nền đen, chưa có hình nền |
| T04 Panel/menu | PASS: panel và dock hiển thị; người dùng xác nhận mở menu Applications bằng cảm ứng (2026-11-18) |
| T05 Terminal mở | PASS: người dùng xác nhận gõ `echo hello` in ra `hello` (2026-11-18) |
| T06 Cảm ứng | PASS: người dùng xác nhận kéo cửa sổ terminal bằng cảm ứng; xfwm4 quản lý cửa sổ (2026-11-18) |
| T07 Ubuntu | PASS gián tiếp: không lệnh nào gọi container `ubuntu` hay `:1`; chưa đăng nhập Ubuntu kiểm tra |

## 16 kịch bản lifecycle yêu cầu

Các kết quả dưới đây tách biệt thử nghiệm WSL với tablet. Manager chưa chạy lifecycle thật; mọi mục chưa được xác minh trên tablet.

| Kịch bản | WSL | Tablet |
|---|---|---|
| 1. Start bình thường | NOT VERIFIED | NOT VERIFIED |
| 2. Stop bình thường | NOT VERIFIED | NOT VERIFIED |
| 3. Start lặp | NOT VERIFIED | NOT VERIFIED |
| 4. Stop lặp | NOT VERIFIED | NOT VERIFIED |
| 5. Start đồng thời | NOT VERIFIED | NOT VERIFIED |
| 6. Gián đoạn khi start | Một phần: thử gate trước/sau ghi state, không chạy desktop | NOT VERIFIED |
| 7. Gián đoạn khi stop | NOT VERIFIED | NOT VERIFIED |
| 8. PID cũ | NOT VERIFIED | NOT VERIFIED |
| 9. PID được tái sử dụng | Một phần: state từ boot trước không được signal; chưa thử PID reuse cùng boot | NOT VERIFIED |
| 10. Phiên PRoot không liên quan | NOT VERIFIED | NOT VERIFIED |
| 11. Phiên X11 không liên quan | Một phần: giữ socket/lock lạ, không thử phiên X11 thực | NOT VERIFIED |
| 12. Phiên Ubuntu | NOT VERIFIED | NOT VERIFIED |
| 13. XFCE lỗi một phần | NOT VERIFIED | NOT VERIFIED |
| 14. Display xung đột | Một phần: phát hiện abstract socket đang nghe hoặc đã bind, giữ lock lạ; chưa chứng minh độc quyền display | NOT VERIFIED |
| 15. Phục hồi sau crash mô phỏng | Một phần: gate thoát khi parent chết; chưa phục hồi phiên | NOT VERIFIED |
| 16. Ownership không rõ | Một phần: status/stop từ chối state không rõ, không signal PID thử nghiệm | NOT VERIFIED |

## Bằng chứng bổ sung

- PIDFD: Python Termux không có `os.pidfd_open`; syscall ARM64 434 (`pidfd_open`) và 424 (`pidfd_send_signal` với signal 0) đã thành công trên chính process thử nghiệm.
- Kiểm thử manager trên WSL: `python3 -m unittest discover -s /mnt/c/Users/PC/linux-desktop/tests -v`, 26 test PASS. Bao gồm khóa, trạng thái chỉ đọc, giữ state, từ chối ownership không rõ, thử gate, xử lý lỗi exec và giữ FD riêng. Helper chưa nối với Start thật. Không xác minh start/stop desktop; 16 kịch bản lifecycle chưa được bao phủ đầy đủ.
- Android Gradle offline `testDebugUnitTest assembleDebug --rerun-tasks`: 10 test PASS, 0 bỏ qua; build thành công. Test chỉ kiểm tra logic, không kiểm tra Android lifecycle hay tích hợp Termux thực. Start tự động từ icon đã bị vô hiệu để tránh app khác kích hoạt qua exported activity; một chạm chưa hoạt động. `apksigner` xác minh chữ ký v1/v2 và cảnh báo `META-INF/com/android/build/gradle/app-metadata.properties not protected by signature`. APK debug chưa cài và không phải sản phẩm hoàn tất.
