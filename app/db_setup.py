import sqlite3
import os

# Goes to the path of the project according to the location of this file.
# NOTE: Don't put this file outside of its original directory or the program breaks due to path errors.
from pathlib import Path
path = Path(__file__)
project_path = path.parent.absolute()
os.chdir(project_path)

db_path = "data"
db_name = "controls.db"
db = f"{db_path}/{db_name}"

class DBcmds:
    # Holds all the methods needed to manipulate the database 
    def __init__(self) -> None:
        self.open_db()

    def open_db(self) -> None:
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()

    def create_table(self, table_name: str, columns: dict) -> None:
        self.open_db()
        stmt = f"""CREATE TABLE IF NOT EXISTS {table_name}(Temp BOOLEAN)"""
        self.cur.execute(stmt)

        drop_temp_column = f"""ALTER TABLE {table_name} DROP COLUMN Temp"""
        for k, v in columns.items():
            add_columns = f"""
            ALTER TABLE {table_name}
            ADD {k} {v}
            """
            self.cur.execute(add_columns)

        self.cur.execute(drop_temp_column)
        self.conn.commit()
        self.conn.close()

    def insert_data(self, table: str, data: list) -> None:
        self.open_db()
        var_string = ', '.join('?' * len(data))
        stmt = f"""INSERT INTO {table} VALUES (%s);""" % var_string
        self.cur.execute(stmt, data)
        self.conn.commit()
        self.conn.close()

    def update_data(self, table: str, column: str, data: any, row: int) -> None:
        self.open_db()
        stmt = f"""
        UPDATE {table} SET {column} = {data} WHERE rowid = {row}
        """
        self.cur.execute(stmt)
        self.conn.commit()
        self.conn.close()

    def delete_table(self, table: str) -> None:
        self.open_db()
        stmt = f"DROP TABLE {table}"
        self.cur.execute(stmt)
        self.conn.commit()
        self.conn.close()

    def delete_row_data(self, table: str, row: int) -> None:
        self.open_db()
        stmt = f"DELETE FROM {table} WHERE rowid = {row}"
        self.cur.execute(stmt)
        self.conn.commit()
        self.conn.close()

    def delete_all_data(self, table: str) -> None:
        self.open_db()
        stmt = f"""DELETE FROM {table}"""
        self.cur.execute(stmt)
        self.conn.commit()
        self.conn.close()

    def get_all_data(self, table: str, get_row=False) -> list:
        self.open_db()
        if get_row:
            stmt = f"SELECT rowid, * FROM {table}"
        else:
            stmt = f"SELECT * FROM {table}"
        self.cur.execute(stmt)

        data = self.cur.fetchall()
        self.conn.close()

        return data

    def get_row_data(self, table: str, row: int) -> list:
        self.open_db()
        stmt = f"""SELECT * FROM {table} WHERE rowid = {row}"""
        self.cur.execute(stmt)
        raw_data = self.cur.fetchall()
        data = raw_data[0]

        self.conn.close()

        return data

    def get_column(self, table: str) -> list:
        # gets column names of a table
        self.open_db()
        stmt = f"""PRAGMA table_info({table})"""
        self.cur.execute(stmt)
        columns = self.cur.fetchall()
        names = [fields[1] for fields in columns]

        self.conn.close()

        return names


class TABLEcmds(DBcmds):
    # Holds all methods that manipulate and initialize tables in database

    # tuning data
    DEFAULT_CURSOR_SPEED = 15
    DEFAULT_SCROLL_SPEED = 1
    DEFAULT_ENABLE_REPEAT = True
    DEFAULT_DELAY_PER_MOVEMENT = 0.1
    DEFAULT_REPEAT_SPEED = 0.03

    def __init__(self):
        super().__init__()
        self.default_values = [
            TABLEcmds.DEFAULT_CURSOR_SPEED, TABLEcmds.DEFAULT_SCROLL_SPEED,
            TABLEcmds.DEFAULT_ENABLE_REPEAT, TABLEcmds.DEFAULT_DELAY_PER_MOVEMENT,
            TABLEcmds.DEFAULT_REPEAT_SPEED
        ]

    # Pre-made functions to reduce suffering in db operations and first time setup.
    def create_mapping(self):
        # Creates 3 columns, uses buttons as rows so that they can activate a given key.
        # The function also creates a default set of keybinds at the first column. It cannot be edited on the app.
        table_columns = {
            "DPAD_UP": "text",
            "DPAD_DOWN": "text",
            "DPAD_LEFT": "text",
            "DPAD_RIGHT": "text",
            "TRIANGLE": "text",
            "CIRCLE": "text",
            "CROSS": "text",
            "SQUARE": "text",
            "L1": "text",
            "L2": "text",
            "L3": "text",
            "L3_UP": "text",
            "L3_DOWN": "text",
            "L3_LEFT": "text",
            "L3_RIGHT": "text",
            "R1": "text",
            "R2": "text",
            "R3": "text",
            "R3_UP": "text",
            "R3_DOWN": "text",
            "R3_LEFT": "text",
            "R3_RIGHT": "text",
            "SELECT_BTN": "text",
            "START_BTN": "text",
            "ANALOG_BTN": "text"
        }
        # NOTE: If you want a button to have no binds, then type 'Empty' on a field instead.
        default_mapping = [
            'keyboard_pg_up',
            'keyboard_pg_down',
            'keyboard_pg_left',
            'keyboard_pg_right',
            'summon_keyboard',
            'mouse_right_click',
            'mouse_left_click',
            'mouse_left_press',
            'keyboard_ctrl_c',
            'keyboard_alt_tab',
            'keyboard_ctrl_a',
            'mouse_move_up',
            'mouse_move_down',
            'mouse_move_left',
            'mouse_move_right',
            'keyboard_ctrl_v',
            'keyboard_tab',
            'keyboard_ctrl_x',
            'mouse_scroll_up',
            'mouse_scroll_down',
            'Empty',
            'Empty',
            'keyboard_windows_btn',
            'Empty',
            'Empty'
        ]

        total_control_count = 25
        free_rows = []
        for _ in range(total_control_count):
            free_rows.append("Empty")

        self.create_table("mapping", table_columns)
        self.insert_data("mapping", default_mapping)

        for _ in range(2):
            self.insert_data("mapping", free_rows)

    def create_presets(self):
        # creates presets, which can be activated/deactivated to run certain mapping columns
        table_columns = {
            "PRESET_1": "BOOLEAN",
            "PRESET_2": "BOOLEAN",
            "PRESET_3": "BOOLEAN"
        }
        default_data = [True, False, False]

        self.create_table("presets", table_columns)
        self.insert_data("presets", default_data)

    def create_all_keybinds(self):
        # creates different keybinds that can be assigned to a controller button
        keybinds = {
            'mouse_move_up': "NONE",
            'mouse_move_down': "NONE",
            'mouse_move_left': "NONE",
            'mouse_move_right': "NONE",
            'mouse_middle_click': "NONE",
            'mouse_right_click': "NONE",
            'mouse_left_click': "NONE",
            'mouse_left_press': "NONE",
            'mouse_scroll_up': "NONE",
            'mouse_scroll_down': "NONE",
            'keyboard_tab': "NONE",
            'keyboard_esc': "NONE",
            'keyboard_ctrl_c': "NONE",
            'keyboard_ctrl_v': "NONE",
            'keyboard_ctrl_x': "NONE",
            'keyboard_ctrl_a': "NONE",
            'keyboard_alt_f4': "NONE",
            'keyboard_windows_btn': "NONE",
            'keyboard_f11': "NONE",
            'keyboard_shift': "NONE",
            'keyboard_alt_tab': "NONE",
            'keyboard_pg_up': "NONE",
            'keyboard_pg_down': "NONE",
            'keyboard_pg_left': "NONE",
            'keyboard_pg_right': "NONE",
            'summon_keyboard': "NONE",
            'Empty': "NONE"
        }
        self.create_table("all_keybinds", keybinds)

    def set_keybinds_empty(self, row):
        # changes all the values of mapping table to empty
        table = "mapping"
        columns = self.get_column("mapping")
        keyword = "'Empty'"
        for column in columns:
            self.update_data(table, column, keyword, row)

    def create_tuning(self):
        # Creates adjustable tunings that can change the speed and feel of the controller when using the app.
        table_columns = {
            "cursor_speed": "INT",
            "scroll_speed": "INT",
            "enable_repeat": "BOOL",
            "delay_per_movement": "INT",
            "repeat_speed": "INT"
        }

        self.create_table("tuning", table_columns)
        self.insert_data("tuning", self.default_values)

    def reset_tuning(self):
        self.delete_all_data("tuning")
        self.insert_data("tuning", self.default_values)

    def save_tuning(self, cursor_speed, scroll_speed, enable_repeat, delay_per_movement, repeat_speed):
        self.delete_row_data("tuning", 1)

        given_data = [cursor_speed, scroll_speed,
                      enable_repeat, delay_per_movement, repeat_speed]
        self.insert_data("tuning", given_data)

def init_tables():
    table_cmds = TABLEcmds()
    table_cmds.create_mapping()
    table_cmds.create_presets()
    table_cmds.create_all_keybinds()
    table_cmds.create_tuning()

def setup_table():
    # Checks if the database exists in the path, if it doesn't,
    # it sets a new one up
    files = os.listdir(db_path)
    if db_name not in files:
        print("Creating controls.db")
        init_tables()
        print("Finished making controls.db")
    else:
        print("controls.db already exists, setup aborted")

if __name__ == "__main__":
    setup_table()