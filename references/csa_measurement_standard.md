# Chuẩn đo bóc CSA dùng chung

Áp dụng cho `csa-quantity-takeoff` và toàn bộ agent trong `csa-takeoff-suite`. Đọc tài liệu này trước khi đo bóc, kiểm tra hoặc phát hành BOQ.

## 1. Nguồn, revision và thứ tự ưu tiên

Áp dụng theo thứ tự: **hợp đồng/phương pháp đo bóc được chấp thuận → specification → bản vẽ revision mới nhất → biện pháp được duyệt → quy tắc mặc định trong tài liệu này**. Nếu nguồn mâu thuẫn hoặc thiếu dữ liệu, không suy diễn: tạo RFI và ghi trạng thái dữ liệu phù hợp.

`csa-orchestrator` phải nhận **Document Register** đầu vào, tối thiểu theo dạng `{"S-101": "Rev.03"}`. Đây là metadata đầu vào, không phải sheet thứ năm. Mỗi dòng `Takeoff_Calculation` chỉ dùng một bản vẽ/revision theo dạng `S-101 Rev.03`; thiếu Document Register, không có bản vẽ trong register, hoặc revision không mới nhất đều chặn phát hành.

Bảng Schedule chỉ là nguồn đối chiếu; không thay thế kích thước hình học hoặc số đếm định vị độc lập.

## 2. BOQ, phép tính và trạng thái

- BOQ chính thức luôn 5 cột A–E và một dòng cho một item. Cột D chỉ chứa **net design quantity** theo hình học.
- Mọi BOQ item có khối lượng phải có ít nhất một `Calc ID`; đây là chính sách thống nhất cho cả item đơn giản và phức tạp. Một `Calc ID` có thể gồm nhiều dòng tính chi tiết, nhưng chỉ được liên kết với một WBS BOQ.
- Cột E là kiểm tra nhanh, dùng mẫu máy kiểm được: `Location=<vị trí/cấu kiện>; Geometry=<kích thước/số đếm>; Deductions=<khấu trừ/cơ sở>; Calc ID=<CAL-...>`. Bên ráp đơn giá có thể ẩn cột này mà không thay đổi dữ liệu BOQ.
- `Takeoff_Calculation` giữ đủ 12 trường: Calc ID, WBS, vị trí/cấu kiện, bản vẽ/revision, nguồn hình vẽ, công thức, khấu trừ/cơ sở đo, ĐVT, khối lượng, trạng thái dữ liệu, người kiểm tra, ghi chú.
- Khi có dữ liệu Calculation, `csa_excel_styler.py` tự thêm hộp `CHÚ GIẢI NHÃN KIỂM SOÁT` dưới bảng. Hộp này giải thích bằng tiếng Việt các mã `NET_DESIGN`, `PROCUREMENT_ONLY` và trạng thái đất; không phải dòng phép tính và không tham gia đối soát.
- Chỉ `Verified` và `Quantity Class=NET_DESIGN` được tổng hợp vào BOQ. Các trạng thái dữ liệu hợp lệ là `Verified`, `Draft`, `Assumption`, `RFI Required`, `Open`.
- Cột `Ghi chú` của mọi dòng Calculation bắt buộc có `Quantity Class=NET_DESIGN` hoặc `Quantity Class=PROCUREMENT_ONLY`. Hao hụt cắt uốn, đặt hàng, vận chuyển hoặc thi công là `PROCUREMENT_ONLY`; không cộng vào BOQ.D.
- Trước phát hành, BOQ và Calculation phải khớp **WBS, ĐVT và tổng khối lượng** trong dung sai làm tròn `0.005`. Mọi Calc ID liên kết phải tồn tại và là `Verified`.

## 3. Bê tông, ván khuôn, thép và lỗ mở

- Với từng cấu kiện BTCT, đánh giá độc lập bê tông, ván khuôn và thép. Không dùng quy tắc “bộ ba” như điều kiện tuyệt đối.
- Ván khuôn chỉ tính cho mặt thực sự cần coffa theo biện pháp và hợp đồng. Không mặc định tính mặt đổ trực tiếp trên đất, lớp lót hoặc bề mặt đã thay coffa nếu không có yêu cầu khác.
- Thép gồm thanh, nối chồng, neo, phụ kiện cấu tạo khi có thể hiện/chỉ dẫn; lượng hao hụt cắt uốn để riêng `PROCUREMENT_ONLY`.
- Các ngưỡng “không trừ lỗ mở” là mặc định có điều kiện, chỉ dùng khi hợp đồng/spec/phương pháp đo bóc hoặc ghi chú bản vẽ cho phép. Nếu không, đo theo hình học thực tế và ghi rõ cơ sở.

- Kết cấu thép thứ cấp & xà gồ (Purlins, Girts, Cleats): Phải trích xuất đủ 4 nguồn dữ liệu văn bản CAD (TEXT, DIMENSION.text, BLOCK ATTRIBUTES, LEADER) và khoanh vùng độc lập từng mặt bằng. Bắt buộc đếm số hàng xà gồ vẽ thực tế trong CAD Block, cấm chia nhịp ước lượng ( / \text{spacing} + 1$). Phân biệt rõ tiết diện Z-profile (xà gồ mái có nối chồng lapsplice) vs C-profile (xà gồ vách Horizontal Girt/Canopy). Số lượng gối đỡ và bu lông nở phải khớp {\text{gối}} = N_{\text{hàng xà gồ}} \times N_{\text{khung dầm đỡ}}$.\n
## 4. Đất và Earthwork_Balance

Tách ít nhất các trạng thái: `IN_SITU_EXCAVATION`, `LOOSE_HAUL`, `COMPACTED_FILL`, `REUSE`, `IMPORTED`, `DISPOSAL`. Hệ số chuyển đổi, taluy, không gian thao tác, shoring, hạ nước, tuyến vận chuyển hoặc tally chỉ dùng khi hồ sơ/phương pháp được duyệt nêu rõ.

Một dòng Calculation thuộc công tác đất phải thêm `EARTHWORK_STATE=<trạng thái>` trong `Ghi chú`. Khi có bất kỳ dòng đất nào, orchestrator tạo bảng phụ Excel Table tên `Earthwork_Balance` tại cột N:X của `Takeoff_Calculation`, không thêm sheet thứ năm. Mỗi dòng cân bằng ghi WBS/khu vực, revision, Calc ID nguồn, ĐVT `m3`, sáu trạng thái thể tích và cơ sở cân bằng. Mỗi Calc ID đất phải có đúng một dòng cân bằng và giá trị trạng thái phải khớp lượng nguồn.

## 5. RFI, QA và phát hành

RFI dùng đúng 8 trường và không được để trống trường nào. Cột H bắt buộc theo mẫu `Owner=<tên>; Status=<trạng thái>; Due=YYYY-MM-DD`. Trạng thái RFI hợp lệ: `Open`, `Pending`, `RFI Required`, `Resolved`, `Closed`, `Cancelled`. Chỉ `Resolved`, `Closed` hoặc `Cancelled` mới cho phép phát hành; rỗng, sai mẫu hoặc mọi trạng thái khác đều chặn.

QA ghi đủ 9 trường vào `QA_Audit`, với trạng thái `Pass`, `Open`, `Resolved`, `RFI Required` và ngày ISO `YYYY-MM-DD`. Trạng thái hiệu lực là dòng mới nhất theo ngày, rồi theo dòng, của từng cặp Gate/đối tượng. Bất kỳ trạng thái hiệu lực `Open` hoặc `RFI Required` nào đều chặn phát hành; mỗi Gate 0–4 phải còn ít nhất một `Pass` hiệu lực.

Gate 0 kiểm tra bốn sheet bắt buộc, header/độ rộng cột, Arial, fill, font size/bold/màu, border, alignment, number format, wrap text, gridline tắt và data row đã AutoFit tối thiểu 28pt. Gate 1–4 kiểm tra truy vết/đơn vị, hợp lý, đo độc lập và đồng bộ liên bộ môn.

## 6. Ranh giới agent

Agent chuyên ngành chỉ bàn giao WBS, Calc ID, vị trí/cấu kiện, bản vẽ/revision, nguồn hình vẽ, công thức, khấu trừ/cơ sở đo, ĐVT, khối lượng, trạng thái dữ liệu, `Quantity Class` và khi phù hợp `EARTHWORK_STATE`. Không tự tạo `.xlsx` phát hành.

`csa-qaqc-audit` chỉ ghi kết quả vào `QA_Audit`, không tạo BOQ cạnh tranh. Chỉ `csa-orchestrator` được tạo và phát hành workbook chính thức qua `save_and_validate_csa_workbook(workbook, file_path, document_register=...)`.

### Quy tắc bắt buộc khi xuất Excel

Không tạo hoặc chạy một file Python mới để tự tạo, định dạng, lưu hoặc AutoFit workbook BOQ. Luồng phát hành duy nhất phải import `csa_excel_styler.py`, gọi `create_csa_workbook()` để khởi tạo và gọi `save_and_validate_csa_workbook(...)` để lưu.

Ngoài `csa_excel_styler.py`, cấm dùng trực tiếp `openpyxl.Workbook()`, `wb.create_sheet()`, `wb.save()` hoặc `autofit_workbook_rows()` cho BOQ phát hành. Nếu có script hỗ trợ trích xuất dữ liệu, nó chỉ được trả dữ liệu đo bóc; không được tạo hoặc ghi `.xlsx`.
