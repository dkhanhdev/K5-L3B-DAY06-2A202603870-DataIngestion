# Corpus

Giữ nguyên `tailieu.pdf`. Chỉ dùng trang PDF **75–104** (trang in **55–84**),
30 trang nội dung chương 2.

Chạy từ thư mục gốc:

```powershell
python starter/scripts/prepare_corpus.py
```

Nếu thiếu thư viện: `python -m pip install -r starter/requirements.txt`.

- `corpus_config.json`: nguồn, giấy phép, phạm vi trang và metadata.
- `manifest.json`: SHA-256, số trang và số ký tự thực tế từng trang.
- `processed/pages.jsonl`: đầu vào cho chunking, embedding và viết benchmark.
- `../results/corpus_preparation.json`: trạng thái chạy hoặc lỗi trích xuất.

`page` là số trang vật lý PDF từ 1; `printed_page` là số trang in.
`section` gán theo trang bắt đầu trong mục lục; trang chuyển mục có thể chứa hai mục.
Box 2.1 được xếp trong Policy implications. Kiểm chứng evidence trước khi viết câu hỏi.
Chưa phục hồi cấu trúc bảng/biểu đồ hoặc loại header/footer.

Nguồn theo PDF: World Bank (2026), *Riding the AI Wave*,
https://doi.org/10.1596/978-1-4648-2362-6.
Giấy phép CC BY 3.0 IGO tại trang PDF 6, lưu ý điều kiện nội dung bên thứ ba.
`accessed_at` là 2026-11-14, ngày học viên xác nhận đã truy cập/tải tài liệu.
`local_verified_at` là ngày kiểm tra file tại máy.

Pipeline trong `starter/src/` đã triển khai và chạy đủ A/B/C; xem `docs/PIPELINE.md`.
Các bước sau phải dùng `processed/pages.jsonl` để không ingest toàn bộ PDF.

## Lấy lại PDF gốc (không đưa vào Git)

PDF gốc được giữ local tại `data/tailieu.pdf` và được loại khỏi lịch sử Git bài nộp.
Người chấm có thể truy cập https://doi.org/10.1596/978-1-4648-2362-6 để tìm
báo cáo World Bank *Riding the AI Wave: East Asia and Pacific Economic Update,
October 2026*, tải bản PDF và lưu đúng đường dẫn trên. Đối chiếu SHA-256 với
`data/manifest.json` để xác nhận đúng snapshot; nếu hash khác thì ghi rõ khác phiên bản,
không coi là tái lập đúng cùng đầu vào. Sau đó chạy `python starter/scripts/prepare_corpus.py`.
Repo có sẵn nội dung 30 trang đã chuẩn hóa, benchmark, chunks, trace và nhãn audit
để kiểm tra kết quả mà không cần chạy lại embedding.
