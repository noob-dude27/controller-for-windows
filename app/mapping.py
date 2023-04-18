# Handles the movement and interpretation of controller movements into mouse/keyboard equivalents.
# That's all I can say...
# This is like, basically an engine that runs the program

from pyjoystick.sdl2 import run_event_loop

import pyjoystick
import keyboard  # NOTE: This one is used for keyboard commands, this program uses a seperate keyboard for typing
import threading
import time
import db_setup as setup
import mouse

# list of controller events
definitions = [
    "Hat 0 [Up]", "Hat 0 [Down]", "Hat 0 [Left]", "Hat 0 [Right]", "Button 0", "Button 1", "Button 2", "Button 3",
    "Button 4", "Button 6", "Button 10", "-Axis 1", "Axis 1", "-Axis 0", "Axis 0", "Button 5", "Button 7", "Button 11",
    "-Axis 4", "Axis 4", "-Axis 2", "Axis 2", "Button 8"
]

setup.setup_table()
db_cmds = setup.DBcmds()


class Controls:
    def __init__(self) -> None:
        self.controls_data = db_cmds.get_column("mapping")

    def get(self):
        # Turns raw controller input into a more readable and user-friendly format
        controls_dict = {}
        for column, control in zip(self.controls_data, definitions):
            controls_dict[column] = control
        return controls_dict


class Keybinds:
    def __init__(self):
        # Pairs controls and keybinds together according to the preset enabled by the user
        self.keybind_data = db_cmds.get_all_data("mapping")

    def return_match(self, presets_dict):
        # Returns a combination of keybinds and the preset that is enabled
        if presets_dict["PRESET_1"] == True:
            return self.keybind_data[0], "PRESET_1"
        elif presets_dict["PRESET_2"] == True:
            return self.keybind_data[1], "PRESET_2"
        elif presets_dict["PRESET_3"] == True:
            return self.keybind_data[2], "PRESET_3"

    def bind(self, controls_dict, correct_keybinds):
        # creates a dictionary where a control is a key and a keybind is a value
        keybinds_dict = {}
        for control, keybind in zip(controls_dict, correct_keybinds):
            keybinds_dict[control] = keybind
        return keybinds_dict


class Presets:
    def __init__(self) -> None:
        # Grabs presets and their values (True or False) for further use
        self.presets = db_cmds.get_column("presets")
        self.preset_data = db_cmds.get_all_data("presets")
        # Removes double encapsulation
        self.preset_values = self.preset_data[0]
        self.presets_dict = {}

    def get(self):
        # Gets the presets and their values and returns it as a dictionary.
        for preset, preset_value in zip(self.presets, self.preset_values):
            self.presets_dict[preset] = preset_value
        return self.presets_dict


class ActionGenerator(threading.Thread):
    def __init__(self, keybinds_dict, controls_dict):
        # This generates mouse/keyboard movement through careful interpretation of controller data.
        # It only stops as soon as the application/program is closed.
        threading.Thread.__init__(self)
        self.keybinds = keybinds_dict
        self.controls = controls_dict
        self.movement = []
        self.tuning_data = self.get_tuning_data()

        self._is_running = True
        self.daemon = True

    def toggle_event_repeater(self, repeater):
        if self.enable_repeat:
            repeater.first_repeat_timeout = self.delay_per_movement
            repeater.check_timeout = self.repeat_speed
        elif not self.enable_repeat:
            repeater.first_repeat_timeout = None
            repeater.check_timeout = None

    def update_event_repeater(self):
        self.repeater.first_repeat_timeout = self.delay_per_movement
        self.repeater.check_timeout = self.repeat_speed

    def get_tuning_data(self):
        tuning_data = db_cmds.get_all_data("tuning")
        tuning_values = tuning_data[0]
        self.cursor_speed = tuning_values[0]
        self.scroll_speed = tuning_values[1]
        self.enable_repeat = tuning_values[2]
        self.delay_per_movement = tuning_values[3]
        self.repeat_speed = tuning_values[4]

    def run(self):
        # NOTE: thread actually starts here.
        # This keeps the thread alive so that it can continously capture controller input.
        self.set_event_manager()
        while self._is_running:
            self.find_key()

    def set_event_manager(self):
        # This sets pyjoystick's ThreadEventManager that has the ability to record same input for a
        # set amount of time.

        # clearer explanation of timeouts:
        # first_repeat_timeout: more like timeout activation
        # repeat_timeout: delay of a repeat of events
        # check_timeout: prevents action from happening for too long
        self.repeater = pyjoystick.Repeater(
            first_repeat_timeout=self.delay_per_movement, repeat_timeout=self.repeat_speed, check_timeout=0.01)

        self.toggle_event_repeater(self.repeater)

        self.mngr = pyjoystick.ThreadEventManager(event_loop=run_event_loop,
                                                  button_repeater=self.repeater)
        self.mngr.start()

    def find_key(self):
        # Records controller input.
        key = self.mngr.find_key(timeout=float('inf'))
        if key:
            self.handle_key_event(key)

    def handle_key_event(self, key):
        # Recieves the controller events and assigns them to their corresponding keybinds
        # If none are received, or an invalid key is pressed, it will receive other controller input
        # instead.
        for k, v in self.controls.items():
            if key == v:
                assigned_key = k

        try:
            if assigned_key in self.keybinds.keys():
                self.movement = self.keybinds[assigned_key]
                print(assigned_key, self.movement)
                self.restructure_params(self.movement)
        except UnboundLocalError:
            print("Invalid key pressed")
        except AttributeError:
            print("Keybind dictionary might be empty or is disabled")

    def restructure_params(self, movement):
        # Restructures readable keybind format into something easier to compare for movement.
        params = movement.split("_")
        input_type = params[0]

        match input_type:
            case "mouse":
                if params[1] == "scroll" or params[1] == "move":
                    self.generate_mouse_action(
                        direction=params[2], action=params[1])
                    
                elif params[2] == "press":
                    self.generate_mouse_action(
                        direction=params[1], action=params[2]
                    )
                
                elif params[2] == "click":
                    self.generate_mouse_action(
                        direction=params[1], action=params[2])
            
            case "keyboard":
                params.pop(0)  # removes input_type
                self.generate_keyboard_action(params)
            
            case "summon":
                if params[1] == "keyboard":
                    keyboard.press_and_release("ctrl+k")

    def generate_mouse_action(self, direction, action):
        mouse_pos = mouse.get_position()
        pos_x = mouse_pos[0]
        pos_y = mouse_pos[1]

        if action == "move":
            match direction:
                case "up":
                    new_pos_y = pos_y - self.cursor_speed
                    mouse.move(pos_x, new_pos_y)
                case "down":
                    new_pos_y = pos_y + self.cursor_speed
                    mouse.move(pos_x, new_pos_y)
                case "left":
                    new_pos_x = pos_x - self.cursor_speed
                    mouse.move(new_pos_x, pos_y)
                case "right":
                    new_pos_x = pos_x + self.cursor_speed
                    mouse.move(new_pos_x, pos_y)

        elif action == "click":
            if direction == "right":
                # Reason for this line is because pressing right-click to open a menu is not enough,
                # you also have to release the key.
                mouse.right_click()
            else:
                # The 'direction' variable is understood by the mouse method as either 'left', or 'right'
                # Therefore no need to individually map their logic 
                #mouse.click(direction)
                mouse.click(direction)

        elif action == "press":
            mouse.press(direction)

        elif action == "scroll":
            match direction:
                case "up":
                    mouse.wheel(self.scroll_speed)
                case "down":
                    mouse.wheel(-self.scroll_speed)

    def generate_keyboard_action(self, key):
        match key[0]:
            case "esc":
                keyboard.press_and_release("esc")
            case "tab":
                keyboard.press_and_release("tab")
                keyboard.release("alt+tab")
            case "shift":
                keyboard.press_and_release("shift")
            case "f11":
                keyboard.press_and_release("f11")
            case "windows":
                time.sleep(0.15)
                keyboard.press_and_release("cmd")

        # alt keys
        if key[0] == "alt":
            match key[1]:
                case "f4":
                    keyboard.press_and_release("alt+f4")
                case "tab":
                    keyboard.press("alt+tab")

        # ctrl keys
        if key[0] == "ctrl":
            match key[1]:
                case "c":
                    keyboard.press_and_release("ctrl+c")
                case "v":
                    keyboard.press_and_release("ctrl+v")
                case "x":
                    keyboard.press_and_release("ctrl+x")
                case "a":
                    keyboard.press_and_release("ctrl+a")

        # pg keys
        if key[0] == "pg":
            match key[1]:
                case "up":
                    keyboard.press_and_release("up")
                case "down":
                    keyboard.press_and_release("down")
                case "left":
                    keyboard.press_and_release("left")
                case "right":
                    keyboard.press_and_release("right")
