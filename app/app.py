# The main program
# This uses the generated "app_gui.py" file from pyuic6 and then hooked with commands from different scripts.
# TODO: Figure out how to update the repository
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMessageBox
from pyjoystick.sdl2 import Joystick, run_event_loop
from generated_scripts.app_gui import Ui_MainWindow

import db_setup as setup
import mapping as mapping
import pyjoystick
import sys
import tkeyboard

db_cmds = setup.DBcmds()
table_cmds = setup.TABLEcmds()

# Prepares the controls for keybind pairing.
controls = mapping.Controls()
controls_dict = controls.get()

# Prepares this generator for receiving controller input/output and for generating its own events.
action_generator = mapping.ActionGenerator(None, controls_dict)
action_generator.start()


def get_preset_num(preset):
    # Helper function, splits preset string into two,
    # Then finds the number of the preset.
    preset_info = preset.split("_")
    preset_num = preset_info[1]
    return preset_num


def create_warning_dialog(text, cmd):
    # Yet another function that creates a warning dialog and runs a command when something happens.
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setText(text)
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Apply)
    selected_btn = msg_box.exec()
    if selected_btn == QMessageBox.StandardButton.Apply:
        cmd()


class App(QtWidgets.QMainWindow):
    def __init__(self):
        super(App, self).__init__()

        # The actual window
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()

        try:
            # Gets keybind_data to bind them to the controls, however if no presets are enabled,
            # the program immediately sets PRESET_1 to True to prevent program crash.
            keybind_data = self.get_keybind_data()
        except TypeError:
            db_cmds.update_data(
                table="presets", column="PRESET_1", data=True, row=1)
            keybind_data = self.get_keybind_data()

        self.bind_keybinds_to_controls()
        self.enable_controls()
        self.list_joysticks()
        self.set_saved_tuning()
        self.populate_mapping_list(
            keybinds=keybind_data[0], preset=keybind_data[1])
        self.set_preset_choices()
        self.set_keybind_editing()
        self.toggle_keybind_editing()

        # Sets the previewing text and in-use text with presets after launch
        self.show_preset_preview()
        self.use_selected_preset()

        # Makes app interactive
        self.connect_cmds()

        # Misc
        self.ui.enable_btn.setChecked(True)
        self.ui.tabWidget.setCurrentIndex(0)

    def connect_cmds(self):
        # Btns
        self.ui.controller_refresh_btn.clicked.connect(self.list_joysticks)
        self.ui.enable_btn.clicked.connect(self.enable_controls)
        self.ui.disable_btn.clicked.connect(self.disable_controls)
        self.ui.mapping_refresh_btn.clicked.connect(self.refresh_mapping_list)
        self.ui.save_tune_btn.clicked.connect(self.save_tuning)
        self.ui.reset_tune_btn.clicked.connect(self.reset_tuning)
        self.ui.use_preset_btn.clicked.connect(self.use_selected_preset)
        self.ui.set_keybind_btn.clicked.connect(self.sync_keybind_to_control)
        self.ui.clear_bind_btn.clicked.connect(self.clear_keybind)
        self.ui.clear_all_binds_btn.clicked.connect(self.clear_all_keybinds)
        self.ui.launch_keyboard_btn.clicked.connect(self.launch_keyboard_widget)
        self.ui.reset_first_preset_btn.clicked.connect(self.reset_first_preset)

        # Btn shortcuts
        self.ui.disable_btn.setShortcut("ctrl+d")
        self.ui.enable_btn.setShortcut("ctrl+e")
        self.ui.launch_keyboard_btn.setShortcut("ctrl+k")

        # Sliders
        self.ui.cursor_speed_slider.valueChanged.connect(
            lambda: self.adjust_tuning_slider(self.ui.cursor_speed_slider))
        self.ui.scroll_speed_slider.valueChanged.connect(
            lambda: self.adjust_tuning_slider(self.ui.scroll_speed_slider))
        self.ui.repeat_speed_slider.valueChanged.connect(
            lambda: self.adjust_tuning_slider(self.ui.repeat_speed_slider))
        self.ui.delay_activation_slider.valueChanged.connect(
            lambda: self.adjust_tuning_slider(self.ui.delay_activation_slider))

        # Line edits/Inputs
        self.ui.cursor_speed_input.textChanged.connect(
            lambda: self.adjust_tuning_entry(self.ui.cursor_speed_input))
        self.ui.scroll_speed_input.textChanged.connect(
            lambda: self.adjust_tuning_entry(self.ui.scroll_speed_input))
        self.ui.repeat_speed_input.textChanged.connect(
            lambda: self.adjust_tuning_entry(self.ui.repeat_speed_input))
        self.ui.delay_activation_input.textChanged.connect(
            lambda: self.adjust_tuning_entry(self.ui.delay_activation_input))

        # Chkbox
        self.ui.repeat_chkbox.clicked.connect(
            self.toggle_repeat_movement_chkbox)

        # Combobox
        self.ui.preset_to_use_list.currentTextChanged.connect(
            self.toggle_keybind_editing)
        self.ui.preset_to_use_list.activated.connect(
            self.show_preset_preview)
        self.ui.edit_control_list.activated.connect(
            self.highlight_mapping_list_cell)

        # Table widget
        self.ui.mapping_list.currentCellChanged.connect(
            self.set_mapping_list_cell)

    def get_keybind_data(self):
        # As the method suggests, it gets the necessary keybinds based from the toggled preset
        self.keybinds_class = mapping.Keybinds()
        self.presets_class = mapping.Presets()
        presets_dict = self.presets_class.get()

        self.controls_data = self.keybinds_class.return_match(presets_dict)
        keybinds = self.controls_data[0]
        current_preset = self.controls_data[1]

        # Then returns data for running the action_generator and visualization.
        return keybinds, current_preset

    def bind_keybinds_to_controls(self):
        # Gets keybinds and matches it with the controls, then returns a dictionary continaing
        # The binded data.
        keybind_data = self.get_keybind_data()
        keybinds = keybind_data[0]
        keybinds_dict = self.keybinds_class.bind(
            controls_dict, keybinds)
        return keybinds_dict

    def enable_controls(self):
        keybinds_dict = self.bind_keybinds_to_controls()
        self.enable = True
        # action_generator uses the keybinds within keybinds_dict to create events.
        action_generator.keybinds = keybinds_dict

    def disable_controls(self):
        self.enable = False
        # Keybinds are set to None to prevent returning movement.
        action_generator.keybinds = None

    def list_joysticks(self):
        self.ui.controllers_list.clear()

        def add_joysticks(joysticks):
            try:
                # Checks for the length of the joystick list.
                # If none, returns a text saying 'No controls found'
                if len(joysticks) <= 0:
                    text = "No controls found. Connect through USB?"
                    self.ui.controllers_list.addItem(text)
                # Else, it iterates through the list and displays them
                else:
                    for joystick in joysticks:
                        controller = joystick.name
                        self.ui.controllers_list.addItem(controller)
            except TypeError:
                # Sometimes a TypeError pops up, and you can't iterate through the supposed "list" of joysticks.
                # Therefore if the data is non-iterable, we don't have to bother counting through the list.
                controller = joysticks.name
                self.ui.controllers_list.addItem(controller)

        # This finds the controllers themselves, then stops after finding them.
        mngr = pyjoystick.ThreadEventManager(
            event_loop=run_event_loop, add_joystick=add_joysticks)
        mngr.start()
        mngr.add_joystick(Joystick.get_joysticks())
        mngr.stop()

    def set_saved_tuning(self):
        """Sets saved tuning data based from "tuning" table."""
        tuning_data = db_cmds.get_all_data("tuning")
        tuning_values = list(tuning_data[0])

        # Toggles repeat_chkbox
        repeat = tuning_values[2]
        if repeat:
            self.ui.repeat_chkbox.setChecked(True)
        else:
            self.ui.repeat_chkbox.setChecked(False)
        tuning_values.pop(2)  # removes repeat value
        self.toggle_repeat_movement_chkbox()

        # Sets input values
        inputs = [self.ui.cursor_speed_input, self.ui.scroll_speed_input,
                  self.ui.delay_activation_input, self.ui.repeat_speed_input]
        for value, entry in zip(tuning_values, inputs):
            entry.setValue(value)

        # Sets slider values
        sliders = [self.ui.cursor_speed_slider, self.ui.scroll_speed_slider,
                   self.ui.delay_activation_slider, self.ui.scroll_speed_slider]
        for value, slider in zip(tuning_values, sliders):
            slider.setValue(int(value))

    def adjust_tuning_slider(self, slider):
        # Adjusts the result/numbers of the input boxes according to slider value.
        value = slider.value()
        # New 3.10 stuff! match-case looks cleaner than if-stmts tbh
        match slider:
            # Cursor speed
            case self.ui.cursor_speed_slider:
                self.ui.cursor_speed_input.setValue(value)

            # Scroll speed
            case self.ui.scroll_speed_slider:
                self.ui.scroll_speed_input.setValue(value)

            # Delay activation
            case self.ui.delay_activation_slider:
                value = value * 0.1
                self.ui.delay_activation_input.setValue(value)

            # Repeat speed
            case self.ui.repeat_speed_slider:
                value = value * 0.01
                self.ui.repeat_speed_input.setValue(value)

    def adjust_tuning_entry(self, entry):
        # Adjusts the sliders according to the given input in the following boxes.
        value = entry.value()
        match entry:
            # Cursor speed
            case self.ui.cursor_speed_input:
                self.ui.cursor_speed_slider.setValue(value)

            # Scroll speed
            case self.ui.scroll_speed_input:
                self.ui.scroll_speed_slider.setValue(value)

            # Delay activation
            case self.ui.delay_activation_input:
                value = value * 10
                self.ui.delay_activation_slider.setValue(int(value))

            # Repeat speed
            case self.ui.repeat_speed_input:
                value = value * 100
                self.ui.repeat_speed_slider.setValue(int(value))

    def toggle_repeat_movement_chkbox(self):
        # Sets the repeat_movement guis enabled/disabled when the chkbox is toggled.
        guis = [self.ui.delay_activation_slider,  self.ui.delay_activation_input,
                self.ui.repeat_speed_input, self.ui.repeat_speed_slider]

        if self.ui.repeat_chkbox.isChecked():
            for gui in guis:
                gui.setEnabled(True)
        else:
            for gui in guis:
                gui.setEnabled(False)

    def reset_tuning(self):
        # Resets the tuning of the program and replaces it with the default settings.
        def action():
            table_cmds.reset_tuning()
            self.set_saved_tuning()
            self.save_tuning()

        create_warning_dialog(
            "Are you sure you want to reset the tuning?", action)

    def save_tuning(self):
        # Gets the value from the inputs and saves it to the db,
        # it then updates the tuning to the desired settings.

        # Gets input values
        cursor_speed = self.ui.cursor_speed_input.value()
        scroll_speed = self.ui.scroll_speed_input.value()
        enable_repeat = self.ui.repeat_chkbox.isChecked()
        delay_activation = self.ui.delay_activation_input.value()
        repeat_speed = self.ui.repeat_speed_input.value()

        # Saves to db
        table_cmds.save_tuning(
            cursor_speed, scroll_speed, enable_repeat, delay_activation, repeat_speed)

        # updates the tuning and repeater
        action_generator.get_tuning_data()
        action_generator.update_event_repeater()
        action_generator.toggle_event_repeater(action_generator.repeater)

    def populate_mapping_list(self, keybinds, preset):
        # Populates 'mapping_list' with data, the list visualizes the current binds
        # that are connected to specific controls.

        # Gets column names of presets and mapping tables
        self.preset_columns = db_cmds.get_column("presets")
        self.control_rows = db_cmds.get_column("mapping")

        def set_cells():
            # Sets the amount of columns
            column_cnt = 2
            keybinds_cnt = len(self.control_rows) + 1  # sets 28 rows in total
            self.ui.mapping_list.setColumnCount(column_cnt)
            self.ui.mapping_list.setRowCount(keybinds_cnt)

        def set_preset_column():
            self.ui.mapping_list.setItem(
                0, 0, QtWidgets.QTableWidgetItem("CONTROLS:"))
            self.ui.mapping_list.setItem(
                0, 1, QtWidgets.QTableWidgetItem(preset))

        def set_control_rows():
            for row, controls in enumerate(self.control_rows):
                self.ui.mapping_list.setItem(
                    row+1, 0, QtWidgets.QTableWidgetItem(controls))

        def show_bind_data():
            for row, keybind in enumerate(keybinds):
                self.ui.mapping_list.setItem(
                    row+1, 1, QtWidgets.QTableWidgetItem(keybind))

        set_cells()
        set_preset_column()
        set_control_rows()
        show_bind_data()

        self.ui.mapping_list.resizeColumnsToContents()

    def set_preset_choices(self):
        presets = db_cmds.get_column("presets")
        for row, preset in enumerate(presets):
            self.ui.preset_to_use_list.insertItem(row, preset)

    def toggle_keybind_editing(self):
        # 7/28/23: Okay, nevermind what that comment said. I am changing it because it's actually an annoying thing in the app.
        # Also this app needs a design overhaul!
        # Back then, before the july update. Preset 1 was not editable even though most of the controls are pre-configured.
        # Because of that, it made the usage of the app somewhat annoying especially when the configs were just a little bit off.
        preset = self.ui.preset_to_use_list.currentText()

        # This time, Preset 2 and 3 cannot be reset to default because they start with nothing at all.
        # I hope it doesn't backfire.
        if preset != "PRESET_1":
            self.ui.reset_first_preset_btn.setDisabled(True)
        else:
            self.ui.reset_first_preset_btn.setDisabled(False)
        
    def reset_first_preset(self):
        # I combined some code from 2 different functions in db_setup.py.
        # Essentialy, it just loads the default configurations from preset 1 as if the database was freshly made.
        # Then refreshes the mapping list
        default_mapping = [
            "'keyboard_pg_up'",
            "'keyboard_pg_down'",
            "'keyboard_pg_left'",
            "'keyboard_pg_right'",
            "'summon_keyboard'",
            "'mouse_right_click'",
            "'mouse_left_click'",
            "'mouse_left_press'",
            "'keyboard_ctrl_c'",
            "'keyboard_alt_tab'",
            "'keyboard_ctrl_a'",
            "'mouse_move_up'",
            "'mouse_move_down'",
            "'mouse_move_left'",
            "'mouse_move_right'",
            "'keyboard_ctrl_v'",
            "'keyboard_tab'",
            "'keyboard_ctrl_x'",
            "'mouse_scroll_up'",
            "'mouse_scroll_down'",
            "'Empty'",
            "'Empty'",
            "'keyboard_windows_btn'",
            "'Empty'",
            "'Empty'"
        ]

        # Damn it. I forgot the methods are from a different class!
        table = "mapping"
        columns = table_cmds.get_column("mapping")
        
        row = 1
        for column, keybind in zip(columns, default_mapping):
            print(table, column, keybind, row)
            table_cmds.update_data(table, column, keybind, row)

        self.refresh_mapping_list()

    def use_selected_preset(self):
        # Gets selected preset
        selected_preset = self.ui.preset_to_use_list.currentText()
        all_presets = db_cmds.get_column("presets")

        # Updates the selected preset to 'True', so that it can be used
        db_cmds.update_data("presets", selected_preset, data=True, row=1)
        for other_preset in all_presets:
            if other_preset != selected_preset:
                db_cmds.update_data(
                    "presets", other_preset, data=False, row=1)

        self.ui.in_use_lbl.setText(f"In-Use: {selected_preset}")

        # Keybind data is then re-fetched to return different keybind data
        self.update_keybind_data()

    def set_keybind_editing(self):
        # Populates the edit_control_list, and edit_keybind_list with table columns
        # for keybind_editing
        controls = db_cmds.get_column("mapping")
        keybinds = db_cmds.get_column("all_keybinds")
        for row, control in enumerate(controls):
            self.ui.edit_control_list.insertItem(row, control)
        for row, keybind in enumerate(keybinds):
            self.ui.edit_keybind_list.insertItem(row, keybind)

    def sync_keybind_to_control(self):
        control = self.ui.edit_control_list.currentText()
        raw_keybind = self.ui.edit_keybind_list.currentText()
        preset = self.ui.preset_to_use_list.currentText()

        # Data has to be quoted for some reason
        keybind = f"'{raw_keybind}'"
        # Splits the preset string, takes the number of the preset, then updates a row of data with the number
        preset_num = get_preset_num(preset)
        db_cmds.update_data(
            table="mapping", column=control, data=keybind, row=preset_num)
        self.update_keybind_data()

    def clear_keybind(self):
        # Gets the selected preset and control, then overwrites the data with 'Empty',
        # so that the control is unusable until a new keybind is synced to it.
        preset = self.ui.preset_to_use_list.currentText()
        control = self.ui.edit_control_list.currentText()
        new_data = "'Empty'"

        preset_num = get_preset_num(preset)
        db_cmds.update_data(
            table="mapping", column=control, data=new_data, row=preset_num)
        self.update_keybind_data()

    def clear_all_keybinds(self):
        # Pretty self-explanatory, gets preset number and clears the row of keybinds
        # according to the number.
        preset = self.ui.preset_to_use_list.currentText()

        def action():
            preset_num = get_preset_num(preset)
            table_cmds.set_keybinds_empty(preset_num)
            self.update_keybind_data()

        create_warning_dialog(
            f"Are you sure you want to clear all keybinds of {preset}", action)

    def update_keybind_data(self):
        # Gets new keybind data and binds it to controls
        data = self.get_keybind_data()
        self.populate_mapping_list(keybinds=data[0], preset=data[1])
        self.bind_keybinds_to_controls()
        if self.enable:
            self.enable_controls()

    def refresh_mapping_list(self):
        # Refreshes mapping list with new keybind data
        keybind_data = self.get_keybind_data()
        self.populate_mapping_list(
            keybinds=keybind_data[0], preset=keybind_data[1])

    def show_preset_preview(self):
        # Shows a preview of a preset's data in self.mapping_list when it is selected,
        # but it doesn't set the keybinds to that preset immediately unless it is then used.
        preset = self.ui.preset_to_use_list.currentText()
        preset_num = get_preset_num(preset)
        preview_data = db_cmds.get_row_data(table="mapping", row=preset_num)

        self.ui.previewing_lbl.setText(f"Previewing: {preset}")
        self.populate_mapping_list(preview_data, preset)

        self.set_mapping_list_cell()

    def set_mapping_list_cell(self):
        controls_column = 0
        keybinds_column = 1
        try:
            # To prevent the program from breaking, an exception was made to continue running the program
            # even if no cells were selected in the mapping_list.

            # Sets the current text of comboboxes based on the current_cell selected by the user
            current_cell = self.ui.mapping_list.currentItem()

            # Gets the info of the adjacent column and sets the text of edit_control and edit_keybind comboboxes together
            if self.ui.mapping_list.currentColumn() == controls_column:
                adjacent_column = current_cell.column() + 1  # switches to keybinds column
                adjacent_cell = self.ui.mapping_list.item(
                    current_cell.row(), adjacent_column)
                self.ui.edit_control_list.setCurrentText(current_cell.text())
                self.ui.edit_keybind_list.setCurrentText(adjacent_cell.text())

            elif self.ui.mapping_list.currentColumn() == keybinds_column:
                adjacent_column = current_cell.column() - 1  # switches to controls column
                adjacent_cell = self.ui.mapping_list.item(
                    current_cell.row(), adjacent_column)
                self.ui.edit_control_list.setCurrentText(adjacent_cell.text())
                self.ui.edit_keybind_list.setCurrentText(current_cell.text())

        except AttributeError:
            print("No cells selected")

    def highlight_mapping_list_cell(self):
        # Gets the amt of rows and columns of the mapping list, then gets every data in it
        list_items = []
        for row in range(self.ui.mapping_list.rowCount()):
            for column in range(self.ui.mapping_list.columnCount()):
                item = self.ui.mapping_list.item(row, column)
                list_items.append(item)

        # Checks if the selected item exists in list_items.
        # Once it does, it gets the row and column of the item, then highlights the cell for visual purposes.
        selected_control = self.ui.edit_control_list.currentText()
        for item in list_items:
            item_text = item.text()
            if selected_control == item_text:
                item_row, item_column = item.row(), item.column()
                self.ui.mapping_list.setCurrentCell(item_row, item_column)

    def launch_keyboard_widget(self):
        self.tkeyboard_widget = tkeyboard.App()
        self.tkeyboard_widget.capture_pressed_keys()


def init_main_app():
    main_app = QtWidgets.QApplication(sys.argv)
    # declaring as variable prevents memory dumping the entire program.
    _ = App()
    sys.exit(main_app.exec())


if __name__ == "__main__":
    init_main_app()
