# Mojave và Picom trên Xiaomi Pad 7 Pro · 20/11/2026

Debian 13 ARM64 trên display `:2.0`, profile `/root/.ld-test/xfce-config`, giao diện X11 1600 × 1068. Xfwm4 PID 5146, panel PID 1293, X11 server PID 15917 và viewer PID 25973 giữ nguyên trong các lượt thử. Trạng thái bàn giao **Effects Off**, selection `_NET_WM_CM_S0` bằng `0x0`. [Kiểm tra Debian](../../artifacts/xfce-effects-20261120/final-debian.txt) · [Kiểm tra Android](../../artifacts/xfce-effects-20261120/final-android.txt)

## Theme và icon

Mẫu Diolinux dùng Mojave Dark và WhiteSur Dark trên XFCE. Cặp theme đó đã được áp dụng đúng trên máy từ vòng trước, nên giữ bản đang dùng và xác minh lại thay vì ghi đè cùng commit. Đã đọc `README.md`, `install.sh`, `config.sh`, hai script dựng GResource, các script tạo asset nút nhỏ và bản cài riêng WhiteSur dùng từ vòng trước. HEAD của hai repo tác giả trùng commit trong các archive đã lưu. [Mẫu Diolinux](https://plus.diolinux.com.br/t/linux-mint-20-2-com-xfce/41173) · [Hồ sơ cài trước](MOJAVE_FIREFOX_2026-11-20.md)

| Thành phần | Bản đang áp dụng | Thư mục |
| --- | --- | --- |
| GTK và Xfwm4 | [`Mojave-Dark-solid`](https://github.com/vinceliuice/Mojave-gtk-theme/tree/eff102568e7aa712e7cb1f246002731a1ac32c2f), commit `eff102568e7aa712e7cb1f246002731a1ac32c2f` | `/root/.themes/Mojave-Dark-solid` |
| Icon | [`WhiteSur-dark`](https://github.com/vinceliuice/WhiteSur-icon-theme/tree/73d8040da51a9ed74e47c7366e7e9ff437601a5c), commit `73d8040da51a9ed74e47c7366e7e9ff437601a5c`, kế thừa `WhiteSur` và `hicolor` | `/root/.local/share/icons/WhiteSur-dark` |

GTK tìm được icon cho cả chín launcher dock. Nút đóng, phóng to và thu nhỏ dùng asset bản thường 24 × 28 px. Whisker, popup Mousepad và cửa sổ mẫu hiển thị đủ chữ và icon trong cảnh kiểm tra. GTK3 có cảnh báo parser CSS Mojave ngay ở mốc tắt Picom, trong khi menu và cửa sổ được thử vẫn vẽ đúng. Độ dễ bấm trực tiếp trên tablet cần anh xác nhận. [Kiểm tra icon](../../artifacts/xfce-effects-20261120/theme-icon-check.txt) · [Desktop và menu](../../artifacts/xfce-effects-20261120/so-sanh-desktop-menu.jpg) · [Cửa sổ và popup](../../artifacts/xfce-effects-20261120/so-sanh-cua-so.jpg)

## Hiệu ứng và hiệu năng

Picom `12.5-1` từ Debian trixie `stable/main`. Giải nén gói và sáu thư viện còn thiếu vào `/root/.local/share/linux-desktop/picom-xfce` để tránh mục autostart mà gói mang theo. Đã đối chiếu `--version`, `--help` và man page đi kèm. X server có Composite, Damage, XFixes, Render, Shape và Sync. Picom chạy với `--backend xrender`, `LIBGL_ALWAYS_SOFTWARE=1`, Xfwm4 `--compositor=off`. [Gói và help](../../artifacts/xfce-effects-20261120/picom-package-and-help.txt) · [Cấu hình](../../scripts/picom-xrender.conf) · [Debian Picom](https://packages.debian.org/trixie/picom)

- Bóng mềm bán kính 12 px, opacity bóng 0,43, áp dụng cho cửa sổ thường và dialog. Fade mở/đóng đặt 150 ms. Video có nhiều khung trung gian ở khoảng 15,25 giây khi đóng và 17,53 giây khi mở. [Video H.264 18,71 giây](../../artifacts/xfce-effects-20261120/motion-picom.mp4)
- Panel và dock dùng opacity 94% cho cả cửa sổ panel, gồm chữ và icon. Chữ vẫn rõ trong ảnh. Khi dừng Picom, nền trở về màu đặc của CSS hiện tại. Blur, bo góc do Picom và trong suốt terminal đều tắt. [Ảnh bật rồi tự tắt](../../artifacts/xfce-effects-20261120/so-sanh-bat-tat.jpg)
- Lượt đầu đặt 12 giây và tự kết thúc. Đã sửa phép nhận dạng tiến trình vì `/proc/PID/exe` dưới PRoot có thể trỏ vào loader. Bản cuối đối chiếu start time, argv và bản đồ vùng thực thi, rồi gửi tín hiệu qua pidfd. Đã xác nhận tự tắt, khởi chạy lặp chỉ có một Picom và tắt từ ADB khi đã bỏ DISPLAY/D-Bus. [Kiểm tra cuối đường tắt](../../artifacts/xfce-effects-20261120/final-controls-retest.txt)

Hai lượt đo ghép cặp đều để yên 5 giây và kéo Mousepad 5 giây theo cùng quỹ đạo XTest. Bảng dùng cặp cuối, đơn vị theo hàng. [Log tắt](../../artifacts/xfce-effects-20261120/before-checks.txt) · [Log bật](../../artifacts/xfce-effects-20261120/picom-checks.txt)

| Phép đo | Tắt | Bật |
| --- | ---: | ---: |
| CPU toàn thiết bị khi rảnh | 15,27% | 20,20% |
| CPU toàn thiết bị trong lúc kéo | 47,91% | 46,23% |
| CPU riêng Picom, tính theo một lõi, khi rảnh / kéo | — | 0,20% / 15,23% |
| CPU X11 server, tính theo một lõi, khi rảnh / kéo | 4,39% / 40,46% | 4,19% / 38,66% |
| Mở Whisker, gồm lệnh và đo kiểm | 309 ms | 346 ms |
| Alt+Tab, có giữ Alt 250 ms và tính thời gian lệnh | 430 ms | 440 ms |

CPU toàn thiết bị dao động giữa hai cặp ngắn. CPU riêng Picom ở lần đo trước là 0,40% khi rảnh và 16,01% khi kéo. Cả hai chế độ kéo được 260 px theo trục dọc, cuộn có đổi dòng, mở popup, maximize và gọi dock được. Alt+Tab chuyển Mousepad → Terminal. Alt+Shift+Tab chuyển focus sang XID Firefox có sẵn trong cả hai chế độ. Các lệnh đo và ảnh không đo được độ trễ từ touchpad vật lý đến màn hình. [Ảnh cùng kịch bản](../../artifacts/xfce-effects-20261120/so-sanh-cua-so.jpg)

## Bật, tắt và quay lại

Mở **Whisker Menu**, gõ `Effects On` hoặc `Effects Off`, rồi Enter. Hai mục là launcher chạy tay trong `/root/.local/share/applications`. Đã nghiệm thu qua đúng menu. Giữ profile bàn giao ở trạng thái tắt, nền panel đặc và dock ẩn thông minh. [Ảnh menu](../../artifacts/xfce-effects-20261120/06d-effects-off-menu.png) · [Kiểm tra menu](../../artifacts/xfce-effects-20261120/effects-menu-check.txt)

Tắt qua ADB nếu giao diện mất phản hồi. Hai lần chạy liên tiếp chỉ dừng Picom đã xác minh ở lần đầu. Lệnh `status` dùng để kiểm tra selection sau khi giao diện lên lại.

```powershell
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
$prefix = '/data/data/com.termux/files/usr'
$debian = "run-as com.termux env PATH=$prefix/bin:/system/bin $prefix/bin/proot-distro login --isolated --shared-tmp debian --"
$control = '/root/.local/share/linux-desktop/picom-xfce/xfce-effects.py'
& $adb -s f422eebd shell "$debian /usr/bin/env -u DISPLAY -u DBUS_SESSION_BUS_ADDRESS /usr/bin/python3 $control off"
& $adb -s f422eebd shell "$debian /usr/bin/python3 $control status"
```

Bản sao trước thử trên tablet tại `/root/.local/share/linux-desktop/backups/20261120-xfce-effects/before.tar`. Bản Windows trùng SHA-256 `d93daf519f708015e92d49489d9e2c5c024fa5ca22db8650316dd2a60ffe03e0`. Nội dung CSS và các XML XFCE tại bàn giao khớp archive. Tắt Picom đủ để quay về giao diện mốc đầu. Các theme/icon từng dùng vẫn có trong `/usr/share/themes` và `/usr/share/icons`. [Bản sao Windows](../../snapshots/xfce-effects-20261120-before.tar)

## Input và Resume

KeyInterceptor bật, `pointerCapture=false` và `showMouseHelper=true`. Nút **R** đã mở menu desktop đúng vị trí trỏ khi Picom chạy bằng thao tác chạm Android qua ADB. Cuộn bằng wheel và chuyển cửa sổ bằng XTest đã chạy trong hai chế độ. Kết quả phần cứng Alt+Tab và Alt+Shift+Tab trước vòng này nằm trong báo cáo input. Command+Tab và nhấp phải trực tiếp trên touchpad giữ trạng thái chưa đạt từ vòng trước. [Ảnh nút R](../../artifacts/xfce-effects-20261120/so-sanh-nut-r.jpg) · [Báo cáo input](XIAOMI_INPUT_2026-11-20.md)

**Home → Linux Resume qua widget chưa đạt.** Lượt chạm đúng `linux-resume.sh` từ Android Home khi Picom đã tắt báo `expected one untagged Termux:X11 server on :2; found 0`. `ps` qua ADB vẫn thấy server `:2` trong miền `runas_app`, còn ứng dụng Termux chạy ở `untrusted_app_27`. Đây là khác biệt quan sát được, chưa đủ để kết luận chính xác nguyên nhân kiểm tra PID thất bại. Cùng script chạy qua `adb shell run-as com.termux` đã mở lại đúng viewer PID 25973. [Nút trên Home](../../artifacts/xfce-effects-20261120/05b-linux-resume-widget.png) · [Lỗi widget](../../artifacts/xfce-effects-20261120/05c-widget-error-crop.png) · [Resume qua ADB](../../artifacts/xfce-effects-20261120/resume-adb-direct.txt)

Anh trai thử trên tablet với Picom bật để xác nhận độ mượt khi kéo liên tục, cuộn hai ngón, Alt+Tab hai chiều và kích thước nút cửa sổ. Nền panel 94% có thể nhìn rõ nhất khi đối chiếu cùng vị trí nền sáng và tối.
