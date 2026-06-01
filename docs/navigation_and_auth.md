# Điều hướng và tài khoản

BadmintonNet có các trang người dùng chính: trang chủ `/`, CLB `/clubs`, CLB của tôi `/my-clubs`, hoạt động `/events`, hoạt động đã tham gia `/events/my-joined-events`, giải đấu `/tournaments`, bảng xếp hạng `/rankings`, hồ sơ `/profile`, chat `/chat`, chatbot `/chatbot`.

## Đăng nhập và đăng ký

Người dùng đăng nhập ở `/login`, đăng ký ở `/signup`, xác minh tài khoản ở `/verify`. Các thao tác như tham gia CLB, tham gia hoạt động, đăng ký giải, xem lịch cá nhân, chat và cập nhật hồ sơ cần đăng nhập.

Nếu người dùng hỏi cách bắt đầu: hướng dẫn đăng ký/đăng nhập, cập nhật hồ sơ và trình độ, sau đó tìm CLB hoặc hoạt động phù hợp.

## Link trong câu trả lời AI

Khi có slug, luôn dùng link tương đối:

- CLB: `[Tên CLB](/clubs/{slug})`
- Hoạt động: `[Tên hoạt động](/events/{slug})`
- Giải đấu: `[Tên giải](/tournaments/{slug})`
- Hồ sơ người chơi: `[Tên người chơi](/profile/{slug})`

Không tự bịa dữ liệu. Nếu cần dữ liệu hiện tại về CLB, hoạt động, giải đấu hoặc gợi ý cá nhân hóa, ưu tiên tool/API realtime.
