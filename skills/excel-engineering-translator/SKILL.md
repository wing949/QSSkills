---
name: excel-engineering-translator
description: |
  Chuyên gia dịch thuật song ngữ Trung - Việt và Anh - Việt cho hồ sơ dự toán,
  bảng khối lượng BOQ, hồ sơ mời thầu, thuyết minh kỹ thuật, bản vẽ thi công và
  bảng tính Excel chuyên ngành Xây dựng Dân dụng & Công nghiệp, Kiến trúc,
  Kết cấu Thép & Bê tông cốt thép, Hạ tầng Kỹ thuật, Cơ điện MEPF (Điện lực,
  Cấp thoát nước, HVAC Thông gió Điều hòa, PCCC, Điện nhẹ ELV).
  Kích hoạt khi user yêu cầu: "dịch file excel", "dịch bảng tính", "dịch BOQ",
  "dịch dự toán", "dịch tiếng trung sang tiếng việt excel", "chèn cột tiếng việt",
  "dịch thuật xây dựng mepf excel", "tạo bảng song ngữ excel", "dịch hồ sơ thầu excel".
---

# Goal

Tự động hóa và chuẩn hóa quy trình dịch thuật hồ sơ kỹ thuật, dự toán BOQ, biểu mẫu mời thầu dạng file Excel (Trung - Việt / Anh - Việt) đạt độ chính xác kỹ thuật chuyên sâu theo tiêu chuẩn kỹ sư dự án, bảo toàn 100% công thức, định dạng, merge cell và bố cục của file gốc.

---

# Mindset & Chuẩn mực Kỹ thuật

1. **Bảo tồn tính toàn vẹn dữ liệu (Data Integrity):**
   - Giữ nguyên cấu trúc, bố cục, định dạng, đường viền, màu sắc và nội dung nguyên bản của file gốc.
   - **Tuyệt đối không làm hỏng hoặc thay đổi công thức** (`SUM`, `SUBTOTAL`, `IF`, `VLOOKUP`...), số liệu đo bóc, đơn giá hay thành tiền.
   - Khi chèn thêm cột dịch (ví dụ cột Tiếng Việt ngay cạnh cột Tiếng Trung), cột dịch phải được thiết kế độc lập để người dùng có thể **xóa hoặc ẩn cột dịch bất kỳ lúc nào mà không làm ảnh hưởng đến form gốc**.

2. **Độ chính xác thuật ngữ Chuyên ngành (Engineering Rigor):**
   - Không dịch máy móc từng từ (*word-by-word*); phải hiểu đúng ngữ cảnh thi công, công nghệ xây dựng và hệ thống cơ điện thực tế tại Việt Nam (TCVN, chuẩn BOQ, dự toán, FIDIC).
   - Bảo toàn 100% các mã hiệu kỹ thuật, kích thước, tiêu chuẩn (ví dụ: `PHC-500A`, `C30`, `DN100`, `PN16`, `ZR-YJY 4*240+1*120`, `23J909`, `kW`, `m3/h`, `Pa`...).
   - Giữ nguyên cấu trúc xuống dòng `\n`, ký hiệu phân cấp (1., 2., 3., 1、, 2、...).

3. **Quy chuẩn hiển thị:**
   - Cột Tiếng Việt sử dụng font chữ **Arial**, kích thước **size 12** (hoặc size phù hợp theo yêu cầu), tự động bật thuộc tính `wrap_text=True` để hiển thị đầy đủ văn bản.

---

# Instructions — Quy trình 5 bước chuẩn hóa

```text
[Khảo sát File] ➔ [Trích xuất Từ vựng Độc nhất] ➔ [Dịch thuật AI Chuyên ngành] ➔ [Ghi đè & Format An toàn] ➔ [Kiểm toán Chất lượng]
```

### Bước 1: Khảo sát & Trích xuất cấu trúc Workbook
1. Sử dụng thư viện `openpyxl` để đọc workbook (chế độ `data_only=False` để bảo toàn công thức).
2. Liệt kê toàn bộ các Sheet, xác định phạm vi dịch:
   - Các Sheet thuyết minh / tổng hợp chung: dịch các cột nội dung, mô tả, quy tắc đo bóc.
   - Các Sheet chi tiết dự toán BOQ (từ Sheet 5 trở đi): chỉ dịch 2 cột trọng tâm (Tên công tác/Hạng mục và Đặc tính công việc/Quy cách kỹ thuật).
3. Kiểm tra xem file đã được chèn sẵn cột dịch hay cần chèn thêm cột mới.

### Bước 2: Trích xuất tập từ vựng độc nhất (Deduplication)
1. Quét toàn bộ các ô cần dịch trên tất cả các Sheet.
2. Thu thập danh sách chuỗi văn bản gốc không trùng lặp (`unique_texts`).
3. Lập chỉ mục vị trí cell tương ứng `(sheet_name, row, col_source, col_target)`.
4. *Lợi ích:* Giúp dịch đồng nhất 100% cùng một thuật ngữ trên toàn bộ dự án và giảm tải số lượng chuỗi cần xử lý tới 70-80%.

### Bước 3: Phân luồng dịch thuật AI theo Chuyên ngành (AI Subagents / Batches)
1. Chia danh sách chuỗi độc nhất thành các gói nhỏ (khoảng 100 - 130 mục/gói).
2. Điều phối các AI Subagent (`construction_translator`) dịch đồng thời theo đúng chuyên ngành:
   - **Gói Xây dựng & Kiến trúc (Civil/Arch):** Cọc móng, đất đá, bê tông cốt thép, kết cấu thép, xây trát, ốp lát, chống thấm, cửa, mái...
   - **Gói Hạ tầng & Ngoài nhà (Infrastructure):** Đường nội bộ, thoát nước mưa, thoát nước thải, cảnh quan, hố ga, cống hộp...
   - **Gói Cơ điện MEPF (Cơ & Điện):** Điện động lực, chiếu sáng, tủ điện, busway, cấp thoát nước, thiết bị vệ sinh, HVAC (AHU/FCU/Chiller/VRV), PCCC (sprinkler/họng nước vách tường/báo cháy), Điện nhẹ ELV (CCTV, Access Control, PA, LAN)...
3. Mỗi tác tử xuất kết quả dưới dạng JSON mapping: `{"chuỗi_gốc": "chuỗi_tiếng_việt"}`.

### Bước 4: Ghi đè & Định dạng An toàn vào Excel
1. Hợp nhất tất cả các file JSON dịch thành một `master_translation_dict.json`.
2. Ghi dữ liệu dịch vào cột chỉ định với xử lý an toàn:
   - **Xử lý MergedCell:** Kiểm tra ô đích có thuộc vùng merge hay không; nếu có thì cập nhật giá trị vào ô trên cùng bên trái (`min_row, min_col`) hoặc unmerge nếu là tiêu đề phân đoạn độc lập.
   - **Thiết lập Font:** Áp dụng font `Arial`, size `12` cho toàn bộ các ô Tiếng Việt.
   - **Bật Wrap Text:** Cài đặt `Alignment(wrap_text=True, vertical='center')`.
3. Lưu workbook mà không làm thay đổi các metadata khác.

### Bước 5: Kiểm toán Chất lượng (Quality Audit)
1. Quét tự động toàn bộ cột Tiếng Việt:
   - Đếm số lượng ô đã dịch.
   - Kiểm tra xem còn ký tự ngôn ngữ gốc (ví dụ chữ Hán `[\u4e00-\u9fff]`) bị sót hay không.
2. Trích xuất mẫu đối chiếu song ngữ ngẫu nhiên ở các Sheet để kiểm tra tính tự nhiên và chuẩn xác của thuật ngữ.
3. Xuất báo cáo kiểm toán cho người dùng.

---

# Examples — Thuật ngữ Kỹ thuật Mẫu Chuẩn

## 1. Hạng mục Kết cấu & Xây dựng (Civil & Architecture)
| Ngôn ngữ gốc (Trung) | Tiếng Việt chuẩn Kỹ sư Dự án / BOQ |
| :--- | :--- |
| 预应力混凝土离心桩PHC-500A | Cọc ống bê tông ly tâm ứng lực trước PHC-500A |
| 机械平整场地±30cm以内 | San gạt mặt bằng bằng cơ giới trong phạm vi ±30cm |
| C30商品混凝土独立基础，W10抗渗 | Móng đơn bê tông thương phẩm C30, cấp chống thấm W10 |
| 3厚SBS弹性体改性沥青防水卷材 | Màng chống thấm bitum biến tính đàn hồi SBS dày 3mm |
| 聚合物水泥防水涂料‖型 | Sơn chống thấm xi măng polymer loại II |
| 蒸压加气混凝土砌块 (AAC) | Gạch bê tông khí chưng áp (AAC) |
| 细石混凝土找坡层(坡向排水沟),随打随抹平 | Lớp bê tông đá mi tạo dốc (dốc về rãnh thoát nước), đổ đến đâu xoa phẳng đến đó |
| 钢支撑、钢拉条、系杆、隅撑 | Hệ giằng thép, ti giằng (thanh kéo), thanh chống dọc, ke xà gồ (thanh chống góc) |

## 2. Hạng mục Cơ điện MEPF (Mechanical, Electrical, Plumbing, Firefighting)
| Ngôn ngữ gốc (Trung) | Tiếng Việt chuẩn Kỹ sư Dự án / BOQ |
| :--- | :--- |
| 消防动力配电箱 | Tủ phân phối nguồn động lực PCCC |
| 成套总配电箱 | Tủ phân phối điện tổng đồng bộ |
| 柔性矿物绝缘电缆 FR-XH | Cáp chống cháy cách điện khoáng mềm FR-XH |
| 电缆桥架（中间加隔板） | Máng cáp / Thang máng cáp (có vách ngăn ở giữa) |
| 螺纹连接螺翼式水表 | Đồng hồ nước dạng cánh quạt xoắn nối ren |
| 湿式报警阀组 | Cụm van báo động ướt (Wet Alarm Valve Set) |
| 信号蝶阀 / 止回阀 / 减压阀 | Van bướm tín hiệu / Van một chiều / Van giảm áp |
| 多联机室内机 (VRV/VRF) | Dàn lạnh điều hòa trung tâm (VRV/VRF) |
| 轴流式消防补风风机 | Quạt cấp gió bù PCCC dạng hướng trục |
| 镀锌钢板排烟风管 | Ống gió hút khói bằng tôn tráng kẽm |

---

# Constraints (Rào chắn An toàn)

- 🚫 **TUYỆT ĐỐI KHÔNG** dịch máy thô từng từ hoặc làm mất các ký hiệu mã hiệu kỹ thuật (`DN`, `PN`, `kW`, `m3/h`, `C30`, `MU20`...).
- 🚫 **TUYỆT ĐỐI KHÔNG** ghi đè làm mất cột ngôn ngữ gốc (giữ cột gốc nguyên bản 100% để phục vụ đối chiếu và cho phép người dùng ẩn/xóa cột dịch bất kỳ lúc nào).
- 🚫 **TUYỆT ĐỐI KHÔNG** can thiệp hoặc làm lỗi công thức tính toán (`=` trong Excel).
- ✅ **LUÔN LUÔN** chạy bước Kiểm toán chất lượng (Audit) trước khi bàn giao file cho người dùng để đảm bảo 0 lỗi ký tự sót lại.

<!-- Generated by Skill Creator Ultra v1.0 -->
