#!/bin/bash
# ============================================================
# 论文编译脚本 (Linux/macOS)
# Compile Thesis Script for Linux/macOS
# ============================================================

echo "========================================="
echo "Compiling Thesis: Polar Route Planning and 3D Reconstruction"
echo "========================================="
echo

cd "$(dirname "$0")"

# Check if pdflatex exists
if ! command -v pdflatex &> /dev/null; then
    echo "ERROR: pdflatex not found. Please install TeX Live."
    exit 1
fi

# Check if biber exists
if ! command -v biber &> /dev/null; then
    echo "ERROR: biber not found. Please install TeX Live."
    exit 1
fi

echo "Step 1: First pdflatex pass..."
pdflatex -interaction=nonstopmode main.tex || { echo "ERROR: First pdflatex pass failed."; exit 1; }

echo "Step 2: Running biber..."
biber main || { echo "ERROR: Biber failed."; exit 1; }

echo "Step 3: Second pdflatex pass..."
pdflatex -interaction=nonstopmode main.tex || { echo "ERROR: Second pdflatex pass failed."; exit 1; }

echo "Step 4: Final pdflatex pass..."
pdflatex -interaction=nonstopmode main.tex || { echo "ERROR: Final pdflatex pass failed."; exit 1; }

echo
echo "========================================="
echo "Compilation successful!"
echo "Output: main.pdf"
echo "========================================="

# Move PDF to out directory
mkdir -p out
cp main.pdf out/thesis.pdf
echo "PDF copied to: out/thesis.pdf"
