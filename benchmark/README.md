# Benchmark
- `questions.json`: Gồm 20 câu đã được học viên duyệt ngày 2026-11-14. Dùng file này cho pipeline.
- `approval.json`: ghi nhận xác nhận của học viên và SHA-256 bản chính thức.
- `questions.draft.json`: bản nháp được giữ lại để truy vết.
- `REVIEW.md`: bản dễ đọc với checklist kiểm chứng từng câu.

## Trạng thái và cách chia

Chia trước thử nghiệm: q01–q15 là dev, q16–q20 là test.
Dev gồm 15 câu từ các trang 75–93 và 102; test gồm 5 câu từ các trang
97, 100, 101, 103, 104. Các trang gold chính không trùng giữa hai tập,
nhưng cùng một tài liệu và có chủ đề/bằng chứng lặp lại: đây không phải phân chia
độc lập theo tài liệu. Năm câu test là mẫu nhỏ; không suy rộng kết quả.

Có 4 câu filter: q02, q06, q10 (dev) và q16 (test).
Các câu này nêu mục nội dung ngay trong câu hỏi; filter `section` là đầu vào
ngữ cảnh có trước retrieval, không suy ra từ gold khi chạy. Section là metadata
cấp trang, có hạn chế ở trang chuyển mục. Corpus có 5 giá trị section phân biệt.
A/B bỏ qua filter; C chỉ áp dụng filter khác null, các câu còn lại không lọc.
Chỉ đưa `question` vào embedding query, tuyệt đối không đưa gold/evidence/đáp án.
Không dùng ID, split, type hoặc các trường review làm đặc trưng truy xuất.

## Checklist tham khảo khi duyệt (20 câu đã được học viên duyệt)

1. Đọc `REVIEW.md`, đối chiếu evidence với trang PDF tương ứng (không nhầm trang in).
2. Kiểm tra đáp án, điều kiện, ngoại lệ và lỗi thứ tự chữ trong bảng/biểu đồ.
3. Tìm thêm bằng chứng hợp lệ ở các trang khác, bao gồm phần tóm tắt lặp ý.
   Danh sách hiện tại chưa liệt kê đầy đủ nguồn thay thế. Evaluator sau này phải
   chấp nhận các bằng chứng tương đương được xác nhận, không chỉ một gold duy nhất.
4. Sửa câu mơ hồ và ghi người duyệt/ngày duyệt; không đánh dấu đã duyệt chỉ vì khớp chuỗi.
5. Chốt bản chính thức, split và tiêu chí chọn trước khi chạy thử.

Tiêu chí chọn cấu hình đã được xác nhận trước thử nghiệm:
ưu tiên Evidence Hit@3 dev, rồi Hit@1 dev; nếu bằng nhau, ưu tiên tổng thời gian
ingest + retrieval thấp hơn trên cùng máy và cùng cách đo. Không dùng test để chọn.

Tôi đã duyệt câu hỏi test trước khi chạy; kết quả dev được dùng chọn cấu hình C,
sau đó cố định lựa chọn trước khi đánh giá test (xem results/selection.json).
Sau khi chốt, chỉ dùng dev để sửa cấu hình. Nếu đã dùng kết quả test để sửa,
ghi rõ rò rỉ và chuẩn bị test mới nếu cần.
