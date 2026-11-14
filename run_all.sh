#!/usr/bin/env bash
# Rebuild everything from scratch. Needs Python 3 with pandas, numpy, matplotlib, openpyxl.
set -e
python3 src/generate_data.py
python3 src/pipeline.py
python3 src/charts.py
python3 src/build_workbook.py
