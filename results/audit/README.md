# Hồ sơ đánh giá

## Kết quả hiện hành

- `REVIEW.md`: bản đọc gồm mẫu, điểm và lý do đã được tôi kiểm tra và xác nhận.
- `coherence_samples.json`: 30 nhãn coherence đã duyệt.
- `human_review.json`: 15 nhãn grounding và 45 bản ghi kiểm tra metadata đã duyệt.
- `summary_human_review.json`: bảng điểm tổng hợp hiện hành.
- `approval.json`: xác nhận duyệt, thời điểm ghi nhận và hash các file nhãn.
- `filter_compliance.json`: kết quả tuân thủ filter của top-3.

## Hồ sơ đề xuất gốc

Các file `coherence_ai_review.json`, `grounding_ai_review.json`,
`metadata_ai_review.json`, `summary_ai_review.json` được giữ nguyên để truy vết.
Trường `pending` trong những file này phản ánh thời điểm đề xuất ban đầu,
không phải trạng thái hiện tại. Học viên đã rà soát và chấp nhận các nhãn;
xem các file hiện hành bên trên. Công cụ và cách kiểm chứng được ghi ở cuối báo cáo.

## Audit retrieval bổ sung

Nguồn tương đương q10 đã được tác giả xác nhận. Xem `results/audit/alternative_evidence_approval.json`,
`results/audit/retrieval_audited_metrics.json` và `results/audit/retrieval_audited_traces.json`
(đường dẫn tính từ thư mục gốc dự án). Tái tính từ trace đã lưu bằng
`python starter/scripts/audit_retrieval.py`. Không ghi đè benchmark, kết quả gốc hay lựa chọn trước test.
