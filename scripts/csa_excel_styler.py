"""
CSA EXCEL STYLER - EXECUTIVE CORPORATE STANDARD
Module định dạng chuẩn hóa 100% cho toàn bộ bảng tính BOQ và RFI của CSA Takeoff Suite.
Tuyệt đối KHÔNG tự định nghĩa lại style thủ công. Mọi Agent bắt buộc sử dụng module này.
"""

import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from numbers import Real
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.table import Table, TableStyleInfo

# ==============================================================================
# 1. HẰNG SỐ BẤT BIẾN (IMMUTABLE CONSTANTS)
# ==============================================================================
FONT_FAMILY = "Arial"
QUANTITY_RECONCILIATION_TOLERANCE = 0.005
REQUIRED_GATES = ("Gate 0", "Gate 1", "Gate 2", "Gate 3", "Gate 4")
QA_VALID_STATUSES = {"Pass", "Open", "Resolved", "RFI Required"}
RFI_VALID_STATUSES = {
    "Open", "Pending", "RFI Required", "Resolved", "Closed", "Cancelled"
}
RFI_RELEASED_STATUSES = {"Resolved", "Closed", "Cancelled"}
CALC_VALID_STATUSES = {"Verified", "Draft", "Assumption", "RFI Required", "Open"}
QUANTITY_CLASSES = {"NET_DESIGN", "PROCUREMENT_ONLY"}
EARTHWORK_STATES = {
    "IN_SITU_EXCAVATION",
    "LOOSE_HAUL",
    "COMPACTED_FILL",
    "REUSE",
    "IMPORTED",
    "DISPOSAL",
}
EARTHWORK_BALANCE_TABLE_NAME = "Earthwork_Balance"
EARTHWORK_BALANCE_START_COLUMN = 14  # N
TAKEOFF_LEGEND_TITLE = "CHÚ GIẢI NHÃN KIỂM SOÁT"
TAKEOFF_LEGEND_ENTRIES = (
    ("NET_DESIGN", "Khối lượng thiết kế hình học; được phép tổng hợp vào BOQ khi đã Verified."),
    ("PROCUREMENT_ONLY", "Hao hụt mua sắm, cắt uốn, vận chuyển hoặc thi công; không cộng vào BOQ."),
    ("IN_SITU_EXCAVATION", "Đất nguyên thổ đào."),
    ("LOOSE_HAUL", "Đất tơi vận chuyển."),
    ("COMPACTED_FILL", "Đất đắp đã đầm."),
    ("REUSE", "Đất đào được tái sử dụng."),
    ("IMPORTED", "Đất mua ngoài."),
    ("DISPOSAL", "Đất thừa vận chuyển đi đổ."),
)

# --- MÀU SẮC SHEET BOQ (XANH NAVY CORPORATE) ---
COLOR_BOQ_TITLE = "1F4E78"        # Xanh Navy đậm cho tiêu đề
COLOR_BOQ_HEADER_FILL = "1F4E78"  # Nền Header Row 5
COLOR_BOQ_HEADER_TXT = "FFFFFF"   # Chữ Header Row 5 (Trắng)
COLOR_BOQ_LEVEL1_FILL = "D9E1F2"  # Nền Phân mục Level 1 (Xanh nhạt)
COLOR_BOQ_LEVEL1_TXT = "002060"   # Chữ Level 1 (Navy đậm)
COLOR_BOQ_LEVEL2_FILL = "F2F2F2"  # Nền Tiểu mục Level 2 (Xám nhạt)
COLOR_BOQ_LEVEL2_TXT = "1F4E78"   # Chữ Level 2 (Navy)

# --- MÀU SẮC SHEET RFI (CAM ĐẤT RUST ORANGE) ---
COLOR_RFI_TITLE = "C65911"        # Cam Đất cho tiêu đề RFI
COLOR_RFI_HEADER_FILL = "C65911"  # Nền Header RFI Row 5
COLOR_RFI_HEADER_TXT = "FFFFFF"   # Chữ Header RFI (Trắng)
COLOR_RFI_GROUP_FILL = "FCE4D6"   # Nền Phân nhóm RFI (Cam đào / Kem)
COLOR_RFI_GROUP_TXT = "833C0C"    # Chữ Phân nhóm RFI (Đỏ Nâu)

# --- ĐƯỜNG VIỀN & MÀU PHỤ TRỢ ---
COLOR_BORDER_DATA = "D9D9D9"      # Viền mỏng ô có nội dung dữ liệu
COLOR_SUBTITLE = "595959"         # Chữ ghi chú tiêu đề (Xám vừa)

# --- CHIỀU CAO DÒNG CỐ ĐỊNH CHO TIÊU ĐỀ & PHÂN MỤC (FIXED FOR TITLE & SECTIONS) ---
HEIGHT_TITLE_1 = 25.0
HEIGHT_TITLE_2 = 20.0
HEIGHT_TITLE_3 = 18.0
HEIGHT_BLANK_GAP = 10.0
HEIGHT_HEADER = 48.0
HEIGHT_LEVEL1 = 28.0
HEIGHT_LEVEL2 = 24.0
MIN_DATA_ROW_HEIGHT = 28.0        # Chiều cao tối thiểu sau khi AutoFit dữ liệu (tránh co cụm)

# --- ĐỘ RỘNG CỘT CHUẨN (COLUMN WIDTHS) ---
WIDTHS_BOQ = {
    "A": 13.0,  # Mã WBS
    "B": 65.0,  # Diễn giải Tam ngữ
    "C": 12.0,  # ĐVT
    "D": 16.0,  # Khối lượng CAD
    "E": 65.0   # Công thức hình học chi tiết (In nghiêng)
}

WIDTHS_RFI = {
    "A": 12.0,  # Mã RFI
    "B": 30.0,  # WBS / Hạng mục
    "C": 38.0,  # Vị trí / Bản vẽ / Revision
    "D": 22.0,  # ĐVT & Khối lượng dự trù
    "E": 50.0,  # Công thức tạm tính
    "F": 50.0,  # Cơ sở kỹ thuật & Câu hỏi
    "G": 30.0,  # Tác động chi phí & Tiến độ
    "H": 32.0   # Người phụ trách / Trạng thái / Hạn
}

WIDTHS_CALCULATION = {
    "A": 14.0,
    "B": 14.0,
    "C": 28.0,
    "D": 30.0,
    "E": 40.0,
    "F": 55.0,
    "G": 45.0,
    "H": 12.0,
    "I": 16.0,
    "J": 18.0,
    "K": 22.0,
    "L": 30.0,
}

WIDTHS_QA_AUDIT = {
    "A": 12.0,
    "B": 34.0,
    "C": 24.0,
    "D": 14.0,
    "E": 45.0,
    "F": 45.0,
    "G": 22.0,
    "H": 18.0,
    "I": 18.0,
}

WIDTHS_EARTHWORK_BALANCE = {
    "N": 28.0,
    "O": 24.0,
    "P": 28.0,
    "Q": 12.0,
    "R": 18.0,
    "S": 20.0,
    "T": 18.0,
    "U": 15.0,
    "V": 15.0,
    "W": 15.0,
    "X": 38.0,
}

HEADERS_BOQ = [
    "MÃ WBS\n(WBS Code)",
    "MÔ TẢ CÔNG VIỆC / ITEM DESCRIPTION / 清单项目名称\n(Tiếng Việt - English - 中文 GB 50500)",
    "ĐƠN VỊ\n(Unit)",
    "KHỐI LƯỢNG THỰC TẾ CAD\n(CAD Actual Qty)",
    "CÔNG THỨC HÌNH HỌC TÓM TẮT & CALC ID\n(Quick Formula & Calculation ID)",
]

HEADERS_CALCULATION = [
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

HEADERS_RFI = [
    "MÃ RFI\n(RFI No.)",
    "MÃ WBS / HẠNG MỤC\n(WBS / Trade)",
    "VỊ TRÍ – BẢN VẼ – REVISION\n(Location – Drawing – Revision)",
    "ĐVT & KHỐI LƯỢNG DỰ TRÙ\n(Unit & Provisional Quantity)",
    "CÔNG THỨC TẠM TÍNH\n(Provisional Formula)",
    "CƠ SỞ KỸ THUẬT & CÂU HỎI\n(Technical Basis & Query)",
    "TÁC ĐỘNG CHI PHÍ / TIẾN ĐỘ\n(Cost / Schedule Impact)",
    "NGƯỜI PHỤ TRÁCH – TRẠNG THÁI – HẠN\n(Owner – Status – Due Date)",
]

HEADERS_QA_AUDIT = [
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

HEADERS_EARTHWORK_BALANCE = [
    "WBS / KHU VỰC\n(WBS / Location)",
    "BẢN VẼ & REVISION\n(Drawing & Revision)",
    "CALC ID NGUỒN\n(Source Calc IDs)",
    "ĐƠN VỊ\n(Unit)",
    "ĐÀO NGUYÊN THỔ\n(In-situ Excavation)",
    "ĐẤT TƠI VẬN CHUYỂN\n(Loose / Haul)",
    "ĐẮP ĐÃ ĐẦM\n(Compacted Fill)",
    "TÁI SỬ DỤNG\n(Reuse)",
    "MUA NGOÀI\n(Imported)",
    "THẢI BỎ\n(Disposal)",
    "CƠ SỞ CÂN BẰNG / GHI CHÚ\n(Balance Basis / Notes)",
]

EARTHWORK_STATE_TO_BALANCE_COLUMN = {
    "IN_SITU_EXCAVATION": 5,
    "LOOSE_HAUL": 6,
    "COMPACTED_FILL": 7,
    "REUSE": 8,
    "IMPORTED": 9,
    "DISPOSAL": 10,
}

SHEET_LAYOUTS = {
    "BOQ": (HEADERS_BOQ, WIDTHS_BOQ),
    "Takeoff_Calculation": (HEADERS_CALCULATION, WIDTHS_CALCULATION),
    "RFI_Kien_Nghi_Bo_Sung": (HEADERS_RFI, WIDTHS_RFI),
    "QA_Audit": (HEADERS_QA_AUDIT, WIDTHS_QA_AUDIT),
}


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    errors: tuple[str, ...]

# ==============================================================================
# 2. STYLES KHỞI TẠO CỐ ĐỊNH (PRE-BUILT STYLES)
# ==============================================================================
# Fonts
FONT_TITLE_BOQ = Font(name=FONT_FAMILY, size=14, bold=True, color=COLOR_BOQ_TITLE)
FONT_SUBTITLE_PROJ_BOQ = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_BOQ_TITLE)
FONT_TITLE_RFI = Font(name=FONT_FAMILY, size=14, bold=True, color=COLOR_RFI_TITLE)
FONT_SUBTITLE_PROJ_RFI = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_RFI_GROUP_TXT)
FONT_SUBTITLE_REF = Font(name=FONT_FAMILY, size=10, italic=True, color=COLOR_SUBTITLE)

FONT_HEADER_BOQ = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_BOQ_HEADER_TXT)
FONT_HEADER_RFI = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_RFI_HEADER_TXT)

FONT_SEC_BOQ = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_BOQ_LEVEL1_TXT)
FONT_SUBSEC_BOQ = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_BOQ_LEVEL2_TXT)
FONT_GROUP_RFI = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_RFI_GROUP_TXT)

FONT_ITEM_WBS = Font(name=FONT_FAMILY, size=10, bold=True, color="000000")
FONT_ITEM_DESC = Font(name=FONT_FAMILY, size=10, color="000000")
FONT_ITEM_UNIT = Font(name=FONT_FAMILY, size=10, color="000000")
FONT_ITEM_QTY = Font(name=FONT_FAMILY, size=10, bold=True, color="000000")
FONT_ITEM_FORMULA = Font(name=FONT_FAMILY, size=9.5, italic=True, color="333333")  # BẮT BUỘC IN NGHIÊNG

# Fills
FILL_HEADER_BOQ = PatternFill(start_color=COLOR_BOQ_HEADER_FILL, end_color=COLOR_BOQ_HEADER_FILL, fill_type="solid")
FILL_SEC_BOQ = PatternFill(start_color=COLOR_BOQ_LEVEL1_FILL, end_color=COLOR_BOQ_LEVEL1_FILL, fill_type="solid")
FILL_SUBSEC_BOQ = PatternFill(start_color=COLOR_BOQ_LEVEL2_FILL, end_color=COLOR_BOQ_LEVEL2_FILL, fill_type="solid")

FILL_HEADER_RFI = PatternFill(start_color=COLOR_RFI_HEADER_FILL, end_color=COLOR_RFI_HEADER_FILL, fill_type="solid")
FILL_GROUP_RFI = PatternFill(start_color=COLOR_RFI_GROUP_FILL, end_color=COLOR_RFI_GROUP_FILL, fill_type="solid")

# Borders
THIN_SIDE = Side(border_style="thin", color=COLOR_BORDER_DATA)
BORDER_DATA = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)

BORDER_HEADER_BOQ = Border(
    left=Side(border_style="thin", color=COLOR_BOQ_HEADER_FILL),
    right=Side(border_style="thin", color=COLOR_BOQ_HEADER_FILL),
    top=Side(border_style="thin", color=COLOR_BOQ_HEADER_FILL),
    bottom=Side(border_style="thin", color=COLOR_BOQ_HEADER_FILL)
)

BORDER_HEADER_RFI = Border(
    left=Side(border_style="thin", color=COLOR_RFI_HEADER_FILL),
    right=Side(border_style="thin", color=COLOR_RFI_HEADER_FILL),
    top=Side(border_style="thin", color=COLOR_RFI_HEADER_FILL),
    bottom=Side(border_style="thin", color=COLOR_RFI_HEADER_FILL)
)

# Alignments
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")


# ==============================================================================
# 3. HÀM KHỞI TẠO & ÁP DỤNG ĐỊNH DẠNG (BUILDER FUNCTIONS)
# ==============================================================================
def create_csa_workbook():
    """
    Khởi tạo Workbook chuẩn gồm BOQ, phép tính, RFI và nhật ký QA.
    Tắt 100% đường lưới mặc định theo quy chuẩn Pure White Canvas.
    """
    wb = openpyxl.Workbook()
    
    ws_boq = wb.active
    ws_boq.title = "BOQ"
    ws_calculation = wb.create_sheet(title="Takeoff_Calculation")
    ws_rfi = wb.create_sheet(title="RFI_Kien_Nghi_Bo_Sung")
    ws_qa = wb.create_sheet(title="QA_Audit")

    for worksheet in wb.worksheets:
        worksheet.views.sheetView[0].showGridLines = False
    
    return wb, ws_boq, ws_calculation, ws_rfi, ws_qa


def setup_title_banner(ws, title_text, project_text, ref_text, is_rfi=False):
    """
    Tạo khối tiêu đề 3 dòng (Row 1-3) và khoảng cách dòng 4.
    """
    if ws.title == "Takeoff_Calculation":
        max_col = 12
    elif ws.title == "QA_Audit":
        max_col = 9
    elif is_rfi or ws.title == "RFI_Kien_Nghi_Bo_Sung":
        max_col = 8
    else:
        max_col = 5
    max_letter = get_column_letter(max_col)
    
    ws.row_dimensions[1].height = HEIGHT_TITLE_1
    ws.row_dimensions[2].height = HEIGHT_TITLE_2
    ws.row_dimensions[3].height = HEIGHT_TITLE_3
    ws.row_dimensions[4].height = HEIGHT_BLANK_GAP
    
    # Row 1
    ws.merge_cells(f"A1:{max_letter}1")
    cell1 = ws["A1"]
    cell1.value = title_text
    cell1.font = FONT_TITLE_RFI if is_rfi else FONT_TITLE_BOQ
    cell1.alignment = ALIGN_CENTER
    
    # Row 2
    ws.merge_cells(f"A2:{max_letter}2")
    cell2 = ws["A2"]
    cell2.value = project_text
    cell2.font = FONT_SUBTITLE_PROJ_RFI if is_rfi else FONT_SUBTITLE_PROJ_BOQ
    cell2.alignment = ALIGN_CENTER
    
    # Row 3
    ws.merge_cells(f"A3:{max_letter}3")
    cell3 = ws["A3"]
    cell3.value = ref_text
    cell3.font = FONT_SUBTITLE_REF
    cell3.alignment = ALIGN_CENTER


def setup_boq_headers(ws, headers=None):
    """
    Tạo Header chuẩn 5 cột A-E cho Sheet BOQ tại Row 5.
    """
    if headers is None:
        headers = HEADERS_BOQ
        
    ws.row_dimensions[5].height = HEIGHT_HEADER
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col_idx, value=h)
        cell.font = FONT_HEADER_BOQ
        cell.fill = FILL_HEADER_BOQ
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_HEADER_BOQ


def setup_takeoff_calculation_headers(ws, headers=None):
    """Tạo Header truy vết phép tính tại dòng 5."""
    if headers is None:
        headers = HEADERS_CALCULATION

    ws.row_dimensions[5].height = HEIGHT_HEADER
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col_idx, value=header)
        cell.font = FONT_HEADER_BOQ
        cell.fill = FILL_HEADER_BOQ
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_HEADER_BOQ


def setup_rfi_headers(ws, headers=None):
    """
    Tạo Header chuẩn 6 cột A-F cho Sheet RFI tại Row 5.
    """
    if headers is None:
        headers = HEADERS_RFI
        
    ws.row_dimensions[5].height = HEIGHT_HEADER
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col_idx, value=h)
        cell.font = FONT_HEADER_RFI
        cell.fill = FILL_HEADER_RFI
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_HEADER_RFI


def setup_qa_audit_headers(ws, headers=None):
    """Tạo Header nhật ký kiểm soát 5 cổng tại dòng 5."""
    if headers is None:
        headers = HEADERS_QA_AUDIT

    ws.row_dimensions[5].height = HEIGHT_HEADER
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col_idx, value=header)
        cell.font = FONT_HEADER_BOQ
        cell.fill = FILL_HEADER_BOQ
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_HEADER_BOQ


def setup_earthwork_balance_headers(ws):
    """Tạo bảng phụ cân bằng đất trong Takeoff_Calculation, không thêm sheet thứ năm."""
    ws.row_dimensions[5].height = HEIGHT_HEADER
    for offset, header in enumerate(HEADERS_EARTHWORK_BALANCE):
        column = EARTHWORK_BALANCE_START_COLUMN + offset
        cell = ws.cell(row=5, column=column, value=header)
        cell.font = FONT_HEADER_BOQ
        cell.fill = FILL_HEADER_BOQ
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_HEADER_BOQ
    for column, width in WIDTHS_EARTHWORK_BALANCE.items():
        ws.column_dimensions[column].width = width


def _refresh_earthwork_balance_table(ws):
    """Cập nhật vùng Excel Table sau khi thêm một hàng cân bằng đất."""
    first_column = EARTHWORK_BALANCE_START_COLUMN
    last_column = first_column + len(HEADERS_EARTHWORK_BALANCE) - 1
    last_row = 5
    for row_idx in range(6, ws.max_row + 1):
        if any(ws.cell(row=row_idx, column=column).value is not None for column in range(first_column, last_column + 1)):
            last_row = row_idx
    if last_row == 5:
        return

    ref = f"{get_column_letter(first_column)}5:{get_column_letter(last_column)}{last_row}"
    if EARTHWORK_BALANCE_TABLE_NAME in ws.tables:
        ws.tables[EARTHWORK_BALANCE_TABLE_NAME].ref = ref
        return

    table = Table(displayName=EARTHWORK_BALANCE_TABLE_NAME, ref=ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
        showRowStripes=False, showColumnStripes=False,
    )
    ws.add_table(table)


def add_earthwork_balance_item(
    ws,
    row_idx,
    wbs_location,
    drawing_revision,
    source_calc_ids,
    unit,
    in_situ_excavation,
    loose_haul,
    compacted_fill,
    reuse,
    imported,
    disposal,
    balance_basis_notes,
):
    """Thêm một dòng cân bằng đất theo sáu trạng thái thể tích bắt buộc."""
    if ws.cell(row=5, column=EARTHWORK_BALANCE_START_COLUMN).value != HEADERS_EARTHWORK_BALANCE[0]:
        setup_earthwork_balance_headers(ws)

    values = [
        wbs_location,
        drawing_revision,
        source_calc_ids,
        unit,
        in_situ_excavation,
        loose_haul,
        compacted_fill,
        reuse,
        imported,
        disposal,
        balance_basis_notes,
    ]
    for offset, value in enumerate(values):
        column = EARTHWORK_BALANCE_START_COLUMN + offset
        cell = ws.cell(row=row_idx, column=column, value=value)
        cell.border = BORDER_DATA
        cell.alignment = ALIGN_LEFT
        cell.font = FONT_ITEM_DESC
        if offset in (4, 5, 6, 7, 8, 9) and isinstance(value, Real) and not isinstance(value, bool):
            cell.font = FONT_ITEM_QTY
            cell.alignment = ALIGN_RIGHT
            cell.number_format = "#,##0.00"

    for offset in (2, 3):
        cell = ws.cell(row=row_idx, column=EARTHWORK_BALANCE_START_COLUMN + offset)
        cell.alignment = ALIGN_CENTER
        cell.font = FONT_ITEM_WBS
    ws.row_dimensions[row_idx].height = None
    _refresh_earthwork_balance_table(ws)


def _takeoff_legend_start_row(ws):
    """Trả về dòng tiêu đề chú giải nếu chú giải đã tồn tại."""
    if ws.title != "Takeoff_Calculation":
        return None
    for row_idx in range(6, ws.max_row + 1):
        if ws.cell(row=row_idx, column=1).value == TAKEOFF_LEGEND_TITLE:
            return row_idx
    return None


def _is_takeoff_legend_row(ws, row_idx):
    """Nhận diện vùng chú giải để không coi đây là dữ liệu phép tính."""
    start_row = _takeoff_legend_start_row(ws)
    if start_row is None:
        return False
    last_row = start_row + 1 + len(TAKEOFF_LEGEND_ENTRIES)
    return start_row <= row_idx <= last_row


def _clear_takeoff_calculation_legend(ws):
    """Xóa chú giải cũ để hàm tạo chú giải có thể gọi lại an toàn."""
    start_row = _takeoff_legend_start_row(ws)
    if start_row is None:
        return
    last_row = start_row + 1 + len(TAKEOFF_LEGEND_ENTRIES)
    for merged_range in list(ws.merged_cells.ranges):
        if merged_range.min_row >= start_row and merged_range.max_row <= last_row:
            ws.unmerge_cells(str(merged_range))
    for row_idx in range(start_row, last_row + 1):
        for column in range(1, len(HEADERS_CALCULATION) + 1):
            ws.cell(row=row_idx, column=column).value = None
        ws.row_dimensions[row_idx].height = None


def add_takeoff_calculation_legend(ws):
    """Thêm chú giải tiếng Việt cho các nhãn kiểm soát dưới bảng phép tính."""
    if ws.title != "Takeoff_Calculation":
        raise ValueError("Chú giải chỉ áp dụng cho sheet Takeoff_Calculation")

    _clear_takeoff_calculation_legend(ws)
    last_content_row = 5
    for row_idx in range(6, ws.max_row + 1):
        if any(ws.cell(row=row_idx, column=column).value is not None for column in range(1, 25)):
            last_content_row = row_idx
    start_row = last_content_row + 3
    last_column = len(HEADERS_CALCULATION)

    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=last_column)
    title_cell = ws.cell(row=start_row, column=1, value=TAKEOFF_LEGEND_TITLE)
    title_cell.font = FONT_SEC_BOQ
    title_cell.fill = FILL_SEC_BOQ
    title_cell.alignment = ALIGN_LEFT
    for column in range(1, last_column + 1):
        cell = ws.cell(row=start_row, column=column)
        cell.fill = FILL_SEC_BOQ
        cell.border = BORDER_DATA
    ws.row_dimensions[start_row].height = HEIGHT_LEVEL1

    header_row = start_row + 1
    ws.cell(row=header_row, column=1, value="MÃ NHÃN")
    ws.merge_cells(start_row=header_row, start_column=2, end_row=header_row, end_column=last_column)
    ws.cell(row=header_row, column=2, value="GIẢI THÍCH")
    for column in range(1, last_column + 1):
        cell = ws.cell(row=header_row, column=column)
        cell.font = FONT_SUBSEC_BOQ
        cell.fill = FILL_SUBSEC_BOQ
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_DATA
    ws.row_dimensions[header_row].height = HEIGHT_LEVEL2

    for offset, (code, description) in enumerate(TAKEOFF_LEGEND_ENTRIES, start=2):
        row_idx = start_row + offset
        ws.cell(row=row_idx, column=1, value=code)
        ws.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=last_column)
        ws.cell(row=row_idx, column=2, value=description)
        for column in range(1, last_column + 1):
            cell = ws.cell(row=row_idx, column=column)
            cell.fill = FILL_SUBSEC_BOQ
            cell.border = BORDER_DATA
        ws.cell(row=row_idx, column=1).font = FONT_ITEM_WBS
        ws.cell(row=row_idx, column=1).alignment = ALIGN_CENTER
        ws.cell(row=row_idx, column=2).font = FONT_ITEM_DESC
        ws.cell(row=row_idx, column=2).alignment = ALIGN_LEFT
        ws.row_dimensions[row_idx].height = HEIGHT_LEVEL2

    return start_row


def add_boq_section_level1(ws, row_idx, section_code, section_name):
    """
    Thêm dòng phân mục chính Level 1 (Phần I, II...): Nền #D9E1F2, Chữ #002060 Bold, Cao 28pt.
    """
    normalized_code = str(section_code).strip().rstrip(".")
    normalized_name = str(section_name).strip()
    if re.match(
        rf"^PHẦN\s+{re.escape(normalized_code)}\s*:",
        normalized_name,
        flags=re.IGNORECASE,
    ):
        display_name = normalized_name
    else:
        display_name = f"{normalized_code}. {normalized_name}"

    ws.row_dimensions[row_idx].height = HEIGHT_LEVEL1
    ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=5)
    cell = ws.cell(row=row_idx, column=1, value=display_name)
    cell.font = FONT_SEC_BOQ
    cell.fill = FILL_SEC_BOQ
    cell.alignment = ALIGN_LEFT
    for col in range(1, 6):
        ws.cell(row=row_idx, column=col).fill = FILL_SEC_BOQ
        ws.cell(row=row_idx, column=col).border = BORDER_DATA


def add_boq_section_level2(ws, row_idx, subsection_code, subsection_name):
    """
    Thêm dòng tiểu mục Level 2 (I.1, I.2...): Nền #F2F2F2, Chữ #1F4E78 Bold, Cao 24pt.
    """
    ws.row_dimensions[row_idx].height = HEIGHT_LEVEL2
    ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=5)
    cell = ws.cell(row=row_idx, column=1, value=f"{subsection_code}. {subsection_name}")
    cell.font = FONT_SUBSEC_BOQ
    cell.fill = FILL_SUBSEC_BOQ
    cell.alignment = ALIGN_LEFT
    for col in range(1, 6):
        ws.cell(row=row_idx, column=col).fill = FILL_SUBSEC_BOQ
        ws.cell(row=row_idx, column=col).border = BORDER_DATA


def add_boq_item(ws, row_idx, wbs, desc_trilingual, unit, qty, formula_detail):
    """
    Thêm dòng công tác dữ liệu chuẩn 5 cột (1 Item = 1 Single Row, AutoFit Row Height).
    """
    # Không gán cứng chiều cao dòng để Excel tự động AutoFit theo độ dài văn bản
    ws.row_dimensions[row_idx].height = None
    
    # Cột A: WBS
    c1 = ws.cell(row=row_idx, column=1, value=wbs)
    c1.font = FONT_ITEM_WBS
    c1.alignment = ALIGN_CENTER
    c1.border = BORDER_DATA
    
    # Cột B: Diễn giải Tam ngữ
    c2 = ws.cell(row=row_idx, column=2, value=desc_trilingual)
    c2.font = FONT_ITEM_DESC
    c2.alignment = ALIGN_LEFT
    c2.border = BORDER_DATA
    
    # Cột C: Đơn vị
    c3 = ws.cell(row=row_idx, column=3, value=unit)
    c3.font = FONT_ITEM_UNIT
    c3.alignment = ALIGN_CENTER
    c3.border = BORDER_DATA
    
    # Cột D: Khối lượng CAD In đậm
    c4 = ws.cell(row=row_idx, column=4, value=qty)
    c4.font = FONT_ITEM_QTY
    c4.alignment = ALIGN_RIGHT
    c4.border = BORDER_DATA
    if isinstance(qty, (int, float)):
        c4.number_format = "#,##0.00"
        
    # Cột E: Công thức hình học In nghiêng
    c5 = ws.cell(row=row_idx, column=5, value=formula_detail)
    c5.font = FONT_ITEM_FORMULA
    c5.alignment = ALIGN_LEFT
    c5.border = BORDER_DATA


def add_takeoff_calculation_item(
    ws,
    row_idx,
    calc_id,
    boq_wbs,
    location_element,
    drawing_revision,
    source_view_detail,
    measurement_formula,
    deductions_measurement_basis,
    unit,
    qty,
    data_status,
    checker,
    remarks,
):
    """Thêm một phép tính chi tiết liên kết với một dòng BOQ qua CALC ID."""
    ws.row_dimensions[row_idx].height = None
    values = [
        calc_id,
        boq_wbs,
        location_element,
        drawing_revision,
        source_view_detail,
        measurement_formula,
        deductions_measurement_basis,
        unit,
        qty,
        data_status,
        checker,
        remarks,
    ]

    for column, value in enumerate(values, 1):
        cell = ws.cell(row=row_idx, column=column, value=value)
        cell.border = BORDER_DATA
        cell.alignment = ALIGN_LEFT
        cell.font = FONT_ITEM_DESC

    for column in (1, 2, 8, 10, 11):
        ws.cell(row=row_idx, column=column).alignment = ALIGN_CENTER
        ws.cell(row=row_idx, column=column).font = FONT_ITEM_WBS

    for column in (6, 7):
        ws.cell(row=row_idx, column=column).font = FONT_ITEM_FORMULA

    qty_cell = ws.cell(row=row_idx, column=9)
    qty_cell.font = FONT_ITEM_QTY
    qty_cell.alignment = ALIGN_RIGHT
    if isinstance(qty, (int, float)):
        qty_cell.number_format = "#,##0.00"


def add_rfi_item(
    ws,
    row_idx,
    rfi_no,
    wbs_trade,
    location_drawing_revision,
    unit_provisional_qty,
    provisional_formula,
    technical_basis_query,
    cost_schedule_impact,
    owner_status_due_date,
):
    """Thêm dòng yêu cầu làm rõ thiết kế chuẩn 8 cột."""
    ws.row_dimensions[row_idx].height = None
    values = [
        rfi_no,
        wbs_trade,
        location_drawing_revision,
        unit_provisional_qty,
        provisional_formula,
        technical_basis_query,
        cost_schedule_impact,
        owner_status_due_date,
    ]

    for column, value in enumerate(values, 1):
        cell = ws.cell(row=row_idx, column=column, value=value)
        cell.font = FONT_ITEM_DESC
        cell.alignment = ALIGN_LEFT
        cell.border = BORDER_DATA

    ws.cell(row=row_idx, column=1).font = FONT_ITEM_WBS
    ws.cell(row=row_idx, column=1).alignment = ALIGN_CENTER
    ws.cell(row=row_idx, column=5).font = FONT_ITEM_FORMULA
    ws.cell(row=row_idx, column=7).font = Font(
        name=FONT_FAMILY, size=9.5, italic=True, color=COLOR_RFI_GROUP_TXT
    )


def add_qa_audit_item(
    ws,
    row_idx,
    gate,
    check_rule,
    target,
    severity,
    evidence,
    required_action,
    owner,
    status,
    audit_date,
):
    """Thêm một dòng nhật ký kiểm tra QA/QC."""
    ws.row_dimensions[row_idx].height = None
    values = [
        gate,
        check_rule,
        target,
        severity,
        evidence,
        required_action,
        owner,
        status,
        audit_date,
    ]

    for column, value in enumerate(values, 1):
        cell = ws.cell(row=row_idx, column=column, value=value)
        cell.font = FONT_ITEM_DESC
        cell.alignment = ALIGN_LEFT
        cell.border = BORDER_DATA

    for column in (1, 4, 7, 8, 9):
        ws.cell(row=row_idx, column=column).alignment = ALIGN_CENTER
    for column in (1, 4, 8):
        ws.cell(row=row_idx, column=column).font = FONT_ITEM_WBS


def finalize_columns(ws, is_rfi=False):
    """Cố định độ rộng cột theo đúng loại sheet."""
    if ws.title in SHEET_LAYOUTS:
        _, widths = SHEET_LAYOUTS[ws.title]
    else:
        widths = WIDTHS_RFI if is_rfi else WIDTHS_BOQ
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width


def finalize_workbook_layout(wb):
    """Áp dụng layout bất biến cho tất cả sheet phát hành."""
    for sheet_name in SHEET_LAYOUTS:
        ws = wb[sheet_name]
        ws.views.sheetView[0].showGridLines = False
        finalize_columns(ws)
        if sheet_name == "Takeoff_Calculation":
            for column, width in WIDTHS_EARTHWORK_BALANCE.items():
                ws.column_dimensions[column].width = width
            if any(True for _ in _data_rows(ws)):
                add_takeoff_calculation_legend(ws)
        for row_idx in _data_rows(ws):
            if not _is_merged_data_row(ws, row_idx):
                existing_height = ws.row_dimensions[row_idx].height or 0
                ws.row_dimensions[row_idx].height = max(existing_height, MIN_DATA_ROW_HEIGHT)


def _primary_column_count(ws):
    layout = SHEET_LAYOUTS.get(ws.title)
    return len(layout[0]) if layout else ws.max_column


def _is_merged_data_row(ws, row_idx):
    return any(ws.cell(row=row_idx, column=1).coordinate in rng for rng in ws.merged_cells.ranges)


def _data_rows(ws):
    primary_column_count = _primary_column_count(ws)
    for row_idx in range(6, ws.max_row + 1):
        if _is_takeoff_legend_row(ws, row_idx):
            continue
        if any(ws.cell(row=row_idx, column=column).value is not None for column in range(1, primary_column_count + 1)):
            yield row_idx


def _schedule_reference_without_geometry(value):
    """Trả về nhãn Schedule nếu nó bị dùng thay cho phép tính hình học."""
    formula_text = str(value or "")
    normalized = formula_text.lower()
    if "theo schedule" in normalized:
        marker = "Theo Schedule"
    elif "theo bảng thống kê" in normalized:
        marker = "Theo Bảng thống kê"
    else:
        return None

    has_geometry = bool(
        re.search(r"\d+(?:[.,]\d+)?\s*[x×*]\s*\d+(?:[.,]\d+)?", formula_text)
    )
    return None if has_geometry else marker


def _rgb(color):
    """Lấy mã RGB sáu ký tự để so style mà không phụ thuộc prefix ARGB."""
    if color is None or color.type != "rgb" or not color.rgb:
        return None
    return color.rgb[-6:].upper()


def _font_matches(actual, expected):
    return (
        actual.name == expected.name
        and actual.sz == expected.sz
        and bool(actual.bold) == bool(expected.bold)
        and bool(actual.italic) == bool(expected.italic)
        and _rgb(actual.color) == _rgb(expected.color)
    )


def _border_matches(actual, expected):
    for side_name in ("left", "right", "top", "bottom"):
        actual_side = getattr(actual, side_name)
        expected_side = getattr(expected, side_name)
        if (
            actual_side is None
            or actual_side.style != expected_side.style
            or _rgb(actual_side.color) != _rgb(expected_side.color)
        ):
            return False
    return True


def _alignment_matches(actual, expected):
    return (
        actual.horizontal == expected.horizontal
        and actual.vertical == expected.vertical
        and bool(actual.wrap_text) == bool(expected.wrap_text)
    )


def _header_style_for_sheet(sheet_name):
    if sheet_name == "RFI_Kien_Nghi_Bo_Sung":
        return FONT_HEADER_RFI, FILL_HEADER_RFI, BORDER_HEADER_RFI
    return FONT_HEADER_BOQ, FILL_HEADER_BOQ, BORDER_HEADER_BOQ


def _data_alignment_for_column(sheet_name, column):
    centered_columns = {
        "BOQ": {1, 3},
        "Takeoff_Calculation": {1, 2, 8, 10, 11},
        "RFI_Kien_Nghi_Bo_Sung": {1},
        "QA_Audit": {1, 4, 7, 8, 9},
    }
    right_columns = {
        "BOQ": {4},
        "Takeoff_Calculation": {9},
    }
    if column in centered_columns.get(sheet_name, set()):
        return ALIGN_CENTER
    if column in right_columns.get(sheet_name, set()):
        return ALIGN_RIGHT
    return ALIGN_LEFT


def _validate_header_cell(sheet_name, column, cell, errors):
    expected_font, expected_fill, expected_border = _header_style_for_sheet(sheet_name)
    if not _font_matches(cell.font, expected_font):
        errors.append(f"{sheet_name}: Header cột {column} sai font Gate 0")
    if cell.fill.fill_type != expected_fill.fill_type or _rgb(cell.fill.fgColor) != _rgb(expected_fill.fgColor):
        errors.append(f"{sheet_name}: Header cột {column} sai fill Gate 0")
    if not _border_matches(cell.border, expected_border):
        errors.append(f"{sheet_name}: Header cột {column} sai border Gate 0")
    if not _alignment_matches(cell.alignment, ALIGN_CENTER):
        errors.append(f"{sheet_name}: Header cột {column} sai alignment Gate 0")


def _validate_primary_data_style(ws, row_idx, column, errors):
    cell = ws.cell(row=row_idx, column=column)
    if cell.value is None:
        return
    if cell.font.name != FONT_FAMILY:
        errors.append(f"{ws.title}: Dòng {row_idx} cột {column} sai font Gate 0")
    if not _border_matches(cell.border, BORDER_DATA):
        errors.append(f"{ws.title}: Dòng {row_idx} cột {column} sai border Gate 0")
    if not _alignment_matches(cell.alignment, _data_alignment_for_column(ws.title, column)):
        errors.append(f"{ws.title}: Dòng {row_idx} cột {column} sai alignment Gate 0")

    numeric_columns = {
        "BOQ": {4},
        "Takeoff_Calculation": {9},
    }
    if (
        column in numeric_columns.get(ws.title, set())
        and isinstance(cell.value, Real)
        and not isinstance(cell.value, bool)
    ):
        if cell.number_format != "#,##0.00":
            errors.append(f"{ws.title}: Dòng {row_idx} cột {column} sai number format Gate 0")
        if not cell.font.bold:
            errors.append(f"{ws.title}: Dòng {row_idx} cột {column} phải in đậm Gate 0")

    formula_columns = {
        "BOQ": {5},
        "Takeoff_Calculation": {6, 7},
        "RFI_Kien_Nghi_Bo_Sung": {5, 7},
    }
    if column in formula_columns.get(ws.title, set()) and not cell.font.italic:
        errors.append(f"{ws.title}: Dòng {row_idx} cột {column} phải italic Gate 0")


def _validate_gate_zero_layout(wb):
    errors = []
    unexpected_sheets = [sheet_name for sheet_name in wb.sheetnames if sheet_name not in SHEET_LAYOUTS]
    if unexpected_sheets:
        errors.append("Workbook có sheet ngoài phạm vi phát hành: " + ", ".join(unexpected_sheets))
    for sheet_name, (headers, widths) in SHEET_LAYOUTS.items():
        if sheet_name not in wb.sheetnames:
            errors.append(f"Thiếu sheet bắt buộc: {sheet_name}")
            continue

        ws = wb[sheet_name]
        actual_headers = [ws.cell(row=5, column=column).value for column in range(1, len(headers) + 1)]
        if actual_headers != headers:
            errors.append(f"{sheet_name}: Header dòng 5 không đúng chuẩn Gate 0")
        if ws.views.sheetView[0].showGridLines is not False:
            errors.append(f"{sheet_name}: Chưa tắt gridline theo chuẩn Gate 0")

        for column, expected_width in widths.items():
            if ws.column_dimensions[column].width != expected_width:
                errors.append(f"{sheet_name}: Độ rộng cột {column} không đúng chuẩn Gate 0")

        for column in range(1, len(headers) + 1):
            _validate_header_cell(sheet_name, column, ws.cell(row=5, column=column), errors)
        if ws.row_dimensions[5].height != HEIGHT_HEADER:
            errors.append(f"{sheet_name}: Header row height không đúng chuẩn Gate 0")

        for row_idx in _data_rows(ws):
            if _is_merged_data_row(ws, row_idx):
                continue
            if (ws.row_dimensions[row_idx].height or 0) < MIN_DATA_ROW_HEIGHT:
                errors.append(f"{sheet_name}: Dòng {row_idx} chưa AutoFit đạt chiều cao tối thiểu Gate 0")
            for column in range(1, len(headers) + 1):
                _validate_primary_data_style(ws, row_idx, column, errors)

    calculation = wb["Takeoff_Calculation"] if "Takeoff_Calculation" in wb.sheetnames else None
    if calculation and (
        EARTHWORK_BALANCE_TABLE_NAME in calculation.tables
        or calculation.cell(row=5, column=EARTHWORK_BALANCE_START_COLUMN).value is not None
    ):
        actual_headers = [
            calculation.cell(row=5, column=EARTHWORK_BALANCE_START_COLUMN + offset).value
            for offset in range(len(HEADERS_EARTHWORK_BALANCE))
        ]
        if actual_headers != HEADERS_EARTHWORK_BALANCE:
            errors.append("Earthwork_Balance: Header không đúng chuẩn Gate 0")
        for offset in range(len(HEADERS_EARTHWORK_BALANCE)):
            _validate_header_cell(
                "Takeoff_Calculation",
                EARTHWORK_BALANCE_START_COLUMN + offset,
                calculation.cell(row=5, column=EARTHWORK_BALANCE_START_COLUMN + offset),
                errors,
            )
        for column, expected_width in WIDTHS_EARTHWORK_BALANCE.items():
            if calculation.column_dimensions[column].width != expected_width:
                errors.append(f"Earthwork_Balance: Độ rộng cột {column} không đúng chuẩn Gate 0")
    return errors


def _normalize_unit(value):
    return str(value or "").strip().casefold().replace("²", "2").replace("³", "3")


def _parse_iso_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_drawing_revision(value):
    match = re.match(
        r"^\s*(?P<drawing>.+?)\s+(?:REV(?:ISION)?\.?\s*)(?P<revision>[A-Za-z0-9._-]+)\s*$",
        str(value or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return match.group("drawing").strip().upper(), _normalize_revision(match.group("revision"))


def _normalize_revision(value):
    return re.sub(r"^REV(?:ISION)?\.?", "", str(value or "").strip().upper())


def _normalize_document_register(document_register):
    if not document_register:
        return None
    items = document_register.items() if hasattr(document_register, "items") else document_register
    normalized = {}
    try:
        for drawing, revision in items:
            drawing_key = str(drawing).strip().upper()
            revision_value = _normalize_revision(revision)
            if drawing_key and revision_value:
                normalized[drawing_key] = revision_value
    except (TypeError, ValueError):
        return None
    return normalized or None


def _extract_tag(value, tag_name):
    match = re.search(
        rf"\b{re.escape(tag_name)}\s*=\s*([A-Z_]+)\b",
        str(value or "").upper(),
    )
    return match.group(1) if match else None


def _parse_rfi_owner_status_due(value):
    fields = {}
    for segment in str(value or "").split(";"):
        key, separator, field_value = segment.partition("=")
        if separator:
            fields[key.strip().casefold()] = field_value.strip()
    owner = fields.get("owner")
    status = fields.get("status")
    due_date = _parse_iso_date(fields.get("due"))
    return owner, status, due_date


def _quantities_match(left, right):
    return abs(float(left) - float(right)) <= QUANTITY_RECONCILIATION_TOLERANCE


def _calc_ids_from_text(value):
    return list(dict.fromkeys(re.findall(r"\bCAL-[A-Z0-9-]+\b", str(value or "").upper())))


def _validate_boq_formula_summary(row_idx, formula_summary, errors):
    formula_text = str(formula_summary or "")
    required_fields = {
        "Location": r"\bLOCATION\s*=\s*[^;]+",
        "Geometry": r"\bGEOMETRY\s*=\s*[^;]*\d",
        "Deductions": r"\bDEDUCTIONS\s*=\s*[^;]+",
        "Calc ID": r"\bCALC\s+ID\s*=\s*CAL-[A-Z0-9-]+",
    }
    for label, pattern in required_fields.items():
        if not re.search(pattern, formula_text, flags=re.IGNORECASE):
            errors.append(f"BOQ dòng {row_idx}: Cột E thiếu trường {label} theo chuẩn kiểm tra nhanh")


def _validate_earthwork_balance(calculation, calculation_records_by_id):
    errors = []
    tagged_records = [
        record
        for records in calculation_records_by_id.values()
        for record in records
        if record["earthwork_state"]
    ]
    if not tagged_records:
        return errors
    if EARTHWORK_BALANCE_TABLE_NAME not in calculation.tables:
        return ["Takeoff_Calculation: Có EARTHWORK_STATE nhưng thiếu bảng Earthwork_Balance"]

    table = calculation.tables[EARTHWORK_BALANCE_TABLE_NAME]
    min_column, min_row, max_column, max_row = range_boundaries(table.ref)
    if min_column != EARTHWORK_BALANCE_START_COLUMN or max_column - min_column + 1 != len(HEADERS_EARTHWORK_BALANCE):
        return ["Earthwork_Balance: Vùng bảng không đúng cấu trúc chuẩn"]
    actual_headers = [calculation.cell(row=min_row, column=column).value for column in range(min_column, max_column + 1)]
    if actual_headers != HEADERS_EARTHWORK_BALANCE:
        return ["Earthwork_Balance: Header không đúng cấu trúc chuẩn"]

    balance_rows = []
    calc_to_balance_row = {}
    for row_idx in range(min_row + 1, max_row + 1):
        values = [calculation.cell(row=row_idx, column=column).value for column in range(min_column, max_column + 1)]
        if not any(value is not None for value in values):
            continue
        wbs_location, drawing_revision, source_ids, unit, *state_values, notes = values
        if not all([wbs_location, drawing_revision, source_ids, unit, notes]):
            errors.append(f"Earthwork_Balance dòng {row_idx}: Thiếu WBS/vị trí, revision, Calc ID, ĐVT hoặc cơ sở cân bằng")
            continue
        if _normalize_unit(unit) != "m3":
            errors.append(f"Earthwork_Balance dòng {row_idx}: ĐVT phải là m3")
        calc_ids = _calc_ids_from_text(source_ids)
        if not calc_ids:
            errors.append(f"Earthwork_Balance dòng {row_idx}: Thiếu Calc ID nguồn hợp lệ")
            continue
        state_values_by_state = {
            state: state_values[column - 5]
            for state, column in EARTHWORK_STATE_TO_BALANCE_COLUMN.items()
        }
        row_record = {
            "row_idx": row_idx,
            "calc_ids": calc_ids,
            "unit": _normalize_unit(unit),
            "state_values": state_values_by_state,
        }
        balance_rows.append(row_record)
        for calc_id in calc_ids:
            if calc_id in calc_to_balance_row:
                errors.append(f"Earthwork_Balance dòng {row_idx}: {calc_id} bị lặp ở nhiều dòng cân bằng")
            calc_to_balance_row[calc_id] = row_record

    for row_record in balance_rows:
        records_by_state = defaultdict(list)
        for calc_id in row_record["calc_ids"]:
            if calc_id not in calculation_records_by_id:
                errors.append(f"Earthwork_Balance dòng {row_record['row_idx']}: Không tìm thấy {calc_id}")
                continue
            for record in calculation_records_by_id[calc_id]:
                if record["earthwork_state"]:
                    records_by_state[record["earthwork_state"]].append(record)
        for state, records in records_by_state.items():
            entered_qty = row_record["state_values"][state]
            if not isinstance(entered_qty, Real) or isinstance(entered_qty, bool):
                errors.append(f"Earthwork_Balance dòng {row_record['row_idx']}: {state} phải là số")
                continue
            expected_qty = sum(record["qty"] for record in records)
            if not _quantities_match(entered_qty, expected_qty):
                errors.append(
                    f"Earthwork_Balance dòng {row_record['row_idx']}: {state} không khớp tổng Calc ID nguồn"
                )

    for record in tagged_records:
        balance_row = calc_to_balance_row.get(record["calc_id"])
        if not balance_row:
            errors.append(
                f"Takeoff_Calculation dòng {record['row_idx']}: {record['calc_id']} chưa có trong Earthwork_Balance"
            )
        elif balance_row["unit"] != _normalize_unit(record["unit"]):
            errors.append(
                f"Earthwork_Balance dòng {balance_row['row_idx']}: ĐVT không khớp {record['calc_id']}"
            )
    return errors


def _validate_release_data(wb, document_register=None):
    errors = []
    boq = wb["BOQ"]
    calculation = wb["Takeoff_Calculation"]
    rfi = wb["RFI_Kien_Nghi_Bo_Sung"]
    qa = wb["QA_Audit"]
    valid_units = {"m", "m2", "m3", "kg", "tấn", "t", "cái", "nos", "bộ", "set", "lot"}
    normalized_register = _normalize_document_register(document_register)
    if any(True for _ in _data_rows(calculation)) and not normalized_register:
        errors.append("Takeoff_Calculation: Thiếu Document Register để xác nhận revision mới nhất")

    calculation_records_by_id = defaultdict(list)
    for row_idx in _data_rows(calculation):
        calc_id = calculation.cell(row=row_idx, column=1).value
        boq_wbs = calculation.cell(row=row_idx, column=2).value
        location_element = calculation.cell(row=row_idx, column=3).value
        drawing_revision = calculation.cell(row=row_idx, column=4).value
        source_view_detail = calculation.cell(row=row_idx, column=5).value
        measurement_formula = calculation.cell(row=row_idx, column=6).value
        deductions_measurement_basis = calculation.cell(row=row_idx, column=7).value
        unit = calculation.cell(row=row_idx, column=8).value
        qty = calculation.cell(row=row_idx, column=9).value
        data_status = calculation.cell(row=row_idx, column=10).value
        checker = calculation.cell(row=row_idx, column=11).value
        remarks = calculation.cell(row=row_idx, column=12).value

        if not all([
            calc_id,
            boq_wbs,
            location_element,
            drawing_revision,
            source_view_detail,
            measurement_formula,
            deductions_measurement_basis,
            unit,
            qty is not None,
            data_status,
            checker,
            remarks,
        ]):
            errors.append(f"Takeoff_Calculation dòng {row_idx}: Thiếu dữ liệu truy vết bắt buộc")
            continue
        normalized_unit = _normalize_unit(unit)
        if normalized_unit not in valid_units:
            errors.append(f"Takeoff_Calculation dòng {row_idx}: Đơn vị không hợp lệ ({unit})")
        if not isinstance(qty, Real) or isinstance(qty, bool):
            errors.append(f"Takeoff_Calculation dòng {row_idx}: Khối lượng phải là số")
            continue
        status = str(data_status).strip()
        if status not in CALC_VALID_STATUSES:
            errors.append(f"Takeoff_Calculation dòng {row_idx}: Trạng thái dữ liệu không hợp lệ ({data_status})")
        quantity_class = _extract_tag(remarks, "QUANTITY CLASS")
        if quantity_class not in QUANTITY_CLASSES:
            errors.append(
                f"Takeoff_Calculation dòng {row_idx}: Thiếu Quantity Class=NET_DESIGN hoặc PROCUREMENT_ONLY"
            )
        earthwork_state = _extract_tag(remarks, "EARTHWORK_STATE")
        if "EARTHWORK_STATE" in str(remarks).upper() and earthwork_state not in EARTHWORK_STATES:
            errors.append(f"Takeoff_Calculation dòng {row_idx}: EARTHWORK_STATE không hợp lệ")
        schedule_marker = _schedule_reference_without_geometry(measurement_formula)
        if schedule_marker:
            errors.append(
                f"Takeoff_Calculation dòng {row_idx}: {schedule_marker} không thay thế công thức hình học độc lập"
            )
        parsed_drawing_revision = _parse_drawing_revision(drawing_revision)
        if not parsed_drawing_revision:
            errors.append(f"Takeoff_Calculation dòng {row_idx}: Bản vẽ & Revision không đúng định dạng")
        elif normalized_register:
            drawing, revision = parsed_drawing_revision
            registered_revision = normalized_register.get(drawing)
            if not registered_revision:
                errors.append(f"Takeoff_Calculation dòng {row_idx}: {drawing} không có trong Document Register")
            elif revision != registered_revision:
                errors.append(
                    f"Takeoff_Calculation dòng {row_idx}: Revision mới nhất không khớp Document Register ({revision} != {registered_revision})"
                )
        calculation_records_by_id[str(calc_id).strip().upper()].append({
            "row_idx": row_idx,
            "calc_id": str(calc_id).strip().upper(),
            "wbs": str(boq_wbs).strip(),
            "unit": normalized_unit,
            "qty": float(qty),
            "status": status,
            "quantity_class": quantity_class,
            "earthwork_state": earthwork_state,
        })

    calc_id_to_boq_wbs = {}
    for row_idx in _data_rows(boq):
        wbs = boq.cell(row=row_idx, column=1).value
        unit = boq.cell(row=row_idx, column=3).value
        qty = boq.cell(row=row_idx, column=4).value
        formula_summary = boq.cell(row=row_idx, column=5).value
        if wbs and qty is not None and not formula_summary:
            errors.append(f"BOQ dòng {row_idx}: Thiếu công thức tóm tắt tại cột E")
        if wbs and qty is not None:
            _validate_boq_formula_summary(row_idx, formula_summary, errors)
        normalized_boq_unit = _normalize_unit(unit)
        if wbs and qty is not None and normalized_boq_unit not in valid_units:
            errors.append(f"BOQ dòng {row_idx}: ĐVT không hợp lệ ({unit})")
        if wbs and qty is not None and (not isinstance(qty, Real) or isinstance(qty, bool)):
            errors.append(f"BOQ dòng {row_idx}: Khối lượng cột D phải là số")
        schedule_marker = _schedule_reference_without_geometry(formula_summary)
        if schedule_marker:
            errors.append(
                f"BOQ dòng {row_idx}: {schedule_marker} không thay thế công thức hình học độc lập"
            )
        calc_ids = _calc_ids_from_text(formula_summary)
        if wbs and qty is not None and not calc_ids:
            errors.append(f"BOQ dòng {row_idx}: Thiếu Calc ID để xác nhận trạng thái Verified")
        calculation_total = 0.0
        for calc_id in calc_ids:
            records = calculation_records_by_id.get(calc_id, [])
            if not records:
                errors.append(f"BOQ dòng {row_idx}: Không tìm thấy {calc_id} trong Takeoff_Calculation")
                continue
            if calc_id in calc_id_to_boq_wbs and calc_id_to_boq_wbs[calc_id] != str(wbs).strip():
                errors.append(f"BOQ dòng {row_idx}: {calc_id} không được dùng cho nhiều WBS")
            calc_id_to_boq_wbs[calc_id] = str(wbs).strip()
            for record in records:
                if record["status"] != "Verified":
                    errors.append(f"BOQ dòng {row_idx}: {calc_id} chưa ở trạng thái Verified")
                if record["wbs"] != str(wbs).strip():
                    errors.append(f"BOQ dòng {row_idx}: WBS của {calc_id} không khớp BOQ")
                if record["unit"] != normalized_boq_unit:
                    errors.append(f"BOQ dòng {row_idx}: ĐVT của {calc_id} không khớp BOQ")
                if record["quantity_class"] == "PROCUREMENT_ONLY":
                    errors.append(f"BOQ dòng {row_idx}: {calc_id} là PROCUREMENT_ONLY, không được cộng vào BOQ.D")
                elif record["quantity_class"] != "NET_DESIGN":
                    errors.append(f"BOQ dòng {row_idx}: {calc_id} không có Quantity Class=NET_DESIGN hợp lệ")
                calculation_total += record["qty"]
        if calc_ids and isinstance(qty, Real) and not isinstance(qty, bool) and not _quantities_match(qty, calculation_total):
            errors.append(
                f"BOQ dòng {row_idx}: Khối lượng cột D không khớp tổng khối lượng Calculation ({qty} != {calculation_total})"
            )

    for row_idx in _data_rows(rfi):
        if any(
            value is None or not str(value).strip()
            for value in (rfi.cell(row=row_idx, column=column).value for column in range(1, 9))
        ):
            errors.append(f"RFI dòng {row_idx}: Thiếu dữ liệu bắt buộc trong biểu mẫu RFI 8 cột")
            continue
        owner, rfi_status, due_date = _parse_rfi_owner_status_due(rfi.cell(row=row_idx, column=8).value)
        if not owner or not rfi_status or not due_date:
            errors.append(
                f"RFI dòng {row_idx}: Cột H phải theo Owner=<tên>; Status=<trạng thái>; Due=YYYY-MM-DD"
            )
            continue
        if rfi_status not in RFI_VALID_STATUSES:
            errors.append(f"RFI dòng {row_idx}: Trạng thái không hợp lệ ({rfi_status})")
        elif rfi_status not in RFI_RELEASED_STATUSES:
            errors.append(f"RFI dòng {row_idx}: {rfi_status} chưa xử lý, không thể phát hành BOQ")

    effective_qa_statuses = {}
    for row_idx in _data_rows(qa):
        if any(
            value is None or not str(value).strip()
            for value in (qa.cell(row=row_idx, column=column).value for column in range(1, 10))
        ):
            errors.append(f"QA_Audit dòng {row_idx}: Thiếu dữ liệu bắt buộc trong biểu mẫu QA 9 cột")
            continue
        gate = str(qa.cell(row=row_idx, column=1).value or "").strip()
        target = str(qa.cell(row=row_idx, column=3).value or "").strip()
        status = str(qa.cell(row=row_idx, column=8).value or "").strip()
        audit_date = _parse_iso_date(qa.cell(row=row_idx, column=9).value)
        if gate not in REQUIRED_GATES:
            errors.append(f"QA_Audit dòng {row_idx}: Gate không hợp lệ ({gate})")
            continue
        if status not in QA_VALID_STATUSES:
            errors.append(f"QA_Audit dòng {row_idx}: Trạng thái không hợp lệ ({status})")
            continue
        if not target or not audit_date:
            errors.append(f"QA_Audit dòng {row_idx}: Thiếu đối tượng hoặc ngày kiểm tra ISO")
            continue
        key = (gate, target)
        current = effective_qa_statuses.get(key)
        candidate = (audit_date, row_idx, status)
        if not current or candidate[:2] >= current[:2]:
            effective_qa_statuses[key] = candidate

    passed_gates = set()
    for (gate, _target), (_audit_date, _row_idx, status) in effective_qa_statuses.items():
        if status in {"Open", "RFI Required"}:
            errors.append(f"QA_Audit: {gate} còn trạng thái {status}, không thể phát hành")
        if status == "Pass":
            passed_gates.add(gate)
    for gate in REQUIRED_GATES:
        if gate not in passed_gates:
            errors.append(f"QA_Audit: {gate} chưa có trạng thái Pass hiệu lực")

    errors.extend(_validate_earthwork_balance(calculation, calculation_records_by_id))

    return errors


def validate_release_readiness(wb, document_register=None):
    """Kiểm tra Gate 0 và điều kiện phát hành của Gate 1–4."""
    errors = _validate_gate_zero_layout(wb)
    if not errors:
        errors.extend(_validate_release_data(wb, document_register=document_register))
    return ValidationResult(passed=not errors, errors=tuple(errors))


# ==============================================================================
# 4. HÀM TỰ ĐỘNG AUTOFIT CHIỀU CAO DÒNG (AUTOFIT ROW HEIGHT)
# ==============================================================================
def autofit_workbook_rows(file_path, use_excel_com=False):
    """
    Tự động thực thi AutoFit Row Height cho toàn bộ file Excel đã lưu:
    - Giữ nguyên chiều cao chuẩn của Khối Tiêu đề (Row 1-4), Header (Row 5), Phân mục Level 1 (28pt), Tiểu mục Level 2 (24pt).
    - Tự động AutoFit 100% dòng dữ liệu (Data Rows) theo đúng thuật toán font rendering của Excel, đảm bảo không bao giờ bị cắt cụt văn bản tam ngữ hay công thức dài.
    - Thiết lập chiều cao tối thiểu MIN_DATA_ROW_HEIGHT (28pt) để bảng không bị co rúm đối với các dòng ngắn.
    - Hỗ trợ cả Microsoft Excel COM (win32com) lẫn Fallback tính toán thuần Python khi chạy môi trường không có Office COM.
    """
    abs_path = os.path.abspath(file_path)

    def python_autofit():
        try:
            import openpyxl

            wb_ox = openpyxl.load_workbook(abs_path)
            text_columns_by_sheet = {
                "BOQ": (2, 5),
                "Takeoff_Calculation": (3, 5, 6, 7, 12, 14, 15, 16, 24),
                "RFI_Kien_Nghi_Bo_Sung": (2, 3, 4, 5, 6, 7, 8),
                "QA_Audit": (1, 2, 3, 5, 6, 7, 8, 9),
            }
            for ws in wb_ox.worksheets:
                text_columns = text_columns_by_sheet.get(ws.title, (2, 5))
                for r in range(6, ws.max_row + 1):
                    cell_a = ws.cell(row=r, column=1)
                    is_merged = any(cell_a.coordinate in rng for rng in ws.merged_cells.ranges)
                    if not is_merged:
                        def count_lines(text, max_chars=55):
                            total = 0
                            for para in str(text).split("\n"):
                                total += max(1, (len(para) + max_chars - 1) // max_chars)
                            return max(1, total)

                        lines = max(
                            count_lines(ws.cell(row=r, column=column).value or "")
                            for column in text_columns
                        )
                        ws.row_dimensions[r].height = max(MIN_DATA_ROW_HEIGHT, lines * 15.0 + 8.0)
            wb_ox.save(abs_path)
            return True
        except Exception:
            return False

    if not use_excel_com:
        return python_autofit()

    # 1. Thử thực thi bằng Excel COM (chính xác tuyệt đối 100% trên Windows)
    try:
        import win32com.client
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        try:
            wb_xl = excel.Workbooks.Open(abs_path)
            for ws_xl in wb_xl.Sheets:
                max_r = ws_xl.UsedRange.Rows.Count
                for r in range(6, max_r + 1):
                    cell_a = ws_xl.Cells(r, 1)
                    if cell_a.MergeCells:
                        val = str(cell_a.Value or "")
                        if any(val.startswith(kw) for kw in ["PHẦN", "PART", "第", "I.", "II.", "III.", "IV."]):
                            ws_xl.Rows(r).RowHeight = HEIGHT_LEVEL1 if ("PHẦN" in val or "PART" in val or "第" in val) else HEIGHT_LEVEL2
                        else:
                            ws_xl.Rows(r).RowHeight = HEIGHT_LEVEL2
                    else:
                        ws_xl.Rows(r).AutoFit()
                        if ws_xl.Rows(r).RowHeight < MIN_DATA_ROW_HEIGHT and ws_xl.Cells(r, 2).Value:
                            ws_xl.Rows(r).RowHeight = MIN_DATA_ROW_HEIGHT
                
                # Bảo toàn chiều cao hàng Tiêu đề và Header Row 5
                ws_xl.Rows(1).RowHeight = HEIGHT_TITLE_1
                ws_xl.Rows(2).RowHeight = HEIGHT_TITLE_2
                ws_xl.Rows(3).RowHeight = HEIGHT_TITLE_3
                ws_xl.Rows(4).RowHeight = HEIGHT_BLANK_GAP
                ws_xl.Rows(5).RowHeight = HEIGHT_HEADER
                
            wb_xl.Save()
            wb_xl.Close()
            return True
        finally:
            excel.Quit()
    except Exception:
        pass

    # 2. Fallback tự động tính toán qua openpyxl nếu Excel COM không khả dụng
    return python_autofit()


def save_and_autofit_workbook(wb, file_path, document_register=None):
    """
    Hàm tương thích ngược; dùng luồng lưu–kiểm tra chuẩn Gate 0–4.
    """
    return save_and_validate_csa_workbook(wb, file_path, document_register=document_register)


def save_and_validate_csa_workbook(wb, file_path, document_register=None):
    """Chuẩn hóa layout, kiểm tra điều kiện phát hành rồi lưu workbook chính thức."""
    finalize_workbook_layout(wb)
    result = validate_release_readiness(wb, document_register=document_register)
    if not result.passed:
        raise ValueError("Không thể phát hành BOQ:\n- " + "\n- ".join(result.errors))

    wb.save(file_path)
    if not autofit_workbook_rows(file_path):
        raise RuntimeError("Không thể AutoFit workbook sau khi lưu")
    saved_workbook = openpyxl.load_workbook(file_path)
    post_autofit_result = validate_release_readiness(
        saved_workbook, document_register=document_register
    )
    if not post_autofit_result.passed:
        raise RuntimeError(
            "Workbook không đạt Gate 0–4 sau AutoFit:\n- "
            + "\n- ".join(post_autofit_result.errors)
        )
    return post_autofit_result
