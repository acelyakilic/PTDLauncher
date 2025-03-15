pip install pillow pygame pygetwindow requests

pyinstaller --onefile --windowed --icon=resources/1.ico --add-data "resources/1.ico;resources" --add-data "resources/2.ico;resources" --add-data "resources/top.png;resources" --add-data "resources/settings.png;resources" --add-data "resources/update.png;resources" --add-data "resources/config.json;resources" --add-data "resources/Closetab.mp3;resources" --add-data "resources/mewtab.mp3;resources" --add-data "resources/off.mp3;resources" --add-data "resources/on.mp3;resources" "PTDLauncher.py"
