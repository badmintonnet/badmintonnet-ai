# Giải đấu

Giải đấu nằm ở `/tournaments`, chi tiết `/tournaments/{slug}`. Có 2 loại: `INDIVIDUAL` cá nhân/cặp đôi và `CLUB` đăng ký theo CLB.

## Xem giải đấu

Thông tin cần ưu tiên: tên, loại tham gia, trạng thái, địa điểm/sân, thời gian thi đấu, thời gian mở-đóng đăng ký, lệ phí, hạng mục, trình độ min-max, số người/CLB đã đăng ký, luật, giải thưởng và kết quả nếu có.

Trạng thái giải: `UPCOMING` sắp diễn ra, `REGISTRATION_OPEN` đang mở đăng ký, `REGISTRATION_CLOSED` đã đóng đăng ký, `IN_PROGRESS` đang diễn ra, `COMPLETED` hoàn thành, `CANCELLED` đã hủy.

## Đăng ký giải cá nhân

Luồng ngắn: vào `/tournaments` -> mở giải -> chọn hạng mục -> xem chi tiết `/tournaments/{slug}/categories/{categoryId}` -> bấm đăng ký.

Với hạng mục đơn, người dùng đăng ký trực tiếp. Với hạng mục đôi, người dùng cần chọn/mời bạn đánh đôi; bạn đánh đôi có thể chấp nhận hoặc từ chối lời mời. Một số hạng mục có lệ phí và cần thanh toán trước khi được duyệt.

Trạng thái đăng ký cá nhân/cặp: `DRAFT`, `PENDING`, `PAYMENT_REQUIRED`, `APPROVED`, `REJECTED`, `CANCELLED`, `ELIMINATED`.

## Đăng ký giải theo CLB

Chỉ chủ CLB hoặc người có quyền quản lý CLB nên đăng ký. Luồng ngắn: mở giải loại `CLUB` -> chọn CLB -> chọn danh sách thành viên roster theo giới hạn min-max -> gửi đăng ký -> thanh toán nếu có -> chờ duyệt.

Sau khi đăng ký, chủ CLB có thể cập nhật roster, hủy đăng ký, xem chi tiết đăng ký, đặt đại diện, xếp lineup và theo dõi bảng đấu/kết quả.

Trạng thái đăng ký CLB: `DRAFT`, `PENDING`, `PAYMENT_REQUIRED`, `PAID`, `APPROVED`, `REJECTED`, `CANCELLED`, `ELIMINATED`.

## Kết quả và bảng đấu

Khi giải đã tạo bảng hoặc có kết quả, người dùng có thể xem bracket, kết quả theo hạng mục, thứ hạng/podium, thống kê và lịch sử thi đấu trong chi tiết giải hoặc hồ sơ người chơi.
