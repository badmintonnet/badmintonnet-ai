# Cách Tính Điểm Phù Hợp Và Xếp Hạng Người Chơi

Tài liệu này mô tả cách BadmintonNet tính điểm gợi ý và xếp hạng người chơi theo logic hiện tại trong backend. Khi người dùng hỏi các câu như "điểm phù hợp tính thế nào", "vì sao CLB này được gợi ý", "score 82/100 nghĩa là gì", "xếp hạng người chơi tính ra sao", hãy ưu tiên dùng nội dung này.

## Điểm Phù Hợp Là Gì

Điểm phù hợp là điểm cá nhân hóa trên thang 0-100. Điểm càng cao nghĩa là CLB, hoạt động hoặc giải đấu càng phù hợp với hồ sơ hiện tại của người dùng.

Điểm này không phải là đánh giá chất lượng tuyệt đối. Nó phản ánh mức độ phù hợp dựa trên vị trí, trình độ, lịch, lịch sử tham gia, CLB đã tham gia và dữ liệu hiện có của hệ thống.

Điểm cuối cùng được làm tròn 1 chữ số và giới hạn trong khoảng 0-100.

## Dữ Liệu Được Dùng Để Gợi Ý

Hệ thống có thể dùng các dữ liệu sau:

- Trình độ người chơi, lấy từ `overallScore` của hồ sơ rating. Nếu chưa có rating, hệ thống dùng mặc định 2.5.
- Vị trí người dùng, nếu hồ sơ có kinh độ và vĩ độ.
- Lịch cá nhân đang hoạt động của người dùng.
- CLB người dùng đã tham gia.
- Tag/phong cách của các CLB người dùng từng tham gia.
- Lịch sử tham gia hoạt động CLB.
- Lịch sử tham gia giải đấu.
- Trạng thái, vị trí, trình độ yêu cầu, hạng mục, slot còn lại và thời gian của CLB/hoạt động/giải đấu.

## Điểm Phù Hợp CLB

Điểm CLB bắt đầu từ 18 điểm nền.

Sau đó cộng thêm:

- Phù hợp trình độ:
  - Nếu trình độ người dùng nằm trong khoảng `minLevel` và `maxLevel` của CLB: +22.
  - Nếu lệch nhẹ không quá 0.5 điểm so với khoảng trình độ của CLB: +12.
  - Nếu lệch nhiều: +2.
- Khoảng cách:
  - Không quá 3 km: +32.
  - Không quá 7 km: +28.
  - Không quá 15 km: +20.
  - Không quá 30 km: +12.
  - Không quá 60 km: +2.
  - Không quá 100 km: -8.
  - Không quá 300 km: -18.
  - Xa hơn 300 km: -35.
  - Nếu thiếu dữ liệu vị trí: +6.
- Tag/phong cách CLB:
  - Nếu CLB có tag giống các CLB người dùng từng tham gia hoặc quan tâm: +12.
- Uy tín CLB:
  - Nếu reputation của CLB từ 70 trở lên: +10.
- Số lượng thành viên:
  - Nếu CLB không giới hạn số thành viên: +4.

Hệ thống không gợi ý lại các CLB mà người dùng đã là thành viên.

## Điểm Phù Hợp Hoạt Động CLB

Điểm hoạt động bắt đầu từ 16 điểm nền.

Sau đó cộng thêm:

- Phù hợp trình độ: tối đa +22.
- Khoảng cách: tối đa +32, và có thể bị trừ điểm nếu quá xa.
- Trùng ngày người dùng thường tham gia: +6.
- Trùng khung giờ quen thuộc với lịch của người dùng: +6.
- Người dùng đang là thành viên CLB tổ chức hoạt động: +14.
- Hạng mục hoạt động trùng với lịch sử tham gia của người dùng: +10.
- Hoạt động vẫn còn chỗ đăng ký: +6.

Hệ thống loại bỏ các hoạt động mà người dùng đã đăng ký và các hoạt động bị trùng lịch cá nhân.

## Điểm Phù Hợp Giải Đấu

Điểm giải đấu bắt đầu từ 14 điểm nền.

Sau đó cộng thêm:

- Khoảng cách: tối đa +32, và có thể bị trừ điểm nếu quá xa.
- Phù hợp trình độ theo hạng mục giải đấu: tối đa +22.
- Có hạng mục giống lịch sử thi đấu của người dùng: +12.
- Trùng ngày hoặc khung giờ quen thuộc: tối đa +6.
- Giải đang mở đăng ký: +12.
- Nếu chưa mở nhưng vẫn còn hạn đăng ký: +8.

Hệ thống không gợi ý các giải đấu mà người dùng đã tham gia.

## Cách Xếp Hạng Người Chơi

BadmintonNet xếp hạng người chơi dựa trên hồ sơ `PlayerRating`. Người dùng tự khai báo hoặc cập nhật các chỉ số sau:

- Kinh nghiệm: `experience`.
- Kỹ thuật giao cầu: `serve`.
- Đập cầu: `smash`.
- Phông cầu: `clear`.
- Bỏ nhỏ: `dropShot`.
- Tạt cầu/drive: `drive`.
- Cầu lưới: `netShot`.
- Đánh đôi: `doubles`.
- Phòng thủ: `defense`.
- Di chuyển chân: `footwork`.
- Thể lực: `stamina`.
- Chiến thuật: `tactics`.

## Điểm Kỹ Thuật Trung Bình

Điểm kỹ thuật trung bình là trung bình cộng của 9 kỹ năng kỹ thuật:

```text
averageTechnicalScore =
  (serve + smash + clear + dropShot + drive + netShot + doubles + defense + footwork) / 9
```

## Điểm Tổng Thể Người Chơi

Điểm tổng thể là tổng có trọng số:

```text
overallScore =
  0.3 * experience
  + 0.4 * averageTechnicalScore
  + 0.2 * stamina
  + 0.1 * tactics
```

Trong đó:

- Kinh nghiệm chiếm 30%.
- Kỹ thuật trung bình chiếm 40%.
- Thể lực chiếm 20%.
- Chiến thuật chiếm 10%.

## Quy Đổi Điểm Thành Trình Độ

Hệ thống đổi `overallScore` thành `skillLevel` như sau:

- `overallScore <= 1`: Mới tập chơi.
- `overallScore <= 2`: Cơ bản.
- `overallScore <= 3`: Trung bình.
- `overallScore <= 4`: Trung bình khá.
- `overallScore <= 4.5`: Khá.
- `overallScore > 4.5`: Bán chuyên.

## Verify Count

`verifyCount` là số lần người chơi được xác nhận rating trong các CLB. Chỉ số này giúp tăng độ tin cậy của hồ sơ, nhưng công thức `overallScore` hiện tại vẫn được tính theo các trường rating ở trên.

## Cách Trả Lời Khi Người Dùng Hỏi

Khi người dùng hỏi về điểm phù hợp hoặc xếp hạng, hãy trả lời theo dữ liệu trên. Không tự bịa thêm các yếu tố chưa có trong code như đèn sân, loại sân, số lượng sân, phí thành viên CLB, trọng số bí mật, hoặc "cài đặt đề xuất" nếu không có dữ liệu rõ ràng.
