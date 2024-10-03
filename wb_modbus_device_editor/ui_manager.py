import ipaddress
import tkinter
import tkinter.scrolledtext as scrolltext
from datetime import datetime
from tkinter import filedialog, ttk

import scroll_frame
import serial.tools.list_ports
import widgets


class UiManager:
    widgets = {}
    win = None
    log = None
    notebook = None
    left_frame = None

    btn_read_params = None
    btn_write_params = None
    btn_open_template = None

    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title("Python Modbus Device Editor")
        self.window.geometry("1490x750")

        self.parametrized_widgets = {}
        self.modbus_widgets = {}
        self.window_widgets = {}

        style = ttk.Style(self.win)
        style.theme_use("clam")
        style.theme_settings(
            "clam",
            {
                "TCombobox": {
                    "map": {
                        "background": [
                            ("active", "darkgray"),
                            ("disabled", "darkgray"),
                        ],
                        "fieldbackground": [("disabled", "gray")],
                        "foreground": [("focus", "black"), ("!disabled", "black")],
                    }
                }
            },
        )

        self.top_frame = widgets.Frame(
            self.window, height=50, opts={"side": tkinter.TOP, "fill": tkinter.X, "expand": False}
        )
        self.io_actions = widgets.Group(
            self.top_frame,
            text="Чтение/запись параметров",
            relief=tkinter.GROOVE,
            opts={"side": tkinter.RIGHT, "fill": tkinter.BOTH, "expand": False},
        )
        self.slave_id = widgets.Spinbox(
            self.io_actions,
            title="Адрес",
            minimum=0,
            maximum=255,
            value_type="int",
            default=1,
            width=4,
            description=None,
            opts={"side": tkinter.LEFT},
        )
        self.btn_open_template = widgets.Button(
            self.io_actions,
            text="Открыть шаблон",
            command=None,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.btn_read_params = widgets.Button(
            self.io_actions,
            text="Читать параметры",
            command=None,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.btn_write_params = widgets.Button(
            self.io_actions,
            text="Записать параметры",
            command=None,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.modbus_settings = widgets.Group(
            self.top_frame,
            text="Настройки подключения",
            relief=tkinter.GROOVE,
            opts={"side": tkinter.RIGHT, "fill": tkinter.BOTH, "expand": True},
        )
        self.modbus_mode = widgets.Combobox(
            self.modbus_settings,
            title="Режим",
            values_enum=self.get_mode_enum(),
            default="RTU",
            width=12,
            selected_func=self.mod_selected,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.modbus_rtu_port = widgets.Combobox(
            self.modbus_settings,
            title="Порт",
            values_enum=self.get_ports_enum(),
            default=None,
            width=40,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.modbus_rtu_baudrate = widgets.Combobox(
            self.modbus_settings,
            title="Скорость обмена",
            values_enum=self.get_baudrate_enum(),
            default=9600,
            width=8,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.modbus_rtu_bytesize = widgets.Combobox(
            self.modbus_settings,
            title="Биты данных",
            values_enum=self.get_bytesize_enum(),
            default=8,
            width=8,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.modbus_rtu_parity = widgets.Combobox(
            self.modbus_settings,
            title="Четность",
            values_enum=self.get_parity_enum(),
            default="N",
            width=8,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.modbus_rtu_stopbits = widgets.Combobox(
            self.modbus_settings,
            title="Стоп биты",
            values_enum=self.get_stopbits_enum(),
            default=2,
            width=8,
            opts={"side": tkinter.LEFT, "anchor": tkinter.SW},
        )
        self.modbus_tcp_ip = widgets.TextInput(
            self.modbus_settings,
            title="IP",
            width=23,
            validation_func=self.validate_ipv4,
            opts={"side": tkinter.LEFT},
        )
        self.modbus_tcp_port = widgets.Spinbox(
            self.modbus_settings,
            title="Порт",
            minimum=1,
            maximum=65535,
            value_type="int",
            default=23,
            width=4,
            description=None,
            opts={"side": tkinter.LEFT},
        )

        self.bottom_frame = widgets.Frame(
            self.window, opts={"side": tkinter.TOP, "fill": tkinter.BOTH, "expand": True}
        )
        self.device_settings = widgets.Group(
            self.bottom_frame,
            text="Настройки устройства",
            relief=tkinter.GROOVE,
            opts={"side": tkinter.LEFT, "fill": tkinter.BOTH, "expand": True},
        )
        self.notebook = widgets.Notebook(
            self.device_settings, opts={"side": tkinter.TOP, "fill": tkinter.BOTH, "expand": True}
        )
        self.journal = widgets.Group(
            self.bottom_frame,
            text="Журнал",
            relief=tkinter.GROOVE,
            opts={"side": tkinter.LEFT, "fill": tkinter.Y},
        )
        self.journal_logger = widgets.ScrolledText(
            self.journal, width=50, opts={"side": tkinter.LEFT, "fill": tkinter.BOTH, "expand": True}
        )

        self.journal_logger.configure(state="disabled")

    def create_tcp_settings(self, mb_settings):
        self.create_text_input(
            parent=mb_settings,
            id="nodel_mb_tcp_ip",
            title="IP",
            validation_func=self.validate_ipv4,
            side=tkinter.LEFT,
        )

        self.tcp_port = self.create_spinbox(
            parent=mb_settings,
            id="nodel_mb_tcp_port",
            title="Порт",
            min_=1,
            max_=65535,
            value_type="int",
            default=23,
            width=4,
            description=None,
            side=tkinter.LEFT,
        )

    def _widget_commit(self, widget, widget_id, widget_type, parent_id, widget_opts):
        widget.id = widget_id
        widget.parent_id = parent_id
        widget.pack(widget_opts)
        widget.pack_info = self.get_pack_info(widget)
        widget.type = widget_type
        widget.visible = True
        widget.conditions = []
        self.widgets[widget_id] = widget

    def write_log(self, text):
        self.journal_logger.configure(state="normal")
        res = self.ljournal_loggerog.insert(
            tkinter.END, "{} | {} \n".format(f"{datetime.now():%H:%M:%S}", text)
        )
        self.journal_logger.configure(state="disabled")
        self.journal_logger.see("end")
        return 0

    def create_frame(self, parent, id, side, fill, expand, **args):
        frame = ttk.Frame(parent, **args)
        frame.pack(padx=5, pady=5, side=side, fill=fill, expand=expand)
        frame.type = "frame"
        frame.id = id
        self.widgets[id] = frame
        return frame

    def create_viewport(self, parent, id):
        scrool_frame = scroll_frame.ScrollFrame(parent)
        viewport = scrool_frame.viewPort
        scrool_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        scrool_frame.pack_info = self.get_pack_info(scrool_frame)
        viewport.type = "viewport"
        viewport.id = id
        self.widgets[id] = viewport
        return viewport

    def create_row(self, parent, id):
        row_frame = ttk.Frame(parent)
        row_frame.type = "row"
        row_frame.pack(padx=5, pady=5, side=tkinter.TOP, fill="x", expand="no")
        row_frame.pack_info = self.get_pack_info(row_frame)
        row_frame.id = id
        self.widgets[id] = row_frame
        return row_frame

    def create_notebook(self, parent, id, **opts):
        notebook = ttk.Notebook(parent)
        notebook.pack(**opts)
        notebook.pack_info = self.get_pack_info(notebook)
        notebook.type = "notebook"
        notebook.id = id
        self.widgets[id] = notebook
        return notebook

    def create_tab(self, id, title):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=title)
        tab.type = "nb_tab"
        self.widgets[id + "nb_tab"] = tab

        viewport = self.create_viewport(tab, id)
        viewport.curr_row = 0
        viewport.curr_col = 0
        viewport.curr_frame = self.create_row(viewport, id + "_row")
        viewport.type = "tab"
        viewport.child_wrap = self.create_group(
            viewport.curr_frame, id + "_wrap", "Базовые", side=tkinter.LEFT, anchor=tkinter.NW
        )
        viewport.id = id
        self.widgets[id] = viewport
        return viewport

    def create_scrolled_text(self, parent, id, width, **opts):
        scrolled_text = scrolltext.ScrolledText(parent, width=width, wrap="word")
        self._widget_commit(
            widget=scrolled_text,
            widget_id=id,
            widget_type="scrolled_text",
            widget_opts=opts,
            parent_id=parent.id,
        )
        return scrolled_text

    def create_group(self, parent, id, title, relief=tkinter.GROOVE, **opts):
        group = ttk.LabelFrame(parent, text=title, relief=relief)
        self._widget_commit(
            widget=group,
            widget_id=id,
            widget_type="group",
            widget_opts={"padx": 5, "pady": 5, **opts},
            parent_id=parent.id,
        )
        return group

    def create_label(self, parent, id, title, **opts):
        label = ttk.Label(parent, text=title)
        self._widget_commit(
            widget=label,
            widget_id=id,
            widget_type="label",
            widget_opts={"padx": 5, "pady": 5, **opts},
            parent_id=parent.id,
        )
        return label

    def create_button(self, parent, id, title, command=None, **opts):
        button = ttk.Button(parent, text=title, command=command)
        self._widget_commit(
            widget=button,
            widget_id=id,
            widget_type="button",
            widget_opts={"padx": 5, "pady": 5, **opts},
            parent_id=parent.id,
        )
        return button

    def create_combobox(self, parent, id, title, dic, default, width, selected_func=None, **opts):
        enums = dic["enum_titles"]
        group = self.create_group(parent, id + "_title", title, relief=tkinter.FLAT, **opts)
        combobox = ttk.Combobox(group, values=enums, state="readonly", width=width)
        combobox.dic = dic
        self._widget_commit(
            widget=combobox,
            widget_id=id,
            widget_type="combobox",
            widget_opts={"padx": 5, "pady": 0, "side": tkinter.TOP, "anchor": tkinter.NW},
            parent_id=parent.id,
        )

        if selected_func:
            combobox.bind("<<ComboboxSelected>>", selected_func)

        if default in dic["enum"]:
            index = dic["enum"].index(default)
            combobox.current(index)
        elif len(enums) >= 1:
            combobox.current(0)

        return combobox

    def get_combobox_format(self, value_type):
        if value_type == "double":
            fmt = "%.2f"
        else:
            fmt = "%.0f"
        return fmt

    def get_pack_info(self, widget):
        info = widget.pack_info()
        del info["in"]
        return info

    def create_spinbox(
        self,
        parent,
        id,
        title,
        min_,
        max_,
        value_type,
        default,
        width,
        description,
        **opts,
    ):
        if min_ == None:
            min_ = 0.0
        if max_ == None:
            max_ = 100.0
        fmt = self.get_combobox_format(value_type)

        group = self.create_group(parent, id + "_title", title, relief=tkinter.FLAT, **opts)
        spinbox = ttk.Spinbox(group, from_=min_, to=max_, format=fmt, width=width)

        if default == None:
            default = 0
        spinbox.set(default)

        self._widget_commit(
            widget=spinbox,
            widget_id=id,
            widget_type="spinbox",
            widget_opts={"padx": 5, "pady": 0, "side": tkinter.TOP, "anchor": tkinter.NW},
            parent_id=parent.id,
        )
        if description != None:
            self.create_label(
                group,
                id + "_decsription",
                "min:{} max:{} default: {}".format(min_, max_, default),
                anchor=tkinter.NW,
            )
        return spinbox

    def create_text_input(self, parent: tkinter.Widget, id, title, validation_func, **opts):
        group = self.create_group(parent, id + "_title", title, relief=tkinter.FLAT, **opts)

        value = tkinter.StringVar()
        validatecommand = group.register(validation_func)
        entry = ttk.Entry(
            group,
            textvariable=value,
            width=23,
            validate="focusout",
            validatecommand=(validatecommand, "%P"),
            state="normal",
        )
        self._widget_commit(
            widget=entry,
            widget_id=id,
            widget_type="entry",
            widget_opts={"padx": 5, "pady": 0, "side": tkinter.TOP, "anchor": tkinter.NW},
            parent_id=parent.id,
        )

    def is_exists_widget(self, id):
        return self.widgets.get(id) is not None

    def set_left_frame_title(self, title):
        self.left_frame.configure(text=title)

    def set_value(self, widget_id, value, scale=None):
        widget = self.widgets.get(widget_id)
        if widget.type == "spinbox":
            if scale != None:
                value = value * scale
                widget.set(value)
            else:
                widget.set(value)
        else:
            if widget.type == "combobox":
                dic = widget.dic
                index = dic["enum"].index(value)
                widget.current(index)

    def get_value(self, widget_id):
        widget = self.widgets[widget_id]
        if "disabled" not in widget.state():
            if widget.type in ["spinbox", "entry"]:
                return widget.get()

            if widget.type == "combobox":
                dic = widget.dic
                value = widget.get()
                index = dic["enum_titles"].index(value)
                return dic["enum"][index]
        else:
            return None

    def get_widget_value(self, widget):
        if widget.type in ["spinbox", "combobox"] and not widget.visible:
            return

        if widget.type == "spinbox":
            return widget.get()

        if widget.type == "combobox":
            value = widget.get()
            dic = widget.dic
            try:
                index = dic["enum_titles"].index(value)
                return dic["enum"][index]
            except ValueError:
                pass

    def get_values(self):
        widgets = self.widgets
        values = {}

        for key, item in widgets.items():
            if item.type in ["spinbox", "combobox"] and not item.visible:
                continue

            if item.type == "spinbox":
                values.update({key: item.get()})

            if item.type == "combobox":
                value = item.get()
                dic = item.dic
                try:
                    index = dic["enum_titles"].index(value)
                    values.update({key: dic["enum"][index]})
                except ValueError:
                    pass

        return values

    def get_modbus_params(self):
        mode = self.get_value("nodel_mb_mode")
        common_params = {
            "mode": mode,
            "slave_id": self.get_value("nodel_mb_slave_id"),
        }
        if mode == "RTU":
            rtu_params = {
                "port": self.get_value("nodel_mb_rtu_port"),
                "baudrate": self.get_value("nodel_mb_rtu_baudrate"),
                "bytesize": self.get_value("nodel_mb_rtu_bytesize"),
                "parity": self.get_value("nodel_mb_rtu_parity"),
                "stopbits": self.get_value("nodel_mb_rtu_stopbits"),
            }
            return {**common_params, **rtu_params}
        if mode in ["TCP", "RTU over TCP"]:
            tcp_params = {
                "ip": self.get_value("nodel_mb_tcp_ip"),
                "port": self.get_value("nodel_mb_tcp_port"),
            }
            return {**common_params, **tcp_params}
        return None

    def get_widget(self, widget_id):
        return self.widgets.get(widget_id)

    def get_widgets(self):
        return self.widgets

    def widget_hide(self, widget_id):
        widget = self.widgets.get(widget_id)
        # if widget.type != "group":
        if widget != None:
            widget.visible = False
            widget.pack_forget()

            widget = self.widgets.get(widget_id + "_title")
            if widget != None:
                widget.pack_forget()

            widget = self.widgets.get(widget_id + "_decsription")
            if widget != None:
                widget.pack_forget()

    def widget_show(self, widget_id):
        widget = self.widgets[widget_id]
        widget.pack(widget.pack_info)
        widget.visible = True

        widget = self.widgets.get(widget_id + "_title")
        if widget != None:
            widget.pack(widget.pack_info)
            # не забываем глянуть, кто родитель и тоже его показать
            parent = self.widgets.get(widget.parent_id)
            parent.pack(parent.pack_info)

        widget = self.widgets.get(widget_id + "_decsription")
        if widget != None:
            widget.pack(widget.pack_info)

    def widget_disable(self, widget_id):
        widget = self.widgets[widget_id]
        widget.config(state="disable")

    def widget_enable(self, widget_id):
        widget = self.widgets[widget_id]

        if widget.type == "combobox":
            widget.config(state="readonly")
        else:
            widget.config(state="!disable")

    def open_file(self, templates_dir):
        file_patch = filedialog.askopenfilename(
            title="Выберите шаблон", initialdir=templates_dir, filetypes=[("JSON Template", "*.json")]
        )
        return file_patch

    def remove_widgets_item(self, key):
        self.widgets[key].destroy()
        del self.widgets[key]

    def delete_widgets(self):
        widgets = dict(self.widgets)
        for key in widgets:
            if "nodel_" not in key:
                self.remove_widgets_item(key)

    def get_ports(self):
        enum = []
        enum_titles = []
        ports = list(serial.tools.list_ports.comports())
        for port, desc, hwid in sorted(ports):
            enum.append(port)
            enum_titles.append("{}: {}".format(port, desc))

        return {"enum": enum, "enum_titles": enum_titles}

    def get_ports_enum(self):
        result = {}
        ports = list(serial.tools.list_ports.comports())
        for port, desc, hwid in sorted(ports):
            result[port] = f"{port}: {desc}"

        return result

    def gen_baudrate_dic(self):
        enum = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        enum_titles = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        return {"enum": enum, "enum_titles": enum_titles}

    def get_baudrate_enum(self):
        items = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        return {item: str(item) for item in items}

    def gen_bytesize_dic(self):
        enum = [5, 6, 7, 8]
        enum_titles = ["5", "6", "7", "8"]
        return {"enum": enum, "enum_titles": enum_titles}

    def get_bytesize_enum(self):
        items = [5, 6, 7, 8]
        return {item: str(item) for item in items}

    def gen_parity_dic(self):
        enum = ["N", "E", "O"]
        enum_titles = ["N", "E", "O"]
        return {"enum": enum, "enum_titles": enum_titles}

    def get_parity_enum(self):
        items = ["N", "E", "O"]
        return {item: item for item in items}

    def gen_stopbits_dic(self):
        enum = [1, 2]
        enum_titles = ["1", "2"]
        return {"enum": enum, "enum_titles": enum_titles}

    def get_stopbits_enum(self):
        items = [1, 2]
        return {item: str(item) for item in items}

    def get_mode_dic(self):
        enum = ["RTU", "TCP", "RTU over TCP"]
        enum_titles = ["RTU", "TCP", "RTU over TCP"]
        return {"enum": enum, "enum_titles": enum_titles}

    def get_mode_enum(self):
        return {"RTU": "RTU", "TCP": "TCP", "RTU over TCP": "RTU over TCP"}

    def validate_ipv4(self, ip):
        try:
            if ip:
                ipaddress.ip_address(ip)
            return True
        except ValueError:
            self.write_log(f"Неверный формат IP адреса: {ip}")
            return False

    def mod_selected(self, event):
        combobox = event.widget
        new_value = combobox.get()
        old_value = "TCP" if self.widgets.get("nodel_mb_tcp_ip") else "RTU"
        if (old_value == "RTU" and new_value in ["TCP", "RTU over TCP"]) or (
            old_value == "TCP" and new_value == "RTU"
        ):  # чтобы при переключении с tcp на rtu over tcp не сбрасывались настройки подключения
            widgets = dict(self.widgets)
            for key in widgets:
                if "nodel_mb_rtu" in key or "nodel_mb_tcp" in key:
                    self.remove_widgets_item(key)

            parent = self.widgets[combobox.parent_id]
            if new_value in ["TCP", "RTU over TCP"]:
                self.create_tcp_settings(parent)
            elif new_value == "RTU":
                self.create_rtu_settings(parent)
