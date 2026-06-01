# Hoạt động CLB

Hoạt động CLB là buổi tập, giao lưu hoặc thi đấu nội bộ do một CLB tạo. Trang chính: `/events`; sự kiện đã tham gia: `/events/my-joined-events`; hoạt động của CLB mình quản lý: `/events/my-clubs`.

## Xem và tìm hoạt động

Người dùng có thể lọc theo tên, tỉnh/thành, phường/xã, thời gian nhanh, miễn phí/có phí, khoảng phí, khoảng ngày, trình độ, thể loại đánh và sân.

Thông tin quan trọng: tên, CLB tổ chức, địa điểm/sân, thời gian bắt đầu-kết thúc, hạn đăng ký, phí, số người đã tham gia, số người tối đa, trình độ min-max, thể loại: đơn nam, đơn nữ, đôi nam, đôi nữ, đôi nam nữ.

## Tham gia hoạt động

Điều kiện thường gặp: đã đăng nhập, hoạt động còn mở, chưa hết hạn đăng ký, chưa vượt số lượng, không trùng lịch cá nhân, đạt khoảng trình độ, và nếu không phải thành viên CLB thì hoạt động phải cho người ngoài tham gia.

Luồng hướng dẫn ngắn: vào `/events` -> mở chi tiết `/events/{slug}` -> bấm tham gia. Nếu hệ thống báo trùng lịch, gợi ý người dùng xem lịch ở hồ sơ hoặc chọn hoạt động khác.

Trạng thái người tham gia: `PENDING` chờ duyệt, `APPROVED` đã được duyệt, `ATTENDED` đã điểm danh, `ABSENT` vắng, `CANCELLED` đã hủy.

## Hủy tham gia và đánh giá

Người dùng có thể hủy tham gia từ chi tiết hoạt động hoặc danh sách đã tham gia; hệ thống có thể yêu cầu lý do hủy. Sau khi hoạt động kết thúc, người tham gia có thể đánh giá hoạt động/CLB nếu giao diện hiển thị nút đánh giá.

## Chủ CLB quản lý hoạt động

Chủ CLB tạo hoạt động tại `/my-clubs/create-event` hoặc trong trang CLB của mình. Thông tin cần có: CLB, tiêu đề, mô tả, yêu cầu, ảnh, địa điểm/sân, thời gian, hạn đăng ký, số người, phí, cho phép người ngoài, giới hạn thành viên CLB/người ngoài, trình độ và thể loại.

Chủ CLB có thể sửa, hủy hoạt động, xem danh sách người tham gia, duyệt/từ chối đăng ký, cập nhật trạng thái tham gia và điểm danh.
