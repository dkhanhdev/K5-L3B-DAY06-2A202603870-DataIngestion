# Đối chiếu checkpoints và bài nộp

Rà soát ngày 14/11/2026. Các mốc bên dưới là yêu cầu sản phẩm, không phải xác nhận
thời lượng đã làm hoặc hạn nộp.

| Checkpoint | Đánh giá | Minh chứng |
|---|---|---|
| 0:25 — dữ liệu và setup | Đủ minh chứng | data/manifest.json: 30 trang PDF 75–104, nguồn, giấy phép, ngày truy cập 14/11/2026; công cụ trích text và database đã chạy |
| 1:00 — benchmark | Đủ số lượng/split/evidence; còn giới hạn gold thay thế | benchmark/questions.json: 20 câu, 15 dev/5 test, 4 filter/1 filter test; 20 evidence khớp nguồn |
| 1:50 — chuẩn hóa và chunk | Đủ minh chứng | data/processed/pages.jsonl, results/corpus_preparation.json, results/chunks/A.jsonl và B.jsonl; offset truy nguồn |
| 2:00 — nghỉ | Không áp dụng kiểm tra artifact | Không suy diễn thời lượng làm bài từ kết quả |
| 2:40 — lưu vector, ba chiến lược | Đủ minh chứng của lần chạy đã lưu | results/ingestion.json, experiment.json; model thật/384 chiều, exact cosine, metadata filter, kiểm tra nạp lại; B/C cùng chunk |
| 3:30 — benchmark và audit | Có đủ trace/metrics/nhãn duyệt; đã bổ sung audit tương đương q10; còn giới hạn ở các câu khác | 45 lượt dev + 15 lượt test, top-3; 30 coherence, 15 grounding, 45 metadata đã được tác giả xác nhận; q10 đã được tác giả xác nhận nguồn thay thế và có bảng điểm audit bổ sung |
| 4:00 — báo cáo và nộp | Báo cáo/artifact có; bước nộp chưa hoàn tất | report/individual/2A202603870_NgoDuyKhanh.md, artifacts/experiment_log.csv, docs/PIPELINE.md; còn commit/push/quyền truy cập/nộp link |

## Những điểm chưa thể kết luận đã hoàn tất

1. Gold thay thế: q10/B trả đúng nội dung tương đương ở PDF 77 nhưng gold chính ở 83.
   Tác giả đã xác nhận; bảng audit riêng cho A/B/C đã được tính, chỉ B/q10/dev đổi điểm.
   Xem results/audit/retrieval_audited_metrics.json. Không sửa số gốc hoặc lựa chọn trước test.
   Các câu khác cũng có thể có bằng chứng tương đương chưa được liệt kê đầy đủ.
2. Nội dung bài đã commit local tại `d364e1bd1cbcce3d691fc0101af087392e661d7f`; SHA được ghi trong STUDENT.md.
   Commit thông tin tiếp theo chỉ cập nhật hồ sơ commit và trạng thái, không thay đổi thí nghiệm.
3. Chưa push/nộp trong phiên làm việc này; chưa xác minh người chấm truy cập repo.
4. Hướng dẫn tái lập đã có nhưng chưa thử lại từ một máy/môi trường hoàn toàn sạch.
5. PDF có điều kiện riêng với nội dung bên thứ ba; tác giả cần kiểm tra quyền chia sẻ
   các thành phần nếu tái sử dụng riêng. Không suy diễn giấy phép của toàn bộ hình/bảng.

## Kết quả kiểm tra tính nhất quán

Xem results/project_review_checks.json: corpus/PDF hash, evidence, split/filter,
trace/metrics, source offsets, thứ tự dev–freeze–test, B/C cùng chunk,
nhãn duyệt và hash phê duyệt đều khớp. Quét mẫu secret phổ biến không tìm thấy
trong các file chuẩn bị nộp; đây không phải đảm bảo phát hiện mọi loại secret.
Không chạy lại mô hình hoặc thay đổi code/corpus/benchmark đã cố định trong lần rà soát.

## Cách trình bày đã thống nhất

- Báo cáo và bản đọc audit dùng ngôi tôi, ghi nhận việc tác giả đã đối chiếu và xác nhận.
- Công cụ hỗ trợ và cách kiểm chứng nằm cuối báo cáo theo RULES.md.
- Các hồ sơ đề xuất AI gốc giữ nguyên; results/audit/README.md phân biệt hồ sơ lịch sử
  với nhãn hiện hành. Trạng thái pending ở hồ sơ lịch sử không phải còn thiếu duyệt.
- Một số docstring TODO trong code là chú thích từ starter, không phải hàm chưa hiện thực.
  Không đổi code chỉ để sửa chú thích trong lần rà soát này vì code đã được fingerprint.

## Phạm vi upload

Theo yêu cầu tác giả, PDF gốc không đưa lên Git; giữ local, có manifest/hash và
hướng dẫn lấy lại trong data/README.md. Code, nội dung trích xuất, benchmark,
trace, audit và báo cáo nằm trong bài nộp. Không upload .runtime, model cache hoặc .env.
