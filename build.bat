pip install pillow pygame pygetwindow requests

pyinstaller --onefile --windowed --icon=resources/favicon.ico --add-data "resources/favicon.ico;resources" --add-data "resources/favicon-flash.ico;resources" --add-data "resources/top.png;resources" --add-data "resources/settings.png;resources" --add-data "resources/update.png;resources" --add-data "resources/config.json;resources" --add-data "resources/closetab.mp3;resources" --add-data "resources/opentab.mp3;resources" --add-data "resources/off.mp3;resources" --add-data "resources/on.mp3;resources" "PTDLauncher.py"
