# Chạy pipeline

## Đầu vào và thiết kế

- `data/processed/pages.jsonl`: đúng 30 trang PDF 75–104.
- `benchmark/questions.json`: 20 câu đã được học viên duyệt; 15 dev / 5 test.
- `starter/experiment.json`: model/revision, seed, tham số A/B/C và tiêu chí chọn chốt trước chạy.
- A: cửa sổ 500 ký tự, overlap 75. B: nhóm đoạn suy ra từ dòng PDF, tối đa 900 ký tự,
  không overlap. C: dùng chính chunk và vector của B, chỉ thêm filter đầu vào.
- B là heuristic dựa trên dấu kết câu, dòng trống, bullet/heading; không khẳng định
  phục hồi bố cục PDF chính xác. A–B thay cả cách chia, giới hạn độ dài và overlap,
  nên chỉ B–C cô lập một yếu tố (metadata filter).
- Model `intfloat/multilingual-e5-small`, revision cố định trong cấu hình, CPU,
  384 chiều, prefix `query: `/`passage: ` và vector chuẩn hóa L2.
  Code từ chối đầu vào vượt giới hạn token thay vì cắt ngầm.
- PostgreSQL + pgvector, exact cosine search, không HNSW/IVFFlat; filter JSONB trước xếp hạng.
- `day6_chunks` là bảng riêng của lab. Nạp một strategy là thay toàn bộ snapshot
  strategy đó trong transaction, loại cả chunk cũ; chunk ID ổn định theo nguồn/nội dung/vị trí.

## Môi trường đã dùng trên Windows

Máy chưa có Docker nên runtime được cài riêng trong `.runtime/`, không commit.
Nếu có conda, từ thư mục gốc:

```powershell
$env:CONDA_PKGS_DIRS = Join-Path (Get-Location) '.runtime/conda-pkgs'
python -m conda create --prefix .runtime/postgres --override-channels -c conda-forge postgresql=16.15 pgvector=0.8.6 --yes
python -m pip install -r starter/requirements.txt
powershell -ExecutionPolicy Bypass -File starter/scripts/start_local_postgres.ps1
```

Runtime này chỉ lắng nghe loopback, trust authentication dành cho lab local.
Không dùng đồng thời runtime này và Docker trên cùng cổng 55433.
Nếu dùng Docker, làm theo `starter/README.md`, copy `.env.example` thành `.env`
để dùng mật khẩu Docker; không commit `.env`.

Tải model thật (chỉ cần lần đầu; chưa gọi embedding):

```powershell
python -c "from huggingface_hub import snapshot_download; snapshot_download('intfloat/multilingual-e5-small', revision='614241f622f53c4eeff9890bdc4f31cfecc418b3', cache_dir='.runtime/huggingface', allow_patterns=['*.json','*.txt','*.model','*.safetensors','1_Pooling/*'], ignore_patterns=['onnx/*','openvino/*'])"
```

## Các giai đoạn (từ thư mục gốc)

```powershell
python starter/scripts/prepare_corpus.py
cd starter
python -m unittest discover -s tests -v
python -m src.run ingest
python -m src.run dev
python -m src.run freeze
python -m src.run test
```

`freeze` chọn theo Hit@3 dev, rồi Hit@1 dev, rồi ingest + dev retrieval seconds;
nếu vẫn bằng nhau, theo tên strategy. Query embedding giống nhau giữa strategy nên
không đưa vào tie-break. Model load, tải model, kiểm tra nạp lại không tính vào ingest
dùng tie-break. C tái sử dụng vector B nhưng được tính cùng chi phí embedding B để
so sánh cấu hình độc lập. Chi phí API bằng 0, không có nghĩa điện/phần cứng miễn phí.

Runner lưu fingerprint code/corpus/benchmark/config và từ chối test khi đã thay đổi.
Không ghi đè trace đã có; không chỉnh dev sau khi freeze. Muốn tái lập một lần chạy mới,
lưu trữ `results/` trước; sau khi đã xem test không coi việc chỉnh cấu hình trên cùng
test là đánh giá holdout độc lập. Đừng xóa kết quả cũ chỉ để che lịch sử.

Metric tự động là source/page đúng + đủ evidence nguyên văn, chuẩn hóa khoảng trắng.
Evaluator hỗ trợ `alternative_gold` đã xác nhận; bằng chứng tương đương chưa liệt kê
cần audit riêng, không tự coi sai về mặt ngữ nghĩa.

## Kết quả và kiểm chứng

`results/ingestion.json`: phiên bản, thời gian, phân bố độ dài, nạp lại không trùng.
`results/chunks/`: nội dung và offset từng chunk.
`results/dev_traces.json`, `test_traces.json`: đầy đủ top-3 và score/metadata/nhãn tự động.
`results/*_metrics.json`: tử/mẫu và tỷ lệ riêng theo split.
`results/selection.json`: quyết định từ dev, timestamp và fingerprint trước test.
`results/audit/`: mẫu cùng 10 vị trí nguồn cho coherence và audit test.

Các mẫu audit đã được học viên đối chiếu và xác nhận; dùng `summary_human_review.json`
làm bảng tổng hợp hiện hành. Phương pháp hỗ trợ AI được ghi trong báo cáo;
các file `*_ai_review.json` là hồ sơ đề xuất ban đầu, không phải trạng thái duyệt hiện tại.

Dừng database nhưng giữ dữ liệu:

```powershell
& ./.runtime/postgres/Library/bin/pg_ctl.exe -D .runtime/pgdata -m fast -w stop
```

Nguồn kỹ thuật: https://huggingface.co/intfloat/multilingual-e5-small,
https://github.com/pgvector/pgvector. Xem `results/ingestion.json` cho phiên bản thực tế.

## Audit retrieval bổ sung

Nguồn tương đương q10 đã được tác giả xác nhận. Xem `results/audit/alternative_evidence_approval.json`,
`results/audit/retrieval_audited_metrics.json` và `results/audit/retrieval_audited_traces.json`
(đường dẫn tính từ thư mục gốc dự án). Tái tính từ trace đã lưu bằng
`python starter/scripts/audit_retrieval.py`. Không ghi đè benchmark, kết quả gốc hay lựa chọn trước test.
