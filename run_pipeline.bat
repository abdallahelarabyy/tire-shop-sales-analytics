@echo off
rem Rebuild everything from data/raw: clean data, notebook, documents and the PDF guide.
setlocal
cd /d "%~dp0"
if not defined PYTHON set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"

echo [1/4] Cleaning...
"%PYTHON%" cleaning\clean_data.py || goto :fail
echo [2/4] Analysis notebook...
"%PYTHON%" tools\build_notebook.py || goto :fail
"%PYTHON%" -m jupyter nbconvert --to html eda\tire_shop_eda.ipynb >nul 2>&1
echo [3/4] Documents...
"%PYTHON%" tools\build_docs.py || goto :fail
echo [4/4] PDF guide...
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if exist "%EDGE%" "%EDGE%" --headless=new --disable-gpu --no-pdf-header-footer --user-data-dir="%TEMP%\edge-pdf" --print-to-pdf="%CD%\docs\Dashboard_Guide.pdf" "file:///%CD:\=/%/docs/guide/Dashboard_Guide.html"
echo Done. Open dashboard\Tire Shop Sales Dashboard.pbix in Power BI Desktop.
exit /b 0
:fail
echo A step failed - see the message above.
exit /b 1
