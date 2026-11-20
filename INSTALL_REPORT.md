# Báo cáo cài đặt

Ngày: 2026-11-18. Workspace: `C:\Users\PC\linux-desktop`.

## Khảo sát

- Tablet ADB `f422eebd`: Android 16/API 36, ABI arm64-v8a; `/data` còn khoảng 101 GiB lúc kiểm tra.
- Termux `0.118.3`, debuggable; `run-as com.termux` hoạt động. `proot-distro 5.4.1`, `termux-x11-nightly 1.03.01-5`, `x11-repo 8.4-1`. APK Termux:X11 `1.03.01-caa7553-13.07.26`.
- Nguồn gốc/chữ ký APK cũ chưa xác minh. Không gỡ, thay hoặc cập nhật APK này.
- Container `ubuntu` đã có; không thay đổi. Trước cài đặt, không có container `debian`.
- `allow-external-apps` trước đó chưa có dòng hiệu lực. Đã sao lưu chính xác vào `/data/data/com.termux/files/home/.termux/termux.properties.linux-desktop.20261118150203.19514.bak` rồi thêm `allow-external-apps=true` tại dòng 192. Thiết lập này cho phép mọi app được cấp quyền RUN_COMMAND chạy lệnh trong Termux, không riêng launcher. Không cấp quyền cho app khác. Khôi phục: từ Termux, sau khi kiểm tra và sao lưu thay đổi mới nếu có, chép file backup này về `~/.termux/termux.properties`; thao tác đó thay toàn bộ cấu hình hiện tại bằng bản sao cũ.
- Docker Registry trả HTTP 401 có Bearer challenge qua HTTPS: truy cập mạng hoạt động.

## Debian

- `proot-distro install -n debian -a aarch64 debian:stable`: thành công; Docker Official Image từ Docker Hub. Sau cài đặt, API Docker Hub công bố manifest ARM64 `sha256:f8e94f418126f96bbe8580c30a47abcea442704b68b30ed8654432ad61bea6c1`. Truy xuất manifest qua HTTPS từ tablet, SHA-256 khớp; layer trong manifest `sha256:14a5a4d8cff3b5f9bdc21a9d0f75142b2a9a21cf46f664f4c5568f346b7fd1f1` khớp SHA-256 của layer lưu trong cache. Chưa xác minh chữ ký image độc lập; tag có thể thay đổi.
- Python Windows khi truy xuất registry báo `CERTIFICATE_VERIFY_FAILED: certificate has expired`; không tắt xác thực TLS. Thay vào đó dùng Python trong Termux với TLS mặc định thành công.
- `uname -m`: `aarch64`. `/etc/os-release`: Debian 13.7 trixie.
- `apt-get update` và `apt-get install --no-install-recommends` hoàn tất thành công. `dpkg-query` xác nhận `xfce4 4.20.1`, `dbus-x11 1.16.2-2`, `xfce4-terminal 1.1.4-1`, `thunar 4.20.2-1+deb13u1`, `git`, `curl`, `wget`, `python3`, `python3-pip`, `nano`, `vim`, `x11-utils` và `x11-xserver-utils`. `dpkg --audit` không có lỗi; `command -v` xác nhận các executable cần thiết.
- Display `:1` có lock/socket từ 24-07 và không được chạm tới; dự kiến dùng `:2` riêng. Chưa xác minh desktop.

## Nguồn chính thức

- https://github.com/termux/proot-distro
- https://github.com/termux/termux-x11
- https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent
- https://hub.docker.com/_/debian

## Việc còn lại

- **BLOCKED:** Bộ quản lý phiên trong `scripts/` chưa an toàn để triển khai. Review phát hiện khoảng gián đoạn giữa tạo process và ghi state có thể để process mồ côi; process PRoot đang chuyển trạng thái khó nhận diện để dọn an toàn; probe X11/XFCE chưa chứng minh thuộc phiên do manager tạo. Start, Stop và Status đều bị vô hiệu hóa và trả lỗi. Chưa copy script sang tablet, chưa cài APK.
- Android project `C:\Users\PC\linux-desktop\android`: Gradle offline build thành công với `ANDROID_HOME` và JDK 21; chạy lại unit test với `--rerun-tasks`: 10 test PASS. Test chưa xác minh Android lifecycle hay tích hợp Termux. Start tự động từ icon đã bị vô hiệu để app khác không thể gọi activity export nhằm kích hoạt Start; yêu cầu một chạm chưa đạt. APK debug: `android\app\build\outputs\apk\debug\app-debug.apk`, package `dev.local.linuxdesktop.launcher`, version 1.0, target 36. Chứng thư debug SHA-256 `a2144c5e6a02981a155f67477b9a611a0baa214a36522b9274fb3ea731afb7d3`; apksigner v1/v2 thành công, có cảnh báo metadata không được v1 bảo vệ. Chưa cài và chưa xác minh tích hợp; không xem APK debug là sản phẩm có thể dùng.
- Cấu hình Termux đã đổi và backup như trên; không tự khôi phục vì người dùng đã chấp thuận bật và có thể cần tiếp tục dự án.
- Đợt tiếp tục: kiểm tra lại `proot 5.1.107.86`, `proot-distro 5.4.1`, Termux Python 3.14.6, `xfce4-session 4.20.2-2`, `xfwm4 4.20.0-1`, SELinux Enforcing. Chưa triển khai manager hay cài launcher.
- Audit 524 package user 0: `dumpsys package` không hiển thị app nào yêu cầu hoặc được cấp RUN_COMMAND; Termux khai báo permission. Giới hạn theo dữ liệu ADB hiển thị; không cấp hoặc thu hồi quyền.
- Chi tiết lỗi và tác động side effect của `proot-distro ps`: `LIFECYCLE_AUDIT.md`.
- Kiểm tra read-only cgroup qua `run-as com.termux`: `/sys/fs/cgroup/apps/uid_10528`, `cgroup.kill`, và thư mục process thuộc `system:system`; thư mục UID và các cgroup root được kiểm tra không writable. Process Termux nằm trong `/apps/uid_10528/pid_2226`. Shell kiểm tra có context `runas_app`, không phải context của process Termux. Các thử nghiệm `unshare --user` và `unshare --pid` trong child tạm thời thất bại lần lượt với `Invalid argument` và `Operation not permitted`. Không tạo hoặc sửa cgroup; không dùng `cgroup.kill` cho toàn UID vì sẽ ảnh hưởng dịch vụ Termux khác. Chi tiết: `LIFECYCLE_AUDIT.md`.
- Kiểm thử X11 `:2`: socket filesystem trả peer PID 15917 của server thử nghiệm; ảnh chụp tablet xác nhận cửa sổ `xmessage` trên viewer. Cảm ứng chưa xác minh. Phiên thử `xfwm4` chưa công bố window manager sau 20 giây, process còn chờ futex; panel và desktop chưa chạy. Bus thử trả lời trong cùng phiên, nhưng truy vấn từ PRoot khác tới bus thử và bus cũ trả `NoReply`; nguyên nhân chưa xác định. Không reinstall hoặc dừng phiên cũ. Chi tiết: `TEST_REPORT.md`.
- 2026-11-18 17:05: cài thêm trong Debian `openbox 3.6.1-12+b2`, `xterm 398`, `mesa-utils 9.0.0-2+b2` (40 gói, `--no-install-recommends`, apt rc 0). Openbox thành `x-window-manager` mặc định qua update-alternatives. Không gỡ gì.
- XFCE chạy được trên `:2` khi ép GL phần mềm và bỏ `xfce4-session`; nguyên nhân và bằng chứng: `TEST_REPORT.md`. Server thử `:3` PID 841 đang chạy.
- Các mục chưa kiểm tra không được coi là PASS.
