@echo off
chcp 65001 >nul
echo ===============================================================================
echo     CAI DAT MOI TRUONG RUNTIME CHO HE SINH THAI CSA TAKEOFF SUITE
echo ===============================================================================
echo.

:: 1. Kiem tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren he thong!
    echo Vui long cai dat Python 3.10 tro len tai: https://www.python.org/downloads/
    echo LUU Y: Khi cai dat, nho tich vao o "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [OK] Da tim thay Python:
python --version
echo.

:: 2. Nang cap pip
echo [1/2] Dang kiem tra va cap nhat pip...
python -m pip install --upgrade pip --quiet

:: 3. Cai dat cac thu vien can thiet
echo [2/2] Dang cai dat cac thu vien Python can thiet cho CSA Takeoff Suite:
echo       - openpyxl (Xu ly dinh dang Excel BOQ 4-Sheet & AutoFit)
echo       - ezdxf    (Doc va trich xuat du lieu vector ban ve CAD .dxf)
echo       - pymupdf  (Doc va trich xuat van ban ban ve PDF)
echo       - matplotlib, pillow (Xu ly anh va do thi)
echo.

python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [CANH BAO] Co loi khi cai dat tu requirements.txt. Dang thu cai truc tiep...
    python -m pip install openpyxl ezdxf pymupdf matplotlib pillow
)

echo.
echo ===============================================================================
echo [THANH CONG] Moi truong Python da san sang cho He sinh thai CSA Takeoff Suite!
echo ===============================================================================
echo.
pause
