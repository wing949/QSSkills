from pathlib import Path
import sys

from openpyxl import load_workbook
import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import csa_excel_styler as styler


def _document_register():
    """Nguồn revision chính thức được đưa từ orchestrator, không nằm trong workbook."""
    return {"S-101": "Rev.03", "A-201": "Rev.02"}


def _release_ready_workbook():
    """Tạo hồ sơ tối thiểu đã đủ 5 Gate để test từng điều kiện phát hành."""
    workbook, boq, calculation, rfi, qa = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)
    styler.add_boq_item(
        boq,
        6,
        "A.01.01",
        "Bê tông móng / Foundation concrete / 基础混凝土",
        "m3",
        2.00,
        "Location=Móng F1; Geometry=2.00 x 2.00 x 0.50; "
        "Deductions=Không; Calc ID=CAL-STR-001",
    )
    styler.add_takeoff_calculation_item(
        calculation,
        6,
        "CAL-STR-001",
        "A.01.01",
        "Móng F1 / trục 1-A",
        "S-101 Rev.03",
        "Mặt cắt 3/S-101",
        "2.00 x 2.00 x 0.50",
        "Không khấu trừ; theo phương pháp đo bóc HĐ",
        "m3",
        2.00,
        "Verified",
        "QS Nguyen",
        "Quantity Class=NET_DESIGN",
    )
    for row, gate in enumerate(range(5), 6):
        styler.add_qa_audit_item(
            qa,
            row,
            f"Gate {gate}",
            "Kiểm tra mẫu",
            "CSA sample",
            "Info",
            "Đủ bằng chứng",
            "Không yêu cầu hành động",
            "QA Lead",
            "Pass",
            "2026-09-23",
        )
    styler.finalize_workbook_layout(workbook)
    return workbook, boq, calculation, rfi, qa


def _validate_ready_workbook(workbook):
    """Gọi validator với Document Register do orchestrator cung cấp."""
    styler.finalize_workbook_layout(workbook)
    return styler.validate_release_readiness(
        workbook, document_register=_document_register()
    )


def test_boq_level_one_section_does_not_repeat_a_part_number_in_its_title():
    """A title already beginning with PHẦN II must not become `II. PHẦN II`."""
    _, boq, _, _, _ = styler.create_csa_workbook()

    styler.add_boq_section_level1(
        boq,
        6,
        "II",
        "PHẦN II: KẾT CẤU & HOÀN THIỆN / PART II: ARCHITECTURAL & FINISHING WORKS",
    )

    assert boq["A6"].value == (
        "PHẦN II: KẾT CẤU & HOÀN THIỆN / PART II: ARCHITECTURAL & FINISHING WORKS"
    )


def test_release_blocks_pending_rfi_with_a_structured_status():
    """Thay đổi để Pending có thể phát hành phải làm test này thất bại."""
    workbook, _, _, rfi, _ = _release_ready_workbook()
    styler.add_rfi_item(
        rfi,
        6,
        "RFI-001",
        "A.01.01",
        "Móng F1 / S-101 Rev.03",
        "m3 / 2.00",
        "2.00 x 2.00 x 0.50",
        "Xác nhận cấp phối",
        "Chưa đưa vào BOQ",
        "Owner=Lead QS; Status=Pending; Due=2026-10-01",
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("Pending" in error for error in result.errors)


def test_release_blocks_an_incomplete_rfi_even_when_its_status_is_resolved():
    """RFI đóng trạng thái nhưng thiếu nội dung vẫn không đủ căn cứ phát hành."""
    workbook, _, _, rfi, _ = _release_ready_workbook()
    styler.add_rfi_item(
        rfi,
        6,
        "RFI-002",
        "A.01.01",
        "Móng F1 / S-101 Rev.03",
        "m3 / 2.00",
        "2.00 x 2.00 x 0.50",
        None,
        "Không ảnh hưởng sau khi xác nhận",
        "Owner=Lead QS; Status=Resolved; Due=2026-10-01",
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any(error.startswith("RFI") for error in result.errors)


def test_release_blocks_an_open_gate_even_when_that_gate_also_has_passed_rows():
    """Thay đổi bỏ qua Open khi Gate đã Pass phải làm test này thất bại."""
    workbook, _, _, _, qa = _release_ready_workbook()
    styler.add_qa_audit_item(
        qa,
        11,
        "Gate 1",
        "Đối soát đơn vị",
        "A.01.01",
        "High",
        "ĐVT m2/m3 chưa thống nhất",
        "Sửa đơn vị",
        "QA Lead",
        "Open",
        "2026-09-24",
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("Gate 1" in error and "Open" in error for error in result.errors)


def test_release_blocks_an_incomplete_qa_audit_row_even_when_gate_is_pass():
    """Không được coi một Gate Pass là hợp lệ khi thiếu bằng chứng hoặc người phụ trách."""
    workbook, _, _, _, qa = _release_ready_workbook()
    styler.add_qa_audit_item(
        qa,
        11,
        "Gate 3",
        "Kiểm tra mẫu",
        "A.01.01",
        "Info",
        None,
        "Không yêu cầu hành động",
        "",
        "Pass",
        "2026-09-24",
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any(error.startswith("QA_Audit") for error in result.errors)


def test_release_blocks_boq_quantity_that_does_not_match_verified_calculations():
    """Thay đổi không còn đối soát tổng BOQ.D phải làm test này thất bại."""
    workbook, boq, calculation, _, _ = _release_ready_workbook()
    boq.cell(6, 4).value = 3.00
    calculation.cell(6, 9).value = 2.00

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("không khớp tổng khối lượng" in error for error in result.errors)


def test_release_blocks_calculation_with_a_wbs_or_unit_different_from_boq():
    """Thay đổi bỏ liên kết WBS/ĐVT phải làm test này thất bại."""
    workbook, _, calculation, _, _ = _release_ready_workbook()
    calculation.cell(6, 2).value = "A.99.99"
    calculation.cell(6, 8).value = "m2"

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("WBS" in error for error in result.errors)
    assert any("ĐVT" in error for error in result.errors)


def test_release_requires_a_document_register_and_the_current_revision():
    """Thay đổi cho phép revision không có nguồn chính thức phải làm test này thất bại."""
    workbook, _, _, _, _ = _release_ready_workbook()

    result = styler.validate_release_readiness(workbook)

    assert result.passed is False
    assert any("Document Register" in error for error in result.errors)


def test_release_blocks_procurement_only_calculation_linked_to_boq():
    """Thay đổi cộng PROCUREMENT_ONLY vào BOQ.D phải làm test này thất bại."""
    workbook, boq, calculation, _, _ = _release_ready_workbook()
    calculation.cell(6, 12).value = "Quantity Class=PROCUREMENT_ONLY"
    boq.cell(6, 5).value = (
        "Location=Móng F1; Geometry=2.00 x 2.00 x 0.50; "
        "Deductions=Không; Calc ID=CAL-STR-001"
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("PROCUREMENT_ONLY" in error for error in result.errors)


def test_release_blocks_earthwork_calculation_without_an_earthwork_balance_row():
    """Thay đổi cho phép đất có trạng thái nhưng thiếu bảng cân bằng phải làm test này thất bại."""
    workbook, _, calculation, _, _ = _release_ready_workbook()
    calculation.cell(6, 12).value = (
        "Quantity Class=NET_DESIGN; EARTHWORK_STATE=IN_SITU_EXCAVATION"
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("Earthwork_Balance" in error for error in result.errors)


def test_gate_zero_rejects_tampered_header_and_data_presentation():
    """Thay đổi không kiểm tra fill, border, alignment, format hoặc italic phải làm test này thất bại."""
    workbook, boq, _, _, _ = _release_ready_workbook()
    boq["A5"].fill = styler.PatternFill(fill_type=None)
    boq["A5"].border = styler.Border()
    boq["A5"].alignment = styler.Alignment(horizontal="left")
    boq["D6"].number_format = "General"
    boq["E6"].font = styler.FONT_ITEM_DESC

    errors = styler._validate_gate_zero_layout(workbook)

    assert any("fill" in error.lower() for error in errors)
    assert any("border" in error.lower() for error in errors)
    assert any("alignment" in error.lower() for error in errors)
    assert any("number format" in error.lower() for error in errors)
    assert any("italic" in error.lower() for error in errors)


def test_release_blocks_a_stale_revision_against_the_document_register():
    """Thay đổi chỉ kiểm tra revision có tồn tại phải làm test này thất bại."""
    workbook, _, calculation, _, _ = _release_ready_workbook()
    calculation.cell(6, 4).value = "S-101 Rev.02"

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("revision mới nhất" in error.lower() for error in result.errors)


def test_release_rejects_unknown_qa_status():
    """Thay đổi cho phép trạng thái QA ngoài enum phải làm test này thất bại."""
    workbook, _, _, _, qa = _release_ready_workbook()
    styler.add_qa_audit_item(
        qa,
        11,
        "Gate 2",
        "Kiểm tra benchmark",
        "A.01.01",
        "Info",
        "Không rõ trạng thái",
        "Cập nhật trạng thái chuẩn",
        "QA Lead",
        "Pending",
        "2026-09-24",
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("trạng thái không hợp lệ" in error.lower() for error in result.errors)


def test_release_requires_the_structured_boq_formula_summary_fields():
    """Thay đổi chấp nhận cột E thiếu location hoặc deductions phải làm test này thất bại."""
    workbook, boq, _, _, _ = _release_ready_workbook()
    boq.cell(6, 5).value = "2.00 x 2.00 x 0.50 = 2.00 m3 | Calc ID: CAL-STR-001"

    result = _validate_ready_workbook(workbook)

    assert result.passed is False
    assert any("Location" in error for error in result.errors)
    assert any("Deductions" in error for error in result.errors)


def test_release_accepts_multiple_verified_calculation_rows_for_one_boq_item():
    """Thay đổi không cộng nhiều dòng Calc ID cho một BOQ item phải làm test này thất bại."""
    workbook, boq, calculation, _, _ = _release_ready_workbook()
    boq.cell(6, 4).value = 5.00
    boq.cell(6, 5).value = (
        "Location=Móng F1; Geometry=(2.00 + 3.00) m3; Deductions=Không; "
        "Calc ID=CAL-STR-001"
    )
    calculation.cell(6, 9).value = 2.00
    styler.add_takeoff_calculation_item(
        calculation,
        7,
        "CAL-STR-001",
        "A.01.01",
        "Móng F2 / trục 1-B",
        "S-101 Rev.03",
        "Mặt cắt 4/S-101",
        "3.00 x 1.00 x 1.00",
        "Không khấu trừ; theo phương pháp đo bóc HĐ",
        "m3",
        3.00,
        "Verified",
        "QS Nguyen",
        "Quantity Class=NET_DESIGN",
    )
    styler.finalize_workbook_layout(workbook)

    result = _validate_ready_workbook(workbook)

    assert result.passed is True


def test_release_accepts_a_resolved_rfi_with_all_required_tokens():
    """Thay đổi chặn cả RFI Resolved phải làm test này thất bại."""
    workbook, _, _, rfi, _ = _release_ready_workbook()
    styler.add_rfi_item(
        rfi,
        6,
        "RFI-001",
        "A.01.01",
        "Móng F1 / S-101 Rev.03",
        "m3 / 2.00",
        "2.00 x 2.00 x 0.50",
        "Xác nhận cấp phối",
        "Không ảnh hưởng sau khi xác nhận",
        "Owner=Lead QS; Status=Resolved; Due=2026-10-01",
    )

    result = _validate_ready_workbook(workbook)

    assert result.passed is True


def test_release_accepts_earthwork_when_every_tagged_calc_id_is_in_the_balance():
    """Thay đổi không tạo hoặc không đọc Earthwork_Balance phải làm test này thất bại."""
    workbook, _, calculation, _, _ = _release_ready_workbook()
    calculation.cell(6, 12).value = (
        "Quantity Class=NET_DESIGN; EARTHWORK_STATE=IN_SITU_EXCAVATION"
    )
    styler.add_earthwork_balance_item(
        calculation,
        6,
        "A.01.01 / Hố móng F1",
        "S-101 Rev.03",
        "CAL-STR-001",
        "m3",
        2.00,
        0.00,
        0.00,
        0.00,
        0.00,
        0.00,
        "Theo hệ số và tuyến vận chuyển được duyệt",
    )
    styler.finalize_workbook_layout(workbook)

    result = _validate_ready_workbook(workbook)

    assert result.passed is True
    assert "Earthwork_Balance" in calculation.tables


def test_takeoff_legend_explains_control_codes_without_becoming_calculation_data():
    """Bỏ vùng loại trừ chú giải sẽ làm validator hiểu nhầm chú giải là phép tính."""
    workbook, _, calculation, _, _ = _release_ready_workbook()

    legend_start_row = styler.add_takeoff_calculation_legend(calculation)
    styler.finalize_workbook_layout(workbook)

    assert calculation.cell(legend_start_row, 1).value == "CHÚ GIẢI NHÃN KIỂM SOÁT"
    assert calculation.cell(legend_start_row + 2, 1).value == "NET_DESIGN"
    assert "được phép tổng hợp vào BOQ" in calculation.cell(
        legend_start_row + 2, 2
    ).value
    assert list(styler._data_rows(calculation)) == [6]

    result = styler.validate_release_readiness(
        workbook, document_register=_document_register()
    )

    assert result.passed is True


def test_finalization_adds_the_takeoff_legend_below_calculation_items():
    """Bỏ lệnh tạo chú giải khi finalize sẽ làm workbook phát hành thiếu phần giải thích."""
    workbook, _, calculation, _, _ = styler.create_csa_workbook()
    styler.setup_takeoff_calculation_headers(calculation)
    styler.add_takeoff_calculation_item(
        calculation,
        6,
        "CAL-STR-001",
        "A.01.01",
        "Móng F1 / trục 1-A",
        "S-101 Rev.03",
        "Mặt cắt 3/S-101",
        "2.00 x 2.00 x 0.50",
        "Không khấu trừ; theo phương pháp đo bóc HĐ",
        "m3",
        2.00,
        "Verified",
        "QS Nguyen",
        "Quantity Class=NET_DESIGN",
    )

    styler.finalize_workbook_layout(workbook)

    assert calculation.cell(9, 1).value == "CHÚ GIẢI NHÃN KIỂM SOÁT"
    assert list(styler._data_rows(calculation)) == [6]


def test_create_workbook_has_the_four_controlled_sheets():
    """Workbook phát hành phải chứa BOQ, phép tính, RFI và nhật ký QA."""
    workbook, *_ = styler.create_csa_workbook()

    assert workbook.sheetnames == [
        "BOQ",
        "Takeoff_Calculation",
        "RFI_Kien_Nghi_Bo_Sung",
        "QA_Audit",
    ]


def test_supporting_sheets_expose_the_agreed_traceability_schema():
    """Calculation, RFI và QA phải giữ đúng dữ liệu cần cho truy vết."""
    workbook, _, calculation, rfi, qa = styler.create_csa_workbook()

    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)

    assert [calculation.cell(5, column).value for column in range(1, 13)] == [
        "CALC ID\n(Calculation ID)",
        "MÃ WBS BOQ\n(BOQ WBS)",
        "VỊ TRÍ / CẤU KIỆN\n(Location / Element)",
        "BẢN VẼ & REVISION\n(Drawing & Revision)",
        "MẶT BẰNG / MẶT CẮT / CHI TIẾT\n(Source View / Detail)",
        "CÔNG THỨC KÍCH THƯỚC\n(Measurement Formula)",
        "KHẤU TRỪ & CƠ SỞ ĐO\n(Deductions & Measurement Basis)",
        "ĐƠN VỊ\n(Unit)",
        "KHỐI LƯỢNG\n(Quantity)",
        "TRẠNG THÁI DỮ LIỆU\n(Data Status)",
        "NGƯỜI KIỂM TRA\n(Checker)",
        "GHI CHÚ\n(Remarks)",
    ]
    assert [rfi.cell(5, column).value for column in range(1, 9)] == [
        "MÃ RFI\n(RFI No.)",
        "MÃ WBS / HẠNG MỤC\n(WBS / Trade)",
        "VỊ TRÍ – BẢN VẼ – REVISION\n(Location – Drawing – Revision)",
        "ĐVT & KHỐI LƯỢNG DỰ TRÙ\n(Unit & Provisional Quantity)",
        "CÔNG THỨC TẠM TÍNH\n(Provisional Formula)",
        "CƠ SỞ KỸ THUẬT & CÂU HỎI\n(Technical Basis & Query)",
        "TÁC ĐỘNG CHI PHÍ / TIẾN ĐỘ\n(Cost / Schedule Impact)",
        "NGƯỜI PHỤ TRÁCH – TRẠNG THÁI – HẠN\n(Owner – Status – Due Date)",
    ]
    assert [qa.cell(5, column).value for column in range(1, 10)] == [
        "CỔNG\n(Gate)",
        "QUY TẮC KIỂM TRA\n(Check Rule)",
        "ĐỐI TƯỢNG\n(Target)",
        "MỨC ĐỘ\n(Severity)",
        "BẰNG CHỨNG\n(Evidence)",
        "HÀNH ĐỘNG YÊU CẦU\n(Required Action)",
        "NGƯỜI PHỤ TRÁCH\n(Owner)",
        "TRẠNG THÁI\n(Status)",
        "NGÀY KIỂM TRA\n(Audit Date)",
    ]


def test_calculation_row_links_a_boq_item_to_its_checked_source():
    """Chi tiết phép tính phải giữ Calc ID, nguồn bản vẽ và trạng thái dữ liệu."""
    _, _, calculation, _, _ = styler.create_csa_workbook()

    styler.add_takeoff_calculation_item(
        calculation,
        6,
        "CAL-STR-001",
        "A.01.01",
        "Móng F1 / trục 1-A",
        "S-101 Rev.03",
        "Mặt cắt 3/S-101",
        "2.00 x 2.00 x 0.50",
        "Không khấu trừ; theo phương pháp đo bóc HĐ",
        "m3",
        2.00,
        "Verified",
        "QS Nguyen",
        "Khối lượng thiết kế thuần",
    )

    assert [calculation.cell(6, column).value for column in range(1, 13)] == [
        "CAL-STR-001",
        "A.01.01",
        "Móng F1 / trục 1-A",
        "S-101 Rev.03",
        "Mặt cắt 3/S-101",
        "2.00 x 2.00 x 0.50",
        "Không khấu trừ; theo phương pháp đo bóc HĐ",
        "m3",
        2.00,
        "Verified",
        "QS Nguyen",
        "Khối lượng thiết kế thuần",
    ]
    assert calculation.cell(6, 6).font.italic is True
    assert calculation.cell(6, 9).font.bold is True


def test_rfi_row_keeps_provisional_quantity_and_formula_in_their_own_columns():
    """RFI phải lưu được lượng dự trù và công thức thay vì ghi đè bằng đề xuất xử lý."""
    _, _, _, rfi, _ = styler.create_csa_workbook()

    styler.add_rfi_item(
        rfi,
        6,
        "RFI-001",
        "B.02 / Chống thấm",
        "WC-01 / A-201 Rev.02",
        "m2 / 8.40",
        "3.00 x 2.20 + 10.00 x 0.30",
        "Thiếu chi tiết vén chân tường; đề nghị xác nhận cao độ",
        "Chờ xác nhận; chưa đưa vào BOQ",
        "Lead QS / Open / 2026-10-01",
    )

    assert [rfi.cell(6, column).value for column in range(1, 9)] == [
        "RFI-001",
        "B.02 / Chống thấm",
        "WC-01 / A-201 Rev.02",
        "m2 / 8.40",
        "3.00 x 2.20 + 10.00 x 0.30",
        "Thiếu chi tiết vén chân tường; đề nghị xác nhận cao độ",
        "Chờ xác nhận; chưa đưa vào BOQ",
        "Lead QS / Open / 2026-10-01",
    ]
    assert rfi.cell(6, 5).font.italic is True


def test_qa_audit_row_records_gate_evidence_and_resolution_status():
    """QA phải có nhật ký rõ cổng kiểm tra, bằng chứng và trạng thái xử lý."""
    _, _, _, _, qa = styler.create_csa_workbook()

    styler.add_qa_audit_item(
        qa,
        6,
        "Gate 3",
        "Đối chiếu 3 chiều",
        "A.01.01 / CAL-STR-001",
        "High",
        "S-101 Rev.03 khớp công thức CAL-STR-001",
        "Không yêu cầu hành động",
        "QA Lead",
        "Pass",
        "2026-09-23",
    )

    assert [qa.cell(6, column).value for column in range(1, 10)] == [
        "Gate 3",
        "Đối chiếu 3 chiều",
        "A.01.01 / CAL-STR-001",
        "High",
        "S-101 Rev.03 khớp công thức CAL-STR-001",
        "Không yêu cầu hành động",
        "QA Lead",
        "Pass",
        "2026-09-23",
    ]
    assert qa.cell(6, 8).font.bold is True


def test_save_and_validate_applies_layout_and_releases_a_verified_workbook(tmp_path):
    """Hàm phát hành phải tự chuẩn hóa layout và chỉ phát hành khi đủ 5 Gate Pass."""
    workbook, boq, calculation, rfi, qa = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)
    styler.add_boq_item(
        boq,
        6,
        "A.01.01",
        "Bê tông móng / Foundation concrete / 基础混凝土",
        "m3",
        2.00,
        "Location=Móng F1; Geometry=2.00 x 2.00 x 0.50; "
        "Deductions=Không; Calc ID=CAL-STR-001",
    )
    styler.add_takeoff_calculation_item(
        calculation,
        6,
        "CAL-STR-001",
        "A.01.01",
        "Móng F1 / trục 1-A",
        "S-101 Rev.03",
        "Mặt cắt 3/S-101",
        "2.00 x 2.00 x 0.50",
        "Không khấu trừ; theo phương pháp đo bóc HĐ",
        "m3",
        2.00,
        "Verified",
        "QS Nguyen",
        "Quantity Class=NET_DESIGN",
    )
    for row, gate in enumerate(range(5), 6):
        styler.add_qa_audit_item(
            qa,
            row,
            f"Gate {gate}",
            "Kiểm tra mẫu",
            "A.01.01",
            "Info",
            "Đạt",
            "Không yêu cầu hành động",
            "QA Lead",
            "Pass",
            "2026-09-23",
        )

    output_path = tmp_path / "boq_verified.xlsx"
    result = styler.save_and_validate_csa_workbook(
        workbook, output_path, document_register=_document_register()
    )

    assert result.passed is True
    assert result.errors == ()
    saved = load_workbook(output_path)
    assert saved["BOQ"].column_dimensions["B"].width == 65.0
    assert saved["Takeoff_Calculation"].column_dimensions["F"].width == 55.0
    assert saved["RFI_Kien_Nghi_Bo_Sung"].column_dimensions["H"].width == 32.0
    assert saved["QA_Audit"].views.sheetView[0].showGridLines is False


def test_save_and_validate_blocks_a_schedule_only_takeoff(tmp_path):
    """Không được phát hành khi BOQ chỉ dẫn Schedule mà thiếu hình học độc lập."""
    workbook, boq, calculation, rfi, qa = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)
    styler.add_boq_item(
        boq,
        6,
        "B.01.01",
        "Cửa nhôm kính / Aluminum window / 铝合金窗",
        "bộ",
        4,
        "Theo Schedule cửa D-01 | Calc ID: CAL-ARC-001",
    )
    styler.add_takeoff_calculation_item(
        calculation,
        6,
        "CAL-ARC-001",
        "B.01.01",
        "Tầng 1",
        "A-201 Rev.02",
        "Mặt bằng tầng 1",
        "Theo Schedule cửa D-01",
        "Không có khấu trừ",
        "bộ",
        4,
        "Verified",
        "QS Nguyen",
        "",
    )
    for row, gate in enumerate(range(5), 6):
        styler.add_qa_audit_item(
            qa,
            row,
            f"Gate {gate}",
            "Kiểm tra mẫu",
            "B.01.01",
            "Info",
            "Đạt",
            "Không yêu cầu hành động",
            "QA Lead",
            "Pass",
            "2026-09-23",
        )

    with pytest.raises(ValueError, match="Theo Schedule"):
        styler.save_and_validate_csa_workbook(workbook, tmp_path / "boq_invalid.xlsx")


def test_save_and_validate_blocks_calculation_without_source_and_deduction_basis(tmp_path):
    """Truy vết chi tiết không được thiếu nguồn hình vẽ hoặc cơ sở khấu trừ."""
    workbook, boq, calculation, rfi, qa = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)
    styler.add_boq_item(
        boq, 6, "A.01.01", "Bê tông móng", "m3", 2.0,
        "Móng F1: 2.00 x 2.00 x 0.50 | Calc ID: CAL-STR-001",
    )
    styler.add_takeoff_calculation_item(
        calculation, 6, "CAL-STR-001", "A.01.01", "Móng F1", "S-101 Rev.03",
        "", "2.00 x 2.00 x 0.50", "", "m3", 2.0, "Verified", "QS Nguyen", "",
    )
    for row, gate in enumerate(range(5), 6):
        styler.add_qa_audit_item(
            qa, row, f"Gate {gate}", "Kiểm tra mẫu", "A.01.01", "Info", "Đạt",
            "Không yêu cầu hành động", "QA Lead", "Pass", "2026-09-23",
        )

    with pytest.raises(ValueError, match="Thiếu dữ liệu truy vết bắt buộc"):
        styler.save_and_validate_csa_workbook(workbook, tmp_path / "boq_missing_trace.xlsx")


def test_save_and_validate_blocks_boq_quantity_without_calc_id(tmp_path):
    """Khối lượng BOQ phải có Calc ID để chứng minh trạng thái Verified."""
    workbook, boq, calculation, rfi, qa = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)
    styler.add_boq_item(
        boq, 6, "A.01.01", "Bê tông móng", "m3", 2.0,
        "Móng F1: 2.00 x 2.00 x 0.50 = 2.00 m3",
    )
    for row, gate in enumerate(range(5), 6):
        styler.add_qa_audit_item(
            qa, row, f"Gate {gate}", "Kiểm tra mẫu", "A.01.01", "Info", "Đạt",
            "Không yêu cầu hành động", "QA Lead", "Pass", "2026-09-23",
        )

    with pytest.raises(ValueError, match="Thiếu Calc ID"):
        styler.save_and_validate_csa_workbook(workbook, tmp_path / "boq_missing_calc_id.xlsx")


def test_autofit_uses_the_safe_python_path_when_com_is_not_requested(tmp_path):
    """AutoFit phải chạy được không cần khởi động Excel COM trong phiên tự động."""
    workbook, boq, *_ = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.add_boq_item(
        boq,
        6,
        "A.01.01",
        "Mô tả ba ngôn ngữ đủ dài để kiểm tra AutoFit",
        "m3",
        1.0,
        "1.00 x 1.00 x 1.00 = 1.00 m3",
    )
    output_path = tmp_path / "autofit.xlsx"
    workbook.save(output_path)

    assert styler.autofit_workbook_rows(output_path, use_excel_com=False) is True


def test_autofit_expands_a_long_takeoff_calculation_formula(tmp_path):
    """AutoFit phải xét công thức ở cột F của Takeoff_Calculation."""
    workbook, _, calculation, _, _ = styler.create_csa_workbook()
    styler.setup_takeoff_calculation_headers(calculation)
    styler.add_takeoff_calculation_item(
        calculation,
        6,
        "CAL-STR-001",
        "A.01.01",
        "Móng F1 / trục 1-A",
        "S-101 Rev.03",
        "Mặt cắt 3/S-101",
        " + ".join(["2.00 x 2.00 x 0.50"] * 12),
        "Không khấu trừ; theo phương pháp đo bóc HĐ",
        "m3",
        24.0,
        "Verified",
        "QS Nguyen",
        "",
    )
    output_path = tmp_path / "calculation-autofit.xlsx"
    workbook.save(output_path)

    assert styler.autofit_workbook_rows(output_path, use_excel_com=False) is True
    saved = load_workbook(output_path)
    assert saved["Takeoff_Calculation"].row_dimensions[6].height > styler.MIN_DATA_ROW_HEIGHT


def test_sample_csa_package_reconciles_boq_calculation_rfi_and_qa(tmp_path):
    """Hồ sơ mẫu phải giữ một BOQ item/một dòng và truy vết đủ bốn sheet."""
    workbook, boq, calculation, rfi, qa = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)

    entries = [
        ("A.01.01", "Bê tông móng", "m3", 2.0, "Location=Móng F1; Geometry=2.00 x 2.00 x 0.50; Deductions=Không; Calc ID=CAL-STR-001", "CAL-STR-001", "Móng F1 / trục 1-A", "2.00 x 2.00 x 0.50", "Không khấu trừ; theo HĐ", "Quantity Class=NET_DESIGN"),
        ("A.02.01", "Ván khuôn canopy", "m2", 12.0, "Location=Canopy cửa chính; Geometry=3.00 x 4.00; Deductions=Không; Calc ID=CAL-STR-002", "CAL-STR-002", "Canopy cửa chính", "3.00 x 4.00", "Chỉ tính mặt dưới cần coffa", "Quantity Class=NET_DESIGN"),
        ("B.01.01", "Trát trần canopy", "m2", 12.0, "Location=Canopy cửa chính; Geometry=3.00 x 4.00; Deductions=Không; Calc ID=CAL-ARC-001", "CAL-ARC-001", "Canopy cửa chính", "3.00 x 4.00", "Kế thừa diện tích ván khuôn đáy", "Quantity Class=NET_DESIGN"),
        ("C.01.01", "Đào đất nguyên thổ", "m3", 18.0, "Location=Hố móng F1; Geometry=3.00 x 3.00 x 2.00; Deductions=Không; Calc ID=CAL-EAR-001", "CAL-EAR-001", "Hố móng F1", "3.00 x 3.00 x 2.00", "Nguyên thổ; chưa áp hệ số tơi", "Quantity Class=NET_DESIGN; EARTHWORK_STATE=IN_SITU_EXCAVATION"),
        ("C.01.02", "Đắp đất đã đầm", "m3", 10.0, "Location=Xung quanh móng F1; Geometry=5.00 x 2.00 x 1.00; Deductions=Không; Calc ID=CAL-EAR-002", "CAL-EAR-002", "Xung quanh móng F1", "5.00 x 2.00 x 1.00", "Thể tích đắp đã đầm theo HĐ", "Quantity Class=NET_DESIGN; EARTHWORK_STATE=COMPACTED_FILL"),
    ]
    for row_idx, entry in enumerate(entries, 6):
        wbs, description, unit, qty, summary, calc_id, location, formula, basis, remarks = entry
        styler.add_boq_item(boq, row_idx, wbs, description, unit, qty, summary)
        styler.add_takeoff_calculation_item(
            calculation, row_idx, calc_id, wbs, location, "S-101 Rev.03",
            "Mặt bằng và mặt cắt 3/S-101", formula, basis, unit, qty,
            "Verified", "QS Nguyen", remarks,
        )

    styler.add_earthwork_balance_item(
        calculation, 6, "C.01 / Hố móng F1", "S-101 Rev.03",
        "CAL-EAR-001, CAL-EAR-002", "m3", 18.0, 0.0, 10.0, 0.0, 0.0, 0.0,
        "Theo hệ số và tuyến vận chuyển được duyệt",
    )

    styler.add_rfi_item(
        rfi, 6, "RFI-001", "B.01.01", "Canopy / A-201 Rev.02", "m2 / 12.00",
        "3.00 x 4.00", "Xác nhận chi tiết lớp hoàn thiện canopy",
        "Không ảnh hưởng sau khi xác nhận", "Owner=Architect; Status=Resolved; Due=2026-09-30",
    )
    for row_idx, gate in enumerate(range(5), 6):
        styler.add_qa_audit_item(
            qa, row_idx, f"Gate {gate}", "Kiểm tra hồ sơ mẫu", "CSA sample", "Info",
            "Đủ bằng chứng", "Không yêu cầu hành động", "QA Lead", "Pass", "2026-09-23",
        )

    output_path = tmp_path / "csa-sample.xlsx"
    assert styler.save_and_validate_csa_workbook(
        workbook, output_path, document_register=_document_register()
    ).passed is True
    saved = load_workbook(output_path)
    assert saved["BOQ"].max_row == 10
    saved_calculation = saved["Takeoff_Calculation"]
    assert list(styler._data_rows(saved_calculation)) == [6, 7, 8, 9, 10]
    assert saved_calculation.cell(13, 1).value == "CHÚ GIẢI NHÃN KIỂM SOÁT"
    assert saved["RFI_Kien_Nghi_Bo_Sung"].cell(6, 4).value == "m2 / 12.00"
    assert saved["RFI_Kien_Nghi_Bo_Sung"].cell(6, 5).value == "3.00 x 4.00"
    assert {saved["QA_Audit"].cell(row, 1).value for row in range(6, 11)} == {
        "Gate 0", "Gate 1", "Gate 2", "Gate 3", "Gate 4",
    }


def test_save_and_validate_supports_hierarchical_subgates_and_wbs_scope(tmp_path):
    """Bảng QA_Audit hỗ trợ phân cấp các cổng con (Gate 2.1, 2.2, 3.1) và ánh xạ dải mã WBS."""
    workbook, boq, calculation, rfi, qa = styler.create_csa_workbook()
    styler.setup_boq_headers(boq)
    styler.setup_takeoff_calculation_headers(calculation)
    styler.setup_rfi_headers(rfi)
    styler.setup_qa_audit_headers(qa)
    styler.add_boq_item(
        boq, 6, "A.01.01", "Bê tông móng M1", "m3", 10.0,
        "Location=Móng M1; Geometry=8 * 1.60 * 1.40 * 0.40 = 10.00 m3; Deductions=None; Calc ID=CAL-CONC-01",
    )
    styler.add_takeoff_calculation_item(
        calculation, 6, "CAL-CONC-01", "A.01.01", "Móng M1", "260917_ASCO_B11_S Rev.01",
        "Mặt bằng móng", "8 * 1.60 * 1.40 * 0.40", "Không khấu trừ", "m3", 10.0,
        "Verified", "Lead QS", "Quantity Class=NET_DESIGN",
    )
    
    subgates = [
        ("Gate 0", "Hồ sơ bảng tính 4 sheet B11 OP2 (Toàn bộ Workbook)"),
        ("Gate 1", "63 dòng công tác BOQ (WBS A.I.01 - C.II.04)"),
        ("Gate 2.1", "Công tác đất & nền móng (WBS A.I.01 - A.I.07)"),
        ("Gate 2.2", "Cốt thép BTCT móng, giằng, cột, dầm (WBS A.II.01 - A.V.08)"),
        ("Gate 3.1", "Kết cấu thép mái, xà gồ Z150 (WBS A.VI.01 - A.VI.06)"),
        ("Gate 3.2", "Hệ cửa đi & louver (WBS B.V.01 - B.V.03)"),
        ("Gate 4.1", "Gói chi phí trọng yếu Pareto 80/20 (Top 20% dòng BOQ)"),
        ("Gate 4.2", "Hồ sơ 4 RFI kỹ thuật & Khung bê tông (RFI-01 - RFI-04)"),
    ]
    for row_idx, (gate, target) in enumerate(subgates, 6):
        styler.add_qa_audit_item(
            qa, row_idx, gate, "Kiểm tra kỹ thuật", target, "Major",
            "Đã đối soát đầy đủ", "Không yêu cầu hành động", "QA Lead", "Pass", "2026-09-24",
        )

    out_file = tmp_path / "boq_subgates.xlsx"
    doc_reg = {"260917_ASCO_B11_S": "Rev.01"}
    res = styler.save_and_validate_csa_workbook(workbook, out_file, document_register=doc_reg)
    assert res.passed is True

