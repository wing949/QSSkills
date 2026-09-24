# SỔ TAY HƯỚNG DẪN SỬ DỤNG HỆ SINH THÁI MULTI-AGENT ĐO BÓC KHỐI LƯỢNG CSA
## (CSA Takeoff Suite — Practical User Guide & Standard Prompts)

---

## 1. TỔNG QUAN HỆ THỐNG
Hệ sinh thái **`csa-takeoff-suite`** là bộ công cụ AI Multi-Agent chuyên nghiệp được thiết kế theo chuẩn Tổng thầu xây dựng (chuẩn hóa từ tài liệu chuyên đề đào tạo QS 2024 và dự án thực tế **ASCO VIET NAM FACTORY - PHASE 1**).

### 🎯 Chuẩn 5 Cột Kỹ Thuật (A - E) & Nguyên Tắc Toàn Vẹn Bảng Tính
Hệ sinh thái tập trung **100% vào 5 cột kỹ thuật đo bóc** chuẩn Tổng thầu:
* **Cột A (STT / Mã hiệu / WBS):** Hệ thống mã phân cấp công tác WBS (I, II, III...; A, B, C...; 1, 2, 3...). Canh giữa, bold.
* **Cột B (Diễn giải / Description / 描述):** Mô tả công việc chi tiết, mác vật liệu, kích thước, điều kiện thi công (Tam ngữ Việt - Anh - Trung chuẩn kỹ thuật TCVN / FIDIC / GB 50500 dịch bằng Gemini, cấm Google Translate). Độ rộng 65, canh trái, wrap text.
* **Cột C (Đơn vị / Unit / 单位):** Đơn vị tính kỹ thuật chuẩn ($m, m^2, m^3, kg, \text{Tấn}, \text{Cái}, \text{Bộ}, \text{Lot}$). Canh giữa.
* **Cột D (Khối lượng / Quantity / 数量):** Khối lượng hình học chính xác tính trực tiếp từ CAD. BẮT BUỘC **IN ĐẬM (`bold=True`)**, canh phải, format `#,##0.00`.
* **Cột E (Công thức tóm tắt & Calc ID / Quick Formula / 计算索引):** Kích thước chính, khấu trừ chính, vị trí và `Calc ID`. BẮT BUỘC *IN NGHIÊNG (`italic=True`)*, rộng 65, canh trái, wrap text; truy vết đầy đủ nằm tại `Takeoff_Calculation`.

🚫 **QUY TẮC TOÀN VẸN BẢNG TÍNH (1 ITEM = 1 SINGLE ROW):**
* **Mỗi công tác chỉ chiếm đúng 1 HÀNG DUY NHẤT.**
* **TUYỆT ĐỐI KHÔNG chèn thêm hàng phụ bên dưới BOQ** để ghi công thức. Một item phức tạp có thể có nhiều dòng phép tính tại `Takeoff_Calculation`, liên kết bằng `Calc ID`.

📑 **QUY TẮC CẤU TRÚC 4 SHEET:**
* **Sheet 1 (`BOQ`):** Phản ánh **100% khối lượng hình học thực tế** trích xuất từ bản vẽ CAD/BIM (**Zero Fabrication Policy**). Tuyệt đối cấm tự bịa chi tiết cốt thép, tiết diện khi bản vẽ chưa thể hiện.
* **Sheet 2 (`Takeoff_Calculation`):** Truy vết phép tính với Calc ID, WBS, vị trí/cấu kiện, bản vẽ/revision, nguồn hình vẽ, công thức, khấu trừ, ĐVT, khối lượng, trạng thái, người kiểm tra và ghi chú.
* **Sheet 3 (`RFI_Kien_Nghi_Bo_Sung`):** Tám cột: Mã RFI; WBS/Hạng mục; Vị trí–Bản vẽ–Revision; ĐVT & Khối lượng dự trù; Công thức tạm tính; Cơ sở kỹ thuật & câu hỏi; Tác động chi phí/tiến độ; Người phụ trách–Trạng thái–Hạn xử lý.
* **Sheet 4 (`QA_Audit`):** Nhật ký Gate, quy tắc, đối tượng, mức độ, bằng chứng, hành động, người phụ trách, trạng thái và ngày kiểm tra.
*(Tuyệt đối không quan tâm đến đơn giá, thành tiền hay phân tích giá thầu).*

---

## 2. DANH SÁCH 6 AGENT CHUYÊN TRÁCH

```
                          ┌──────────────────────────────────────────────┐
                          │         1. CSA-ORCHESTRATOR AGENT            │
                          │   (Kỹ sư Trưởng / Điều phối viên BOQ)        │
                          └──────────────────────┬───────────────────────┘
                                                 │
            ┌───────────────────┬────────────────┴───────────────────┬───────────────────┐
            ▼                   ▼                                    ▼                   ▼
┌──────────────────────┐┌──────────────────────┐  ┌──────────────────────┐┌──────────────────────┐
│2. STRUCTURAL-TAKEOFF ││3. ARCHITECTURAL-     │  │4. INFRASTRUCTURE-    ││5. METHOD-TEMPORARY-  │
│        AGENT         ││    TAKEOFF AGENT     │  │    TAKEOFF AGENT     ││    TAKEOFF AGENT     │
│ (Chuyên gia Kết cấu) ││(Chuyên gia Hoàn thiện│  │ (Chuyên gia Hạ tầng) ││  (Chuyên gia BPTC)   │
└──────────┬───────────┘└──────────┬───────────┘  └──────────┬───────────┘└──────────┬───────────┘
           │                       │                         │                       │
           └───────────────────────┼─────────────────────────┴───────────────────────┘
                                   │ Chuyển dữ liệu chuẩn
                                   ▼
                          ┌──────────────────────────────────────────────┐
                          │            6. CSA-QAQC-AUDIT AGENT           │
                          │   (Chuyên viên Thẩm tra & Kiểm soát BOQ)     │
                          └──────────────────────────────────────────────┘
```

1. **`csa-orchestrator` (Lead QS Agent):** Điều phối toàn bộ dự án, phân rã WBS, giao việc cho các Subagent và là agent duy nhất tổng hợp/phát hành workbook 4 sheet.
2. **`csa-structural-takeoff` (Structural Agent):** Bóc cọc, ép âm, đất đào/đắp, bê tông, ván khuôn, cốt thép (móng, đà kiềng, cột, dầm, sàn, cầu thang, móng máy, bể ngầm).
3. **`csa-architectural-takeoff` (Architectural Agent):** Bóc xây tường, trát, ốp lát, sơn (**chỉ tới trần thạch cao**), trần vách nhẹ chống cháy, cửa & vách kính, chống thấm (vén chân tường 300mm, màng TPO kèm xốp PE).
4. **`csa-infrastructure-takeoff` (Infrastructure Agent):** Bóc san lấp, đường nội bộ, sân bãi, hệ thống thoát nước (hố ga, mương kín/hở, cống ly tâm, bể tự hoại), hàng rào, cổng, cảnh quan cây xanh.
5. **`csa-method-temporary-takeoff` (Method & Temporary Agent):** Bóc cừ Larsen, shoring, bơm hạ nước ngầm, cẩu tháp, vận thăng, giàn giáo cột cao, giàn giáo bao che an toàn, phụ trợ mặt bằng tạm.
6. **`csa-qaqc-audit` (QA/QC Audit Agent):** Thực thi **Quy trình 5 Gate (0–4)** và ghi bằng chứng/hành động vào `QA_Audit`, không phát hành BOQ cạnh tranh.

---

## 3. CÁC KỊCH BẢN SỬ DỤNG THỰC TẾ & CÂU LỆNH (PROMPTS) MẪU

> [!TIP]
> **TẠI SAO PROMPT CHỈ CẦN 1 CÂU NGẮN GỌN?**
> Toàn bộ các quy tắc kỹ thuật chuyên sâu (phân rã WBS, điều phối Subagents, Single RC Baseline, kế thừa ván khuôn trần, đối chiếu chéo 3 chiều, QA/QC 5 Gate, chuẩn 5 cột A-E, Tam ngữ, workbook 4 sheet) **ĐÃ ĐƯỢC TÍCH HỢP SẴN TRONG HỆ THỐNG SKILLS**.
> 
> Vì vậy, trong công việc hàng ngày, bạn **HOÀN TOÀN KHÔNG CẦN lặp lại các bước kỹ thuật dài dòng**. Bạn chỉ cần dùng **Prompt Tối Giản** bên dưới, AI sẽ tự động kích hoạt và thực thi đầy đủ toàn bộ quy chuẩn!

> [!IMPORTANT]
> Khi cần **file BOQ `.xlsx` chính thức**, chỉ cần gọi `csa-orchestrator`. Bạn **không cần** nhắc `csa_excel_styler.py` trong prompt thường ngày: đó là quy tắc nội bộ bắt buộc của skill. Không yêu cầu agent “tạo một file Python xuất Excel” hoặc chạy script Excel cũ; các agent chuyên ngành chỉ bàn giao dữ liệu đo bóc, không phát hành workbook.

---

### 🔹 KỊCH BẢN 1: Bóc trọn gói một công trình từ A đến Z (End-to-End)
* **Khi nào dùng:** Khi có bản vẽ của một hạng mục hoàn chỉnh (Nhà bảo vệ, Nhà xe, Trạm bơm, Nhà xưởng chính) và cần xuất ra bảng BOQ đầy đủ chuẩn 5 cột A-E.
* **Agent tiếp nhận:** `csa-orchestrator`.
* **Prompt tối giản (khuyên dùng hằng ngày):**
  ```text
  Hãy đóng vai trò Lead QS Orchestrator, bóc tách khối lượng toàn bộ hạng mục Nhà Bảo Vệ B19 theo bản vẽ đính kèm và phát hành BOQ chính thức.
  ```
  *(Skill tự dùng `csa_excel_styler.py`, kiểm tra Document Register, RFI và các Gate; bạn không cần nhắc lại.)*
* **Prompt tăng cường (chỉ dùng khi đang chuyển đổi từ script Excel cũ):**
  ```text
  Hãy đóng vai trò Lead QS Orchestrator, bóc tách khối lượng toàn bộ hạng mục Nhà Bảo Vệ B19 theo bản vẽ đính kèm và phát hành BOQ chính thức. Chỉ phát hành qua csa_excel_styler.py; không tạo hoặc dùng script Excel thủ công.
  ```
* **Khi nào cần thêm nội dung?** Chỉ thêm khi dự án có điều kiện hợp đồng hoặc mặt bằng đặc thù, ví dụ:
  ```text
  Hãy đóng vai trò Lead QS Orchestrator, bóc tách khối lượng toàn bộ hạng mục Nhà Bảo Vệ B19 theo bản vẽ đính kèm. Lưu ý: Áp dụng hợp đồng Trọn gói (Lump Sum), đất đào lên phải vận chuyển đổ đi toàn bộ không đắp lại.
  ```

---

### 🔹 KỊCH BẢN 2: Bóc chuyên sâu một gói Kết cấu BTCT
* **Khi nào dùng:** Khi có bản vẽ móng, cột, dầm, sàn và cần kiểm tra độc lập bê tông, ván khuôn, thép theo hồ sơ và biện pháp được duyệt.
* **Agent tiếp nhận:** `csa-structural-takeoff`.
* **Prompt Tối Giản (Khuyên dùng hàng ngày):**
  ```text
  Hãy đóng vai trò Structural Takeoff Agent, bóc tách khối lượng Kết cấu cho sàn tầng 2 trục 1-5 theo bản vẽ kết cấu đính kèm.
  Chỉ bàn giao dữ liệu WBS/Calc ID/phép tính/trạng thái cho csa-orchestrator; không tạo file Excel.
  ```
* *(Agent kiểm tra phạm vi thực sự cần coffa, trừ giao theo cơ sở đo bóc, nối chồng/thép cấu tạo theo hồ sơ, và tách dữ liệu đáy dầm/sàn để chuyển giao cho Hoàn thiện).*

---

### 🔹 KỊCH BẢN 3: Bóc gói Hoàn thiện Kiến trúc (Tránh bóc thừa/sót)
* **Khi nào dùng:** Khi cần bóc tách hoàn thiện phòng, tầng hoặc cả tòa nhà mà không bị lỗi bóc thừa sơn hoặc thiếu lanh tô/bổ trụ.
* **Agent tiếp nhận:** `csa-architectural-takeoff`.
* **Prompt Tối Giản (Khuyên dùng hàng ngày):**
  ```text
  Hãy đóng vai trò Architectural Takeoff Agent, bóc tách khối lượng Hoàn thiện cho tầng 1 Nhà Văn phòng theo bản vẽ kiến trúc đính kèm.
  Chỉ bàn giao dữ liệu WBS/Calc ID/phép tính/trạng thái cho csa-orchestrator; không tạo file Excel.
  ```
* *(Agent sẽ tự động áp dụng: Single RC Baseline theo Kết cấu, trát trần lộ thiên kế thừa ván khuôn, sơn chỉ tới trần, đối chiếu chéo 3 chiều cho cửa và diện tích phòng).*

---

### 🔹 KỊCH BẢN 4: Thẩm tra, soát lỗi bảng tính BOQ có sẵn (Audit & QA/QC)
* **Khi nào dùng:** Khi nhận được file Excel BOQ từ cấp dưới hoặc từ đối tác/thầu phụ gửi sang và cần rà soát độ tin cậy.
* **Agent tiếp nhận:** `csa-qaqc-audit`.
* **Prompt Tối Giản (Khuyên dùng hàng ngày):**
  ```text
  Hãy đóng vai trò QA/QC Audit Agent, thực hiện thẩm tra toàn diện bảng khối lượng trong file Excel đính kèm.
  ```
* *(Agent sẽ chạy 5 Gate (0–4), quét lỗi, soát đơn vị và truy vết, kiểm tra benchmark có điều kiện, Pareto 80/20, đối chiếu chéo và Zero Fabrication; kết quả ghi vào `QA_Audit`.)*

---

### 🔹 KỊCH BẢN 5: Bóc khối lượng Hạ tầng ngoài nhà
* **Khi nào dùng:** Khi cần bóc hệ thống đường nội bộ, thoát nước, hố ga, hàng rào, cảnh quan sân bãi.
* **Agent tiếp nhận:** `csa-infrastructure-takeoff`.
* **Prompt Tối Giản (Khuyên dùng hàng ngày):**
  ```text
  Hãy đóng vai trò Infrastructure Takeoff Agent, bóc khối lượng tuyến đường bê tông nội bộ và hệ thống thoát nước mưa theo bản vẽ hạ tầng đính kèm.
  Chỉ bàn giao dữ liệu WBS/Calc ID/phép tính/trạng thái cho csa-orchestrator; không tạo file Excel.
  ```
* *(Agent sẽ tự động bóc đủ: Đầm K98, cấp phối đá dăm, bạt PE, bê tông mặt đường, lưới thép, khe co giãn, hố ga, mương đan, cống ly tâm, hàng rào, cảnh quan).*

---

### 🔹 KỊCH BẢN 6: Bóc Biện pháp Thi công & Công tác Tạm (BPTC)
* **Khi nào dùng:** Khi cần bóc các chi phí phụ trợ, thiết bị thi công và biện pháp an toàn cho công trường.
* **Agent tiếp nhận:** `csa-method-temporary-takeoff`.
* **Prompt Tối Giản (Khuyên dùng hàng ngày):**
  ```text
  Hãy đóng vai trò Method & Temporary Works Agent, bóc tách danh mục Biện pháp Thi công và Công tác Tạm cho dự án theo hồ sơ đính kèm.
  Chỉ bàn giao dữ liệu WBS/Calc ID/phép tính/trạng thái cho csa-orchestrator; không tạo file Excel.
  ```
* *(Agent sẽ tự động bóc đủ: Cừ Larsen, shoring, bơm nước ngầm, cẩu tháp, vận thăng, giàn giáo cột cao, giàn giáo bao che, điện nước thi công, lán trại kho bãi).*

---

## 4. BẢNG TRA CỨU NHANH QUY TẮC VÀNG (CHEAT SHEET)

| Hạng mục | Quy tắc kỹ thuật bắt buộc | Cơ sở xử lý lỗ mở |
|---|---|:---:|
| **Bê tông Cột** | Tính từ mặt sàn dưới đến đáy dầm/sàn trên. | Không trừ thép chiếm chỗ; lỗ mở theo hợp đồng/spec/phương pháp đo bóc. |
| **Bê tông Dầm** | Tính phần bụng dầm dưới đáy sàn, trừ giao cột. | Sàn tính trùm qua dầm (không trừ dầm) |
| **Ván khuôn** | Chỉ tính mặt thực sự cần coffa; trừ giao dầm vào cột, dầm phụ vào dầm chính. Tách riêng thông tầng $> 6\,\text{m}$. | Theo hợp đồng/spec/phương pháp đo bóc; không dùng ngưỡng tuyệt đối. |
| **Cốt thép** | Nối chồng tính theo cây đường kính lớn hơn ($35d - 40d$). Bắt buộc có thép chân chó, đai chữ U. | Trọng lượng: $q = \frac{d^2}{162.2}\,(kg/m)$ |
| **Xây tường** | Trừ toàn bộ bê tông lanh tô, giằng, bổ trụ. Bổ trụ khi $L>4\text{m}$, giằng khi $H>4\text{m}$. | Theo hợp đồng/spec/phương pháp đo bóc; không dùng ngưỡng tuyệt đối. |
| **Khung Bê tông Đấu thầu** | **SINGLE RC BASELINE:** Bắt buộc dùng đúng tiết diện dầm/cột bản vẽ Kết cấu để khấu trừ xây/trát ("Bê tông bóc ở đâu thì trừ ở đó"). Tính đủ trát cạnh cột lồi. | Không trừ theo dầm/cột Kiến trúc cũ |
| **Trát tường trong** | **Có trần:** Trát cao hơn trần $100\,\text{mm}$ ($H_{\text{trát}} = H_{\text{trần}} + 0.1\text{m}$).<br>**Không trần:** Trát tới đáy sàn/mái.<br>**Bóc riêng trát cột, dầm BTCT** (kể cả phần cột lồi nhô ra khỏi tường). | Không trát kịch sàn khi có trần treo |
| **Trát & Sơn Trần BTCT** | **Kế thừa từ Kết cấu:** Lấy trực tiếp từ diện tích Ván khuôn đáy sàn + đáy dầm + cạnh dầm lộ thiên khu vực không đóng trần (canopy, sê nô, tầng hầm). | Có trần treo $\rightarrow = 0\,\text{m}^2$ (không trát/sơn) |
| **Sơn tường** | **Chỉ tính đến cao độ trần thạch cao**. Trừ diện tích ốp gạch/đá. | Không sơn tường trên trần treo |
| **Cửa & Cửa sổ** | **ĐỐI CHIẾU CHÉO 3 CHIỀU:** Mặt bằng (Plan) $\leftrightarrow$ Mặt đứng (Elevations) $\leftrightarrow$ Bảng Schedule. Tuyệt đối không chỉ lấy số từ Schedule. | Kiểm tra đúng cao độ bậu cửa ($SH$) và vị trí mở |
| **Phòng, Trần & Ốp lát** | **ĐỐI CHIẾU CHÉO 3 CHIỀU:** BẮT BUỘC đo kích thước lọt lòng hình học thực tế ($L \times W - \sum S_{\text{cột lồi}}$) trên Mặt bằng $\leftrightarrow$ Đối chiếu Bảng thống kê phòng/trần (Room/Ceiling Schedule). Cột E bắt buộc thể hiện công thức $L \times W$ kèm kết quả đối soát. | Chênh lệch $\le 2\%$ cho phép làm tròn; Lệch lớn $\rightarrow$ Bắt buộc lấy theo hình học CAD |
| **Chống thấm** | Chân tường WC, ban công, sê-nô: **Vén cao tối thiểu $300\,\text{mm}$** ($P_{\text{chu vi}} \times 0.3\,\text{m}$). | Màng TPO sàn mái có xốp PE Foam $10\text{mm}$ |
| **Bể ngầm** | Bắt buộc có: Chống thấm lỗ ty ván khuôn, Waterstop V20, cán vữa dốc, chống thấm 2 mặt. | Tính theo số lượng ty xuyên thành bể |
| **Móng máy** | Bắt buộc có: Vát góc 4 cạnh chamfer ($m$), xoa mặt ($m^2$), vữa Sika Grout chân đế ($m^3$). | Theo kích thước bản mã chân đế máy |

---

## 5. DẢI HÀM LƯỢNG THÉP BENCHMARK DÙNG ĐỂ KIỂM CHỨNG NHANH
*(Dùng khi Gate 2 của QA/QC kiểm tra độ tin cậy)*

* **Móng đơn / Móng băng:** $80 - 110\,\text{kg}/\text{m}^3$
* **Móng bè / Đài cọc:** $100 - 140\,\text{kg}/\text{m}^3$
* **Cột:** $160 - 250\,\text{kg}/\text{m}^3$
* **Dầm:** $140 - 200\,\text{kg}/\text{m}^3$
* **Sàn thông thường:** $90 - 130\,\text{kg}/\text{m}^3$ *(hoặc $10 - 15\,\text{kg}/\text{m}^2$ sàn)*
* **Vách hầm / Lõi thang:** $130 - 180\,\text{kg}/\text{m}^3$
* **Tổng thể công trình cao tầng BTCT:** $110 - 160\,\text{kg}/\text{m}^2$ sàn GFA
* **Nhà xưởng kết cấu thép:** $25 - 45\,\text{kg}/\text{m}^2$ sàn GFA
* **Tỷ lệ Ván khuôn / Bê tông:** $2.5 - 3.5\,\text{m}^2/\text{m}^3$ (dầm sàn)
* **Tỷ lệ Diện tích Trát / Diện tích Xây:** $1.8 - 2.0$
* **Ngoại lệ cho công trình nhỏ / thấp tầng / cấu kiện mỏng:**
  * Nhà phụ trợ (Bảo vệ, Trạm bơm): Sàn mỏng $100\,\text{mm}$, sê nô $\rightarrow$ Tỷ lệ VK/BT thực tế có thể đạt $8 - 12\,\text{m}^2/\text{m}^3$ (bình thường).
  * Móng đơn nhỏ: Hàm lượng thép $15 - 30\,\text{kg}/\text{m}^3$ khi thép cổ cột tính vào cột.

---

## 6. QUY CHUẨN XUẤT BÁO CÁO EXCEL (.XLSX) CHUẨN ĐẲNG CẤP EXECUTIVE CORPORATE
* **Quyền phát hành:** Chỉ `csa-orchestrator` tạo `.xlsx` chính thức bằng `csa_excel_styler.py`, từ `create_csa_workbook()` đến `save_and_validate_csa_workbook(...)`; không tạo/chạy/tái sử dụng script Python xuất Excel thủ công. Agent chuyên ngành chỉ bàn giao dữ liệu chuẩn.
* **Cấu trúc 4 sheet:**
  1. **`BOQ`:** 5 cột A–E; D là net design quantity, E là công thức tóm tắt + `Calc ID`. Bên ráp đơn giá có thể ẩn cột E mà không thay đổi dữ liệu BOQ.
  2. **`Takeoff_Calculation`:** truy vết 12 trường đầy đủ cho từng phép tính, bao gồm nguồn bản vẽ/revision, khấu trừ, trạng thái dữ liệu và người kiểm tra. Dưới bảng có hộp chú giải tiếng Việt cho các mã kiểm soát như `NET_DESIGN` và trạng thái đất.
  3. **`RFI_Kien_Nghi_Bo_Sung`:** 8 cột chuẩn, trong đó ĐVT & khối lượng dự trù ở D, công thức tạm tính ở E, cơ sở/câu hỏi ở F, tác động ở G và người phụ trách–trạng thái–hạn ở H.
  4. **`QA_Audit`:** Gate, quy tắc, đối tượng, mức độ, bằng chứng, hành động, người phụ trách, trạng thái, ngày kiểm tra.
* **Điều kiện lưu:** Orchestrator truyền `Document Register` chính thức vào hàm lưu. Hàm tự chuẩn hóa độ rộng cột, AutoFit hàng, tắt gridline và tái kiểm tra sau lưu: mọi BOQ.D phải khớp tổng Calc ID `Verified` + `NET_DESIGN` cùng WBS/ĐVT; RFI phải đủ 8 cột và chỉ `Resolved`/`Closed`/`Cancelled`; QA phải đủ 9 cột, dùng trạng thái chuẩn và không còn `Open`/`RFI Required` hiệu lực ở bất kỳ Gate/đối tượng nào.

---

## 7. QUY TẮC SỐ 1: TUYỆT ĐỐI CẤM BỊA SỐ LIỆU (ZERO FABRICATION POLICY)
* **KHÔNG BAO GIỜ** được tự ý gán, sao chép, hay mặc định lấy số liệu từ BOQ tham khảo (BASE/VE) hoặc từ bất kỳ nguồn có sẵn nào vào cột Khối lượng (Cột D).
* **MỌI con số khối lượng** phải là **kết quả tính toán trực tiếp** từ dữ liệu hình học thực tế của bản vẽ CAD/BIM, kèm công thức hình học minh bạch.
* Nếu không có đủ dữ liệu bản vẽ, **BẮT BUỘC ghi rõ sang Sheet RFI để yêu cầu bổ sung** thay vì tự ý điền một con số ước lượng.
* Vi phạm nguyên tắc này được coi là **sai sót nghiêm trọng nhất** trong toàn bộ quy trình đo bóc.

---

## 8. HƯỚNG DẪN CÀI ĐẶT & CHUYỂN GIAO SANG MÁY KHÁC (ENVIRONMENT SETUP & MIGRATION)

### 📌 1. Thư mục Plugin & Skills
* **Đường dẫn Global:** `%USERPROFILE%\.gemini\config\plugins\csa-takeoff-suite\`
* **Đường dẫn Workspace:** `<Thư_Mục_Dự_Án>\.agents\plugins\csa-takeoff-suite\`

### 📌 2. Yêu cầu Runtime & Dependencies
* **Python $\ge 3.10$** (Tích chọn `"Add python.exe to PATH"` khi cài đặt trên Windows).
* **Các thư viện Python cần thiết (`requirements.txt`):**
  - `openpyxl`: Xử lý Excel BOQ 4 Sheet & AutoFit (`csa_excel_styler.py`).
  - `ezdxf`: Đọc và trích xuất thực thể CAD vector (`.dxf`).
  - `pymupdf` (`fitz`): Đọc và bóc tách bản vẽ PDF.
  - `matplotlib`, `pillow`: Xử lý hình ảnh và biểu đồ.
* **Lệnh cài đặt nhanh:**
  ```powershell
  # Chạy script 1-click có sẵn:
  setup_env.bat
  # Hoặc lệnh pip:
  pip install -r requirements.txt
  ```

### 📌 3. Công cụ chuyển đổi CAD (.dwg sang .dxf)
* Python và `ezdxf` đọc file `.dxf`. Khi dự án cấp file `.dwg`:
  - **Khuyên dùng (Free 100%):** Cài phần mềm **ODA File Converter** (Open Design Alliance) để chuyển đổi cả thư mục DWG sang DXF 2018 chỉ với 1 click.
  - **Nếu có AutoCAD:** Dùng lệnh `DXFOUT` hoặc script `export_dxf.scr`.
  - **Nếu có Antigravity IDE:** Dùng MCP Server `dwg-mcp`.

