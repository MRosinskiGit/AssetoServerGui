import sys

from PySide6.QtWidgets import QApplication

from ac_server_gui.core.config import load_config
from ac_server_gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("AC Server GUI")
    config = load_config()
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
