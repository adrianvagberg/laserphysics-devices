# Menlo THz TDS GUI
A Python GUI made to analyze THz Time-Domain Spectroscopy data collected by the Menlo Tera K15 system.

## Run from IDE or as stand-alone .exe
You may run the GUI by running the `THz_TDS_GUI.py` file from your IDE after installing all required packages, or by using `pyinstaller` to create a stand-alone .exe file that can be run from anywhere: 
```bash
  pip3 install pyinstaller
  pyinstaller THz_TDS_GUI.spec  
```
The .exe file will end up in `/dist/THz TDS GUI.exe` and can be copied to the Desktop, or distributed to a lab computer on a USB-drive.

With the .exe file, Python does not need to be installed on that computer. The programs runs like any other Windows application.