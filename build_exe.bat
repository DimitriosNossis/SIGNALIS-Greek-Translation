@echo off
rem Builds dist\SIGNALIS-Greek-Patcher.exe
rem Needs: pip install -r requirements.txt pyinstaller
python -m PyInstaller --onefile --console --name SIGNALIS-Greek-Patcher ^
  --add-data "translation;translation" ^
  --collect-all UnityPy ^
  --collect-all fmod_toolkit ^
  --collect-all pyfmodex ^
  --collect-all texture2ddecoder ^
  --collect-all etcpak ^
  --collect-all astc_encoder ^
  --collect-all archspec ^
  patch.py
