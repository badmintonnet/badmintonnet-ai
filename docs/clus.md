# CLB cầu lông

CLB là nhóm người chơi trên BadmintonNet để sinh hoạt, tổ chức hoạt động và đăng ký giải theo CLB. Trang chính: `/clubs`; CLB của tôi: `/my-clubs`; tạo CLB: `/clubs/create`.

## Tìm và xem CLB

Người dùng có thể tìm CLB theo tên, tỉnh/thành, phường/xã, sân, khoảng trình độ, uy tín và trạng thái đã tham gia. Link chi tiết có dạng `/clubs/{slug}`.

Thông tin nên nhắc: tên CLB, chủ CLB, địa điểm/sân, số thành viên, giới hạn thành viên, trình độ min-max, public/private, tag, uy tín và số hoạt động.

## Tạo CLB

Luồng ngắn: đăng nhập -> vào `/clubs/create` -> nhập tên, mô tả, logo, địa điểm/sân, số thành viên tối đa, trình độ min-max, chế độ hiển thị và tag -> gửi tạo CLB.

Sau khi tạo, người tạo là chủ CLB. CLB có trạng thái `PENDING`, `ACTIVE` hoặc `INACTIVE`; nếu chưa active thì hướng dẫn người dùng chờ duyệt hoặc liên hệ quản trị viên.

## Tham gia CLB

Luồng ngắn: vào `/clubs` -> mở chi tiết `/clubs/{slug}` -> bấm tham gia -> nhập lời nhắn nếu có -> chờ chủ CLB duyệt.

Trạng thái thành viên: `PENDING` chờ duyệt, `APPROVED` là thành viên, `REJECTED` bị từ chối, `BANNED` bị cấm. Nếu đã tham gia, gợi ý người dùng vào `/my-clubs`.

## Quản lý CLB của tôi

Trang `/my-clubs/{slug}` dành cho chủ CLB và thành viên. Chủ CLB có thể sửa thông tin CLB, xem thành viên/khách, duyệt hoặc từ chối yêu cầu, xác minh trình độ thành viên, tạo cảnh báo, thu hồi cảnh báo, mời người chơi, xem lịch thành viên và quản lý hoạt động.

Thành viên có thể xem thông tin CLB, hoạt động, thành viên, cảnh báo của mình và rời CLB nếu cần.

## Giải theo CLB

Trong CLB của tôi, chủ CLB có thể đăng ký CLB tham gia giải loại `CLUB`, chọn roster thành viên, cập nhật roster trước hạn, chọn đại diện/lineup nếu giải yêu cầu, theo dõi trạng thái đăng ký và hủy đăng ký khi còn được phép.
