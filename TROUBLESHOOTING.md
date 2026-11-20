# Khắc phục sự cố

## Chưa có desktop hoặc nút báo trạng thái không rõ

Kiểm tra Termux và Termux:X11 còn cài, rồi kiểm tra quyền RUN_COMMAND của Linux Desktop trong cài đặt Android. Cho phép quyền này đồng nghĩa app được cấp có thể chạy lệnh với quyền Termux. `allow-external-apps=true` còn là điều kiện bắt buộc; nó áp dụng với mọi app được cấp quyền RUN_COMMAND, không chỉ launcher.

Manager chưa an toàn và chưa được triển khai; Start, Stop và Status đều từ chối hoạt động trong source. Không chạy source manager trên tablet để thử khi ownership chưa được xác minh. Không khẳng định phiên còn sống sau khi Android kết thúc tiến trình. Nếu callback mất, không coi yêu cầu là thành công; kiểm tra trạng thái sau khi mở lại app khi manager đã an toàn. Không xóa container, khóa, PID hoặc tiến trình lạ để xử lý lỗi.

Cgroup hiện có của Termux không chứng minh khả năng cô lập riêng desktop. Không chạy `cgroup.kill` cho toàn UID Termux: thao tác đó có thể dừng cả dịch vụ không liên quan. Không xóa lock/socket `:1` để ép desktop khởi động.

## Phiên thử `:2` chỉ hiện con trỏ

Ảnh chụp tablet xác nhận cửa sổ `xmessage` hiển thị trong Termux:X11 trên `:2`; chưa xác minh cảm ứng. `xfce4-session` và `xfwm4` thử nghiệm đang chờ futex; `xfwm4` chưa công bố window manager, panel và desktop chưa chạy. Bus thử trả lời trong cùng phiên, nhưng truy vấn từ PRoot khác tới cả bus thử và bus cũ trả `NoReply`; nguyên nhân chưa xác định. Không tự xóa socket hoặc giết process theo tên. Xin phép trước khi dừng hoặc thay phiên đang hoạt động.

## XFCE treo, màn hình đen con trỏ X

Nguyên nhân: Mesa GL phần cứng (`libgallium`) treo trên futex khi khởi tạo trong PRoot. Kiểm tra: `timeout 20 glxinfo -B` treo, còn `LIBGL_ALWAYS_SOFTWARE=1 glxinfo -B` chạy. Cách chạy: `scripts/xfce-components.sh :N` trong Debian (`--shared-tmp`), dùng GL phần mềm và không dùng `xfce4-session`. Không chạy hai window manager trên một display; script tự từ chối nếu đã có WM.

## Khôi phục cấu hình Termux

Bản sao trước thay đổi: `/data/data/com.termux/files/home/.termux/termux.properties.linux-desktop.20261118150203.19514.bak`. Trước khi khôi phục, xem cả file hiện tại và backup, đồng thời sao lưu các thay đổi mới nếu muốn giữ. Từ Termux, dùng `cp -p ~/.termux/termux.properties.linux-desktop.20261118150203.19514.bak ~/.termux/termux.properties` rồi `termux-reload-settings`. Lệnh thay toàn bộ file hiện tại bằng bản sao cũ; không chạy nếu muốn giữ thay đổi sau lần sao lưu mà chưa nhập lại chúng.

## Ubuntu và dữ liệu khác

Không dùng `proot-distro remove`, `reset` hoặc `restore` để sửa lỗi: các lệnh này có thể phá dữ liệu. Container `ubuntu` có sẵn không thuộc phạm vi triển khai.
