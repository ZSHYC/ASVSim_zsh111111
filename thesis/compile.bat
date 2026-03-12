@echo off
REM ============================================================
REM 论文编译脚本 (Windows) - 修复版
REM Compile Thesis Script for Windows (Fixed)
REM ============================================================

echo =========================================
echo Compiling Thesis: Polar Route Planning and 3D Reconstruction
echo =========================================
echo.

cd /d "C:\Users\zsh\Desktop\ASVSim_zsh\thesis"

REM Check if pdflatex exists
where pdflatex >nul 2>&1
if errorlevel 1 (
    echo ERROR: pdflatex not found. Please install MiKTeX or TeX Live.
    exit /b 1
)

REM Check if biber exists
where biber >nul 2>&1
if errorlevel 1 (
    echo ERROR: biber not found. Please install MiKTeX or TeX Live.
    exit /b 1
)

echo Step 1: First pdflatex pass...
pdflatex -interaction=nonstopmode main.tex
if not exist main.pdf (
    echo ERROR: First pdflatex pass failed - no PDF generated.
    exit /b 1
)

echo Step 2: Running biber...
biber main
REM Biber warnings are OK, continue regardless

echo Step 3: Second pdflatex pass...
pdflatex -interaction=nonstopmode main.tex

echo Step 4: Final pdflatex pass...
pdflatex -interaction=nonstopmode main.tex

echo.
echo =========================================
echo Compilation successful!
echo Output: main.pdf
echo =========================================

REM Move PDF to out directory
if not exist out mkdir out
copy main.pdf out\thesis.pdf >nul
echo PDF copied to: out\thesis.pdf

REM Show PDF info
for %%I in (main.pdf) do (
    echo File size: %%~zI bytes
)
