# Kế hoạch Fedora trên Xiaomi Pad 7 Pro

Mở **Fedora** bằng một lần chạm trên màn hình chính Android. Chạy cục bộ, không cần root. **Linux Resume** tiếp tục mở Debian hiện tại. Bản kế hoạch ngày 26/11/2026. Fedora chưa được cài.

## Phương án

Dùng image Fedora 45 ARM64 từ Fedora Registry, cài XFCE trong container PRoot mới. Termux chạy phía sau. Android trên máy `muyu` đã báo `VMs are not supported` và thiếu `/dev/kvm` khi kiểm tra ngày 20/11. Đóng gói PRoot vào APK riêng vẫn giữ chi phí của PRoot, nên ưu tiên đo độ mượt của desktop trên máy thật. [Fedora XFCE ARM64](https://fedoraproject.org/spins/xfce/download/) · [Android AVF](https://source.android.com/docs/core/virtualization) · [Giới hạn PRoot](https://github.com/termux/proot-distro#proot-limitations)

## Các bước triển khai

1. **Cài Fedora riêng.** Ghi phiên bản và digest của image. Tạo container `fedora45` với thư mục dữ liệu, cấu hình, socket và âm thanh riêng. Dùng `--isolated` và chỉ gắn tài nguyên Fedora cần. Giữ nguyên container Debian, Ubuntu, viewer Termux:X11, cấu hình Android và nút **Linux Resume**.
2. **Mở desktop bằng một chạm.** Dùng TigerVNC trong Fedora và AVNC trên Android. VNC lắng nghe trên loopback và có xác thực, với thông tin kết nối lưu trong AVNC. Nút **Fedora** trên màn hình chính khởi động phiên nếu đã tắt hoặc mở lại phiên hiện có. Kiểm tra thao tác này khi rút cáp USB và khi Debian đang chạy trên `:2`. [TigerVNC](https://tigervnc.org/doc/Xvnc.html) · [AVNC](https://github.com/gujjwal00/avnc) · [Termux:Widget](https://github.com/termux/termux-widget)
3. **Tắt Fedora an toàn.** Nút **Tắt Fedora** yêu cầu ứng dụng đóng và cho phép lưu việc. Nếu ứng dụng đang chờ xác nhận lưu, giữ phiên mở. Khi đóng xong, dừng XFCE, VNC và âm thanh của Fedora. Kiểm tra chạm liên tiếp chỉ mở một phiên, tắt rồi mở lại được, và Debian vẫn chạy.
4. **Kiểm tra công việc hằng ngày.** Dùng `dnf` để cài và gỡ một gói thử. Thử giao dịch tương tự qua dnfdragora, kể cả dịch vụ D-Bus mà nó cần. Chỉ tính chợ ứng dụng đạt khi giao dịch hoàn tất từ giao diện. Mở VS Code Desktop bản RPM ARM64 của Microsoft, sửa và lưu tệp mẫu, chạy Bash tích hợp. Mở từng mục Cài đặt XFCE, quản lý tệp và LibreOffice. Thử âm lượng, cảm ứng, bàn phím và touchpad thật. [dnfdragora](https://packages.fedoraproject.org/pkgs/dnfdragora/dnfdragora/) · [VS Code trên Fedora](https://code.visualstudio.com/docs/setup/linux#_rhel-fedora-and-centos-based-distributions)
5. **Đo trước khi chốt viewer.** Ở `1600×1068`, lấy trung vị ba lần mở từ trạng thái đã tắt và ba lần mở lại. Đo CPU và RAM khi chờ, thử gõ và cuộn trong VS Code, rồi kiểm tra quay lại phiên sau khi tablet ngủ. Nếu VNC giật hoặc nhập liệu trễ rõ, thử viewer Termux:X11 với ID ứng dụng riêng và đo lại. [Termux:X11](https://github.com/termux/termux-x11)

Ngủ và tắt nguồn tablet vẫn dùng nút nguồn của HyperOS. Nút **Tắt Fedora** dừng phiên Fedora. Khi cần quay về desktop đang dùng, mở **Linux Resume** trên Android.
