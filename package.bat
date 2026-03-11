@echo off
pushd "%~dp0"

echo Cleaning up...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist CryptoTool.spec del CryptoTool.spec

echo Building with hidden console...
:: Added --windowed flag to hide the command prompt window
pyinstaller --noconfirm --onefile --windowed --name "CryptoTool" --collect-all "cryptography" --collect-all "PyQt6" main.py

echo Build finished.
pause
popd
公测版