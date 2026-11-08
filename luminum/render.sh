#!/bin/sh
# Render the deck with LibreOffice and blend it over the scan for checking.
set -e
cd "$(dirname "$0")/build"
rm -f LuMiNum_CarbideLamps.pdf
timeout 180 soffice --headless --convert-to pdf LuMiNum_CarbideLamps.pptx >/dev/null 2>&1
pdftoppm -r 204.27 -png -singlefile LuMiNum_CarbideLamps.pdf render
