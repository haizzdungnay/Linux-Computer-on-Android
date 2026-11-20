# Bàn phím và touchpad Xiaomi trong Debian XFCE

Ngày 20/11/2026, trên Xiaomi Pad 7 Pro `24091RPADG` (`muyu`, ADB `f422eebd`). Android 16/API 36, HyperOS `OS3.0.303.0.WOYMIXM`, build `BP2A.250605.031.A3`.

## Thiết bị và cấu hình đo được

| Cổng vào Android | ID Android | VID:PID | Nguồn | Node |
|---|---:|---|---|---|
| Xiaomi Keyboard | 8 | `15d9:00a3` | KEYBOARD, alphabetic | event6 |
| Xiaomi Mouse | 9 | `15d9:00a2` | MOUSE_RELATIVE. Event Hub báo disabled khi đo. | event7 |
| Xiaomi Touch | 10 | `15d9:00a1` | MOUSE, TOUCHPAD | event8 |
| Xiaomi Consumer | 11 | `15d9:00a4` | KEYBOARD, DPAD, JOYSTICK | event9 |

Cụm Xiaomi hiện qua bus `0x0006` (HID ảo nội bộ), `IsExternal: false`, không có địa chỉ Bluetooth ở bốn thiết bị trên. Touch dùng `hid-multitouch` và keyboard dùng `hid-generic`. Tên phần cứng, touchpad cơ học và kiểu kết nối phù hợp dòng Xiaomi Pad 7 / 7 Pro Focus Keyboard dùng tiếp điểm từ tính. Cần nhãn ở mặt dưới hoặc trên hộp để xác nhận mã SKU cụ thể. [Thông số Xiaomi](https://www.mi.com/global/product/xiaomi-pad-7-7-pro-focus-keyboard/specs) · [Kết nối và cử chỉ](https://www.mi.com/global/product/xiaomi-pad-7-7-pro-focus-keyboard/)

Màn **Bàn phím vật lý** hiển thị **Tiếng Anh (Mỹ) - Bàn phím Android**, IME **Gboard**. Android dùng `Generic.kl`/`Generic.kcm` cho keyboard, lưu `english_us` cho subtype hiện tại theo VID/PID. Tap-to-click bật, tốc độ touchpad 3, cuộn tự nhiên được mapper báo bật, vùng nhấp phải được cấu hình bật. Không suy từ các cờ này rằng cử chỉ đang tạo nhấp phải. Xiaomi ghi nhận vuốt hai ngón từ mép touchpad là cử chỉ Back. Các bài thử diễn ra ở giữa touchpad trừ click góc phải. [Trạng thái input](../../artifacts/input-20261120/device-input.txt)

Termux `0.118.3` UID `10528`. Viewer `com.termux.x11` UID `10529`, APK `1.03.01-caa7553-13.07.26` (versionCode 15), companion `termux-x11-nightly 1.03.01-5`. KeyInterceptor được khai báo với `BIND_ACCESSIBILITY_SERVICE`, khả năng lọc phím và `canRetrieveWindowContent=false`. Trước thử, danh sách dịch vụ Trợ năng đã bật rỗng. Sau khi anh bật thủ công, Android xác nhận service được bind. Quyền `WRITE_SECURE_SETTINGS` chỉ được khai báo, không thấy bản cấp quyền. [Manifest](https://github.com/termux/termux-x11/blob/caa7553b36c5567e19896ab6521a2cdcb8010014/app/src/main/AndroidManifest.xml) · [Service](https://github.com/termux/termux-x11/blob/caa7553b36c5567e19896ab6521a2cdcb8010014/app/src/main/java/com/termux/x11/utils/KeyInterceptor.java)

Debian ARM64/PRoot, display `:2`, HOME `/root`, profile `/root/.ld-test/xfce-config`, software GL, compositor tắt. `_NET_SUPPORTING_WM_CHECK` xác nhận Xfwm4 PID 5146; xfsettingsd 5115, xfdesktop 5324 và panel 1293 ở cùng profile, UID 10528 và tracer 5096. Truy vấn Xfconf dùng D-Bus của phiên này. XKB `evdev/pc105/us`; Alt_L thuộc Mod1, Super_L thuộc Mod4; map chuột 1–10 giữ nguyên. XI 2.4 thấy thiết bị ảo Lorie mouse (6) và Lorie keyboard (8). [Export Xfconf và X11](../../artifacts/input-20261120/xfce-x11-before.txt)

## Chẩn đoán

### Bàn phím

| Thao tác vật lý | Sự kiện quan sát được và hành vi | Tầng và hướng xử lý |
|---|---|---|
| Nhấn/thả Ctrl, Shift, Alt riêng | Kernel và XI đều thấy down/up. XI dùng Control_L 37, Shift_L 50, Alt_L 64. | Đường bàn phím cơ bản hoạt động. |
| Giữ/phát Command | Kernel phát KEY_LEFTMETA. Trước KeyInterceptor, HyperOS mở `MiuiKeyboardShortcuts` khi giữ. Sau khi bật, XI thấy Super_L 133 down/up và bộ modifier trở về rỗng. | Phím in Command là Meta trái của Android và Super trái của XKB trên máy này. |
| Alt+Tab, Alt+Shift+Tab trước sửa | Kernel có Tab down/up, XI thiếu Tab trong các lượt đổi app. Android đổi sang Launcher/ứng dụng khác, giữ PID viewer 25973. | Policy Android nhận tổ hợp trước viewer. XFCE đã có forward/reverse binding; thử KeyInterceptor của bản cài. |
| Alt+Tab, Alt+Shift+Tab sau bật KeyInterceptor | Tab 23, Alt 64, Shift 50 vào Lorie. Có 24 lần nhấn Tab với Alt trong đoạn thử hai chiều, ba XID khác nhau được đưa lên focus. Android giữ Termux:X11 trong đoạn này. | PASS chuyển cửa sổ XFCE hai chiều. Khi giữ Alt để chọn, thả Alt để xác nhận. |
| Command+Tab, Command+Shift+Tab với shortcut HyperOS bật | Kernel có Meta và Tab; XI thấy Super 133 nhưng chuỗi Tab bị cắt. Log Android báo Launcher/Gần đây và overlay; viewer cùng PID. | `dumpsys window policy` xác nhận Meta + Android keycode 61 (`KEYCODE_TAB`) thực thi `launch_recents`. Alt+Tab là phương án XFCE đã thử. |
| Esc | XI thấy Escape 9 down/up và viewer vẫn focus trong các lần thử riêng. | Source gọi bỏ pointer capture khi thả Esc đơn. Với `pauseKeyInterceptingWithEsc=false`, Esc được gửi vào X11 và không tắt KeyInterceptor. Home là đường ra Android. |

HyperOS liệt kê **Alt Tab → Chuyển đổi Gần đây** và **Meta Tab → Mở Gần đây**. Công tắc nằm ở màn **Lối tắt bàn phím**, nhóm **Lối tắt hệ thống** (activity `com.miui.miinput.action.MIUI_KEYBOARD_SHORTCUT`). Khi riêng **Mở Gần đây** tắt thử, có lượt Command+Tab vào XI đủ cả hai phím. Giữ Command vẫn gọi overlay `MiuiKeyboardShortcuts` và làm viewer mất focus. Kết quả cuối policy xác nhận **Mở Gần đây** bật lại. [Policy ban đầu](../../artifacts/input-20261120/hyperos-tab-policy.txt) · [Tắt thử](../../artifacts/input-20261120/hyperos-meta-tab-off-trial.txt) · [Policy cuối](../../artifacts/input-20261120/hyperos-tab-policy-final.txt)

XFWM4 4.20.0 đặt `<Super>Tab` thành `switch_window_key`, chuyển giữa cửa sổ cùng ứng dụng. Không có binding mặc định cho `<Super><Shift>Tab`. Xfwm4 chọn một binding cho mỗi action cycle đang dùng cho Alt. Trong export không có shortcut Super đơn mở menu phía XFCE. Kết luận cho Command+Tab hai chiều là **CHƯA ĐẠT**. [Xfwm4 cycle](https://github.com/xfce-mirror/xfwm4/blob/xfwm4-4.20.0/src/cycle.c) · [Xfwm4 bindings](https://github.com/xfce-mirror/xfwm4/blob/xfwm4-4.20.0/src/settings.c)

### Touchpad

| Thao tác vật lý | Sự kiện và hành vi | Tầng và hướng xử lý |
|---|---|---|
| Click trái, giữ kéo | `Xiaomi Touch` phát BTN_MOUSE, XI phát Button1. Có RawMotion trong lúc giữ Button1 khi capture bật. Anh xác nhận kéo cửa sổ và bôi đen chữ dùng được với cấu hình cuối. | PASS theo đo click và xác nhận thao tác ứng dụng. |
| Cuộn hai ngón | Lượt capture bật không thấy nút cuộn. Lượt tắt capture thấy 12 lần X11 Button5 press, và anh xác nhận cuộn được. | PASS cuộn dọc với `pointerCapture=false`. Android thực hiện xử lý touchpad ở chế độ không capture. |
| Chạm hai ngón / click cơ học hai ngón / bấm góc dưới phải | Thiết bị nhận nhiều ngón, có `BTN_TOOL_DOUBLETAP` và `BTN_TOOL_TRIPLETAP` trong lượt đo. Click cơ học tạo BTN_MOUSE. Các mẫu nút trên Android cho `0x1` (primary); không bắt được `0x2` (secondary), KEY_BACK hay XI Button3 trong lượt thử này. | **CHƯA ĐẠT**. Bằng chứng chỉ ra đường nhận dạng cử chỉ/nút bên Android. Tần suất poll có thể bỏ lỡ xung ngắn, chưa xác định vì sao từng cử chỉ không sinh secondary. |
| Nhấp phải bằng chuột Bluetooth | Anh xác nhận làm được. | PASS theo xác nhận người dùng, đối chứng cho đường chuột phải của ứng dụng. |
| Di chuyển bằng touchpad rồi chạm **R** trên màn hình | `xev` thấy đủ Button3 press/release qua Lorie. Thunar và Mousepad hiện cửa sổ GTK popup menu trong kiểm tra có chạm ADB. Anh xác nhận nút **R** mở đúng vị trí con trỏ và muốn giữ. | PASS phương án dự phòng. Nút **R** nằm trong cụm L/M/R của Termux:X11. |

`touchMode=Trackpad` chọn chế độ mô phỏng cho màn cảm ứng. Đường touchpad Xiaomi được đo trên event8, rồi Lorie mouse ID 6 phía XI. Bản này nhận `BUTTON_SECONDARY` hoặc chuyển `KEYCODE_BACK` về nút phải nếu sự kiện đến từ SOURCE_MOUSE/SOURCE_MOUSE_RELATIVE. Back chung vẫn đặt **toggle soft keyboard**. [TouchInputHandler](https://github.com/termux/termux-x11/blob/caa7553b36c5567e19896ab6521a2cdcb8010014/app/src/main/java/com/termux/x11/input/TouchInputHandler.java)

## Cấu hình áp dụng và hoàn tác

| Thay đổi | Giá trị trước | Giá trị áp dụng | Hoàn tác |
|---|---|---|---|
| Dịch vụ Trợ năng `Termux:X11 KeyInterceptor` | Tắt | Bật thủ công trong Android | **Khả năng truy cập → Chung → Quyền → Ứng dụng đã tải xuống → Termux:X11 KeyInterceptor → Tắt**. Chỉ tắt mục này. |
| Viewer `pointerCapture` | `true` | `false` | Bật **Capture external pointer devices when possible** trong Termux:X11 hoặc chạy dòng đầu bên dưới. |
| Viewer `showMouseHelper` | `false` | `true`, theo xác nhận của anh | Tắt **Show mouse click helper overlay** trong Termux:X11 hoặc chạy dòng thứ hai bên dưới. |

Trong PowerShell, đưa viewer lên trước rồi chạy:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" -s f422eebd shell 'run-as com.termux env PATH=/data/data/com.termux/files/usr/bin:/system/bin timeout 7 termux-x11-preference pointerCapture:true'
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" -s f422eebd shell 'run-as com.termux env PATH=/data/data/com.termux/files/usr/bin:/system/bin timeout 7 termux-x11-preference showMouseHelper:false'
```

Viewer đang dùng `preferScancodes=true`, `hardwareKbdScancodesWorkaround=true`, `filterOutWinkey=false`, `dexMetaKeyCapture=false`, `enableAccessibilityServiceAutomatically=false`, `pauseKeyInterceptingWithEsc=false`. Chế độ pause theo Esc có sẵn, và khi bật thì phím Esc đơn chuyển trạng thái bắt phím cho tới khi rearm. Giữ pause tắt để Esc đóng menu mà vẫn bắt Alt+Tab. Khi Home chuyển focus, service thôi chuyển phím mới vào X11 và có thể chuyển nốt key-up của phím đã giữ. Mở lại bằng **Linux Resume**. [Cấu hình ban đầu](../../artifacts/input-20261120/termux-x11-before.txt) · [Cấu hình tắt pointer capture](../../artifacts/input-20261120/termux-x11-pointer-off.txt) · [Xử lý Esc](https://github.com/termux/termux-x11/blob/caa7553b36c5567e19896ab6521a2cdcb8010014/app/src/main/java/com/termux/x11/input/InputEventSender.java)

So sánh CLI trước/sau chỉ có hai preference khác giá trị. Export live Xfconf, XKB, map pointer, thiết bị XI và PID của phiên XFCE khớp từng byte. [Viewer cuối](../../artifacts/input-20261120/termux-x11-final.txt) · [XFCE cuối](../../artifacts/input-20261120/xfce-x11-final.txt)

## Phím tắt và nghiệm thu

| Thao tác | Kết quả |
|---|---|
| Alt+Tab / Alt+Shift+Tab | **PASS phần cứng**. Chuyển qua ba XID XFCE, 24 lần nhấn Tab với Alt, không đổi app Android trong đoạn kiểm tra tương ứng. XQueryKeymap cho thấy modifier được nhả sau mỗi chuỗi theo dõi. |
| Command+Tab / Command+Shift+Tab | **CHƯA ĐẠT**. Thử bật và tắt riêng policy Meta+Tab. Bản Android có overlay khi giữ Meta. Dùng Alt+Tab cho công việc trong XFCE. |
| Click trái, cuộn hai ngón, kéo cửa sổ, chọn chữ | **PASS** với cấu hình cuối. Cuộn dọc và click có sự kiện XI, thao tác kéo và chọn chữ do anh xác nhận. |
| Nhấp phải và mở menu | **CHƯA ĐẠT** với cử chỉ trên touchpad Xiaomi. Nút **R** mở đúng tại con trỏ theo anh xác nhận. Đã đo menu trong Thunar và Mousepad bằng chạm nút R tự động. Anh xác nhận chuột Bluetooth cũng nhấp phải được. |
| Esc và Home → Linux Resume | Escape 9 đi đủ down/up, có mẫu Android vẫn giữ viewer. Anh xác nhận chủ động về Home rồi Resume được. Các lượt qua ứng dụng Android khác và quay lại đều giữ PID viewer; ô nhập văn bản ngoài Linux chưa thử riêng. |
| Ctrl+C ngắt tiến trình trong terminal | **PASS theo xác nhận của anh** với lệnh mẫu `sleep`. Lượt bổ sung không có sự kiện tương ứng trong cửa sổ thu, nên không tính là PASS từ trace. |
| Menu, Shift+F10, Fn | Nút **Menu** tạo popup Mousepad trong kiểm tra phần mềm. Lượt `Shift+F10` phần mềm không mở menu Mousepad và không ghi được F10/Menu vật lý. Hành vi Fn/F1–F12 còn **CHƯA KIỂM CHỨNG**. |
| Ctrl+C/V/X/A/Z/S/F trong editor, Ctrl+Tab / Ctrl+Shift+Tab, Ctrl+Shift+C/V trong terminal, Alt+F4, tháo/gắn lại | **CHƯA KIỂM CHỨNG** riêng từng tổ hợp. Alt+F4 chỉ nên thử ở cửa sổ mẫu không có nội dung chưa lưu. |

## Bằng chứng

- Lượt ban đầu: [kernel](../../artifacts/input-20261120/baseline-android.txt), [focus Android](../../artifacts/input-20261120/baseline-focus.txt), [XInput](../../artifacts/input-20261120/baseline-x11.txt). Timestamp uptime XInput bị hằng do PRoot. Bộ đọc focus ban đầu cũng lỗi regex và được khởi động riêng giữa lượt. Các lần chuyển app được đối chiếu nhờ timestamp kernel và log activity. Lượt sau dùng CLOCK_MONOTONIC cho XI và đã đồng bộ thời gian Android.
- Lượt bật KeyInterceptor: [kernel và focus](../../artifacts/input-20261120/keyinterceptor-android.txt), [XInput và XQueryKeymap](../../artifacts/input-20261120/keyinterceptor-x11.txt).
- Lượt tắt pointer capture: [kernel và focus](../../artifacts/input-20261120/pointer-off-android.txt), [XInput và XQueryKeymap](../../artifacts/input-20261120/pointer-off-x11.txt).
- Lượt đo bổ sung: [kernel và trạng thái nút Android](../../artifacts/input-20261120/targeted-android.txt), [XInput và focus](../../artifacts/input-20261120/targeted-x11.txt). Bộ đếm slot thô có lệch một sau một số lần nhả hết ngón; kết luận đa chạm dựa trên các cờ kernel BTN_TOOL_DOUBLETAP/BTN_TOOL_TRIPLETAP.
- Đối chứng phần mềm: [Button3 vào xev](../../artifacts/input-20261120/x11-button3-synthetic.txt), [nút R vào xev và menu ứng dụng](../../artifacts/input-20261120/mouse-helper-synthetic.txt), [phím Menu trong Mousepad](../../artifacts/input-20261120/mousepad-menu-synthetic.txt).
- Lượt nghiệm thu cuối: [kernel và focus](../../artifacts/input-20261120/acceptance-android.txt), [XInput](../../artifacts/input-20261120/acceptance-x11.txt). Bộ đo tự dừng, không ghi được chuỗi Ctrl hoặc Home/Resume của lượt này. Kết quả kéo, bôi đen, Ctrl+C trong terminal và Home/Resume do anh xác nhận sau thử.

ADB shell đọc được getevent trên bốn node đã chọn, không cần root. `xinput` 1.6.4 lấy từ gói Debian đã xác thực qua APT, giải nén tạm, không cài vào Debian. Các lượt tương tác có thời hạn. Không lưu nội dung gõ, clipboard hay ảnh màn hình. ADB input điều hướng màn Cài đặt và chạm nút R trong bài kiểm tra phần mềm. Các kết luận phần cứng dựa vào lượt người dùng thao tác hoặc xác nhận.
