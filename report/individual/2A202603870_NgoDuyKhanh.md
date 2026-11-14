# Báo cáo cá nhân — Day 6

Tôi so sánh ba chiến lược chuẩn bị dữ liệu trên cùng corpus và benchmark. Tôi đã đối chiếu các mẫu với tài liệu nguồn và xác nhận điểm đánh giá cho 30 mẫu coherence, 15 lượt grounding và 45 bản ghi metadata.

Họ và tên: **Ngô Duy Khánh** · MSSV: **2A202603870** · Lớp: **L3B**.

## Dữ liệu và pipeline

- Chủ đề: ứng dụng AI, việc làm, kỹ năng, đổi mới và chính sách tại Đông Á–Thái Bình Dương.
- Nguồn: World Bank (2026), *Riding the AI Wave*, DOI https://doi.org/10.1596/978-1-4648-2362-6. PDF đầy đủ ở `data/tailieu.pdf`, 122 trang. Giấy phép ghi ở trang PDF 6: CC BY 3.0 IGO; cần ghi công và kiểm tra điều kiện nội dung bên thứ ba.
- Corpus: đúng 30 trang vật lý PDF 75–104, tương ứng trang in 55–84 của chương 2; không tính bìa, mục lục hay references. Có 124.725 ký tự sau chuẩn hóa; manifest lưu SHA-256 và số ký tự mỗi trang. Tôi truy cập/tải tài liệu ngày **14/11/2026**; ngày này đã được ghi trong manifest.
- Trích text bằng pypdf, Unicode NFC, thu gọn khoảng trắng ngang và giữ xuống dòng. 30 trang đã chọn không rỗng; lỗi extraction được ghi và dừng. Chưa loại header/footer, phục hồi bảng/biểu đồ, sửa lỗi thứ tự hai cột hoặc nối đoạn qua trang. Các giới hạn này ảnh hưởng trực tiếp chunking.
- Embedding local: `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, 384 chiều, CPU 4 threads, batch 16, seed 42. Query dùng prefix `query: `, document dùng `passage: `; chuẩn hóa L2. Token dài nhất trong tài liệu đã embed là 251; code từ chối vượt giới hạn model thay vì cắt ngầm.
- PostgreSQL 16.15 + pgvector 0.8.6; exact cosine, không ANN. Do máy chưa có Docker, runtime local cài qua conda-forge trong `.runtime/`; chỉ lắng nghe 127.0.0.1:55433. Bảng `day6_chunks`, khóa `(strategy, chunk_id)`, metadata JSONB và filter tham số hóa trước xếp hạng.
- Nạp dữ liệu bằng thay snapshot từng strategy trong transaction, ID ổn định theo nguồn, trang, phương pháp, offset và text. Xóa chunk không còn tồn tại khi nguồn đổi; không sửa các bảng ngoài lab. Nạp lại A/B/C giữ nguyên số lượng và hash nội dung/metadata/vector.
- Metadata: document_id, source, page vật lý; printed_page = page − 20; chapter=2, language=en, year=2026 theo PDF; section từ mục lục. Section là nhãn theo trang, trang chuyển mục có thể chứa mục trước; Box 2.1 nằm trong Policy implications. Hữu ích cho truy nguồn và lọc phạm vi, chưa phải phân loại từng đoạn.
- Model card: https://huggingface.co/intfloat/multilingual-e5-small ; vector store: https://github.com/pgvector/pgvector .

## Cấu hình và benchmark

| Strategy | Chunk | Filter |
|---|---|---|
| A | Fixed 500 ký tự, overlap 75 | Không |
| B | Đoạn/heading suy ra từ dòng PDF, tối đa 900 ký tự; split block quá dài theo câu/từ; overlap 0 | Không |
| C | Chính chunk và vector của B | section chỉ khi câu hỏi cung cấp |

- A–B thay cách chia lẫn kích thước và overlap, nên không quy toàn bộ chênh lệch cho một tham số. B–C giữ nguyên chunk/model/vector/store/metric và chỉ thay filter, là so sánh có kiểm soát một yếu tố.
- Benchmark: 20 câu tiếng Việt, evidence tiếng Anh từ corpus; tôi đã đối chiếu và xác nhận cả 20 câu trước khi chạy. q01–q15 dev, q16–q20 test. Gold chính của hai tập khác trang nhưng cùng tài liệu, chủ đề lặp; không phải holdout độc lập theo tài liệu.
- Filter: q02/q06/q10 dev và q16 test; mục được nêu trong câu hỏi trước truy xuất. Không đưa gold, đáp án hoặc evidence vào embedding query/filter. C chạy không filter với 16 câu còn lại.
- Metric tự động: hit khi một chunk đúng document/page gold và chứa đầy đủ evidence_quote sau chuẩn hóa khoảng trắng. Hit@1 và Evidence Hit@3 báo tử/mẫu. Không cộng evidence nhiều chunk vào metric chính. Bằng chứng tương đương chưa được liệt kê đầy đủ: evaluator hỗ trợ alternative_gold được xác nhận; số hiện tại là strict quote-match, có thể bỏ sót bằng chứng đúng về nghĩa.
- Tiêu chí đã chốt trước chạy: Hit@3 dev giảm dần → Hit@1 dev giảm dần → tổng ingest + dev retrieval thấp hơn → tên strategy nếu vẫn hòa.
- Lựa chọn **C** được đóng băng tại `2026-11-14T03:08:32.032540+00:00` (UTC, tương ứng 10:08:32 ngày 14/11/2026 giờ Việt Nam), trước test. Xem `results/selection.json` cho hash corpus/code/benchmark/config và dev metrics. Không thay cấu hình sau khi xem test.

## Kết quả truy xuất thực tế

| Strategy | Split | Hit@1 | Evidence Hit@3 | Chunk count | Ingest (s) | Retrieval toàn split (s) | API USD |
|---|---|---|---|---:|---:|---:|---:|
| A | dev | 1/15 (6.7%) | 2/15 (13.3%) | 304 | 31.011 | 0.811 | 0 |
| B | dev | 4/15 (26.7%) | 6/15 (40.0%) | 191 | 6.195 | 0.671 | 0 |
| C | dev | 4/15 (26.7%) | 8/15 (53.3%) | 191 | 6.187 | 0.666 | 0 |
| A | test | 2/5 (40.0%) | 2/5 (40.0%) | 304 | 31.011 | 0.231 | 0 |
| B | test | 3/5 (60.0%) | 3/5 (60.0%) | 191 | 6.195 | 0.219 | 0 |
| C | test | 3/5 (60.0%) | 3/5 (60.0%) | 191 | 6.187 | 0.213 | 0 |

Ingest gồm chia chunk + document embedding + lần lưu đầu; không gồm tải/model load hoặc kiểm tra nạp lại. C tái sử dụng B nhưng được quy cùng thời gian embedding/chunking B cho so sánh chi phí triển khai độc lập. Retrieval gồm mở kết nối và SQL từng query, chưa gồm query embedding (đo riêng trong trace). Chỉ đo một lần theo thứ tự A→B→C, có ảnh hưởng warm-up/cache; không suy luận tốc độ ổn định từ chênh lệch này. Thời gian A embedding cao hơn có thể chịu warm-up vì chạy trước. Chi phí API 0; điện và khấu hao máy không đo.

| Strategy | Chunk chars min/median/max | Tổng ký tự chunk | Re-ingest trước/sau |
|---|---|---:|---|
| A | 88/500/500 | 145275 | 304/304 |
| B | 43/698/900 | 124725 | 191/191 |
| C | 43/698/900 | 124725 | 191/191 |

### Kết quả audit bổ sung bằng chứng tương đương

Tôi xác nhận đoạn ở trang PDF 77 (trang in 57) là bằng chứng tương đương hợp lệ cho q10, ngoài gold chính tại PDF 83. Tôi áp dụng cùng quy tắc chấp nhận nguồn bổ sung cho cả A/B/C trên chính các top-3 đã lưu; không chạy lại retrieval, không chỉnh model/chunk/filter. Phần này được xác nhận sau khi đã xem kết quả, nên được báo riêng với số gốc và không dùng lại để chọn cấu hình. Các bằng chứng tương đương khác chưa được rà soát đầy đủ.

| Strategy | Split | Hit@1 sau audit | Evidence Hit@3 sau audit |
|---|---|---|---|
| A | dev | 1/15 (6.7%) | 2/15 (13.3%) |
| B | dev | 5/15 (33.3%) | 7/15 (46.7%) |
| C | dev | 4/15 (26.7%) | 8/15 (53.3%) |
| A | test | 2/5 (40.0%) | 2/5 (40.0%) |
| B | test | 3/5 (60.0%) | 3/5 (60.0%) |
| C | test | 3/5 (60.0%) | 3/5 (60.0%) |

Chỉ B/q10/dev đổi từ miss sang hit ở top-1 và top-3: B đạt Hit@1 5/15 và Hit@3 7/15. A không truy xuất đoạn thay thế này; C đã có hit ở gold chính. Điểm test không đổi. Sau audit C vẫn có Hit@3 dev cao nhất (8/15), còn B có Hit@1 cao hơn C (5/15 so với 4/15). Điều này cho thấy filter không cải thiện mọi thứ hạng; lựa chọn C ban đầu vẫn được giữ theo tiêu chí ưu tiên Hit@3 đã chốt.

Chi tiết: `results/audit/alternative_evidence_approval.json`, `retrieval_audited_metrics.json` và `retrieval_audited_traces.json`. Có thể tái tính bằng `python starter/scripts/audit_retrieval.py` từ thư mục gốc.

## Audit năm khía cạnh

Tôi đã đọc và đối chiếu các mẫu với tài liệu nguồn, xác nhận điểm và lý do trong bảng dưới. Tôi kiểm tra metadata theo nguồn, trang và vị trí ký tự. Tôi đã thấy gold và kết quả truy xuất khi đánh giá, nên việc chấm không độc lập/mù và có nguy cơ thiên lệch. Hồ sơ điểm và xác nhận nằm trong `results/audit/coherence_samples.json`, `human_review.json`, `summary_human_review.json` và `approval.json`.

| Strategy | Coherence đã duyệt /2 (10 vị trí) | Metadata kiểm tra đủ/đúng | Top-3 tuân thủ filter test | Grounding đã duyệt 0/1/2 | Grounding đã duyệt /2 |
|---|---:|---|---|---|---:|
| A | 0.90 | 15/15 | 1/1 | 0/1/4 | 1.80 |
| B | 1.30 | 15/15 | 1/1 | 0/1/4 | 1.80 |
| C | 1.30 | 15/15 | 1/1 | 0/1/4 | 1.80 |

1. **Retrieval:** Số strict ban đầu: C tăng Hit@3 dev từ 6/15 lên 8/15 so với B. Sau khi tôi xác nhận nguồn tương đương q10, B đạt 7/15 và C giữ 8/15; lợi ích Hit@3 còn lại ở q06. Riêng q10, B đã có bằng chứng hợp lệ ở top-1 còn C ở top-2. Test B=C ở 3/5; không có bằng chứng C tốt hơn tổng quát.
2. **Coherence:** cùng 10 vị trí đầu nội dung sau header ở PDF 75–84, được quy định trong cấu hình trước chạy. B/C có một số câu trọn ý hơn A; vẫn lỗi nối trang và biểu đồ tuyến tính. Mẫu đầu trang thiên về heading/caption, chưa đại diện toàn corpus. B và C cùng chunk nên coherence bằng nhau.
3. **Metadata:** 15 bản ghi test mỗi strategy đối chiếu nguồn/trang/offset và metadata cấp trang, không phát hiện sai lệch theo quy tắc đã khai báo. A/B không áp dụng filter nhưng top-3 q16 tình cờ đều ở Policy implications, nên cả ba đều đạt 1/1; không lấy con số này làm bằng chứng filter cải thiện retrieval. section giúp C thu hẹp phạm vi q06/q10 ở dev, nhưng chỉ q06 còn tăng Hit@3 sau audit nguồn tương đương; hạn chế là nhãn trang thô và chỉ một câu filter test.
4. **Grounding:** chấm độ đủ bằng chứng của cả top-3, không chấm đáp án LLM; chưa xây chatbot sinh đáp án. q16 cả ba chỉ đạt 1 vì thiếu nghiên cứu trái chiều. Các câu còn lại đủ thông tin, đôi khi phải ghép hai chunk; vì thế đánh giá grounding có thể cao hơn proxy Hit@3.
5. **Strategy impact:** A tạo 304 chunk/145.275 ký tự do overlap, B/C 191 chunk/124.725 ký tự. B có Hit@3 tốt hơn A ở cả hai split, nhưng khác nhiều tham số. Theo số strict ban đầu, C tăng hit ở hai câu dev; sau audit q10, lợi ích Hit@3 còn một câu và Hit@1 của C thấp hơn B. C không tăng điểm test trong mẫu này. Lựa chọn vẫn là C theo dev đã chốt.

## Ví dụ lỗi có truy vết

- **q16, gold PDF 97:** A có trang 97 ở rank 2 nhưng bị cắt trước phần nghiên cứu không thấy tăng giá; B/C trả PDF 95,100,100, thiếu đoạn nghiên cứu trái chiều ở 97. Đây là thiếu điều kiện/bằng chứng phản biện, không thể trả lời đầy đủ từ top-3.
- **q18, A, gold PDF 101:** rank 1 chứa nhóm quốc gia và ưu tiên giáo dục cơ bản; rank 2 chứa đầu tư giáo dục bậc cao. Không chunk nào chứa toàn bộ evidence nên Hit@3=0, nhưng ghép hai chunk đủ grounding. B/C giữ đầy đủ trong top-1 nên hit.
- **q20, gold PDF 104:** A có số 30.000 vụ và 2.000 giờ công ở rank 1 nhưng gold gồm cả câu kết về thời gian giải quyết bị cắt; B/C chia ngay sau số 30.000 nên cần rank 1+2. Metric strict ghi miss cho cả ba; điểm grounding đã xác nhận vẫn 2 vì thông tin cần trả lời đủ trong top-3. Không sửa gold hoặc chunk sau khi thấy test.
- **q10 dev, B — false negative của gold ban đầu:** top-1 PDF 77 có đủ nội dung tương đương gold PDF 83. Tôi đã xác nhận nguồn bổ sung; bảng audit riêng sửa B/q10 thành hit. Số gốc và lựa chọn trước test vẫn được giữ để truy vết.

## Tái lập và artifacts

- Lệnh setup/run đầy đủ: `docs/PIPELINE.md`. Chạy lần lượt ingest → dev → freeze → test từ `starter/`. Không ghi đè kết quả cũ; lưu trữ lần chạy trước khi tái lập.
- Nguồn dữ liệu: `data/corpus_config.json`, `data/manifest.json`, `data/processed/pages.jsonl`.
- Trace đầy đủ: `results/dev_traces.json` (45 lượt), `results/test_traces.json` (15 lượt), mỗi lượt top-3 gồm ID/text/score/metadata và nhãn strict.
- Cấu hình/thời gian/phiên bản: `starter/experiment.json`, `results/ingestion.json`; log thí nghiệm: `artifacts/experiment_log.csv`.
- Mẫu và nhãn AI từng trường hợp: `results/audit/REVIEW.md`, `coherence_ai_review.json`, `grounding_ai_review.json`, `metadata_ai_review.json`, `summary_ai_review.json`.
- Nhãn tôi đã kiểm tra và xác nhận: `results/audit/coherence_samples.json`, `results/audit/human_review.json`; bảng tổng hợp `summary_human_review.json`, xác nhận `approval.json`. Hồ sơ đề xuất ban đầu được giữ để truy vết.
- Kiểm thử: 4 unit tests + 1 real pgvector integration test; kiểm tra persistence sau restart ghi trong `results/verification.json`.

Phiên bản thực tế: Python 3.14.7; torch 2.15.0, sentence-transformers 6.2.0, transformers 5.22.1, pypdf 7.0.0, psycopg 3.3.8, numpy 2.5.3. Runtime/model/database không commit, có hướng dẫn tải lại.

## Giới hạn và bước cải tiến

- Chỉ 30 trang, 20 câu, 5 test cùng một tài liệu; tất cả test thuộc phạm vi Policy implications. Không đủ để kết luận tổng quát hoặc so sánh thống kê.
- Gold alternatives chưa đầy đủ; strict quote-match có false negative. Tôi đã xác nhận nguồn thay thế q10 và ghi điểm audit riêng; các câu khác vẫn có thể có nguồn hợp lệ chưa được liệt kê. Không thay kết quả lựa chọn cấu hình ban đầu.
- PDF còn header/footer, lỗi xuống dòng giữa câu/giữa cột và số biểu đồ. Heuristic B đôi khi tách câu như q20; ưu tiên cải tiến chuẩn hóa bố cục và kiểm tra các đoạn nối trang trên dev trong thí nghiệm tương lai.
- Thời gian chỉ một lượt, có warm-up/cache và thứ tự chạy; chi phí không gồm điện, phần cứng và tải model.

- Nếu tiếp tục sửa chunk/model sau lần này, ghi thí nghiệm mới và dùng test mới cho kết luận độc lập. Không điều chỉnh trên test cũ.

## Công cụ hỗ trợ và cách kiểm chứng

Tôi sử dụng Codex để hỗ trợ triển khai mã nguồn, tạo bản nháp benchmark, thực thi lệnh, phân tích kết quả và đề xuất nhãn audit. Tôi đã kiểm tra 20 câu hỏi/đáp án với tài liệu nguồn, rà soát các mẫu audit và chấp nhận điểm cùng lý do đề xuất. Các nhãn đánh giá có hỗ trợ AI; tôi không coi đây là đánh giá độc lập/mù. File đề xuất gốc và hồ sơ xác nhận được giữ trong `results/audit/` để truy vết.

## Kiểm tra trước khi nộp

- Kiểm tra các đường dẫn dữ liệu, trace, nhãn đánh giá và lệnh chạy trong repo.
- Bổ sung commit chốt bài trong STUDENT.md sau khi commit và push.
- Xác minh người chấm truy cập được repo, rồi nộp link theo hướng dẫn lớp.
