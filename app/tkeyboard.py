from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from generated_scripts.tkeyboard_gui import Ui_tkeyboard_widget

import keyboard 
import ctypes

User32 = ctypes.WinDLL('User32.dll')

symbols_to_shift = [
    "!", "@", "#", "$", "%", "^", "&", "*", "(", ")",
    "_", "~", "{", "}", "|", '"', ":", "?", "<", ">"
]

class App(QtWidgets.QMainWindow):
    def __init__(self):
        super(App, self).__init__()

        # The actual window
        self.ui = Ui_tkeyboard_widget()
        self.ui.setupUi(self)
        self.set_window_focus()
        
        self.show()

    def set_window_focus(self):
        # Prevents the window from hiding even if another gui is focused     
        self.setWindowFlags(Qt.WindowType.WindowDoesNotAcceptFocus | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.WindowMinimizeButtonHint |
                            Qt.WindowType.WindowCloseButtonHint
                            )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        User32.SetWindowLongW(int(self.winId()), -20, 134217728)

    def capture_pressed_keys(self):
        # Gets every keyboard button then checks if each button was clicked
        for btn in self.findChildren(QtWidgets.QPushButton):
            btn.clicked.connect(lambda: self.press_selected_key())

    def press_selected_key(self):
        # Presses the selected key to an input field.
        widget = self.sender()
        key = widget.text()
        if key == "&&":
            keyboard.press_and_release("&")
        elif key in symbols_to_shift:
            keyboard.press_and_release(f"shift+{key}")
        else:
            keyboard.press_and_release(key)