import tkinter
import tkinter.scrolledtext as scrolltext
from datetime import datetime
from tkinter import filedialog, ttk

import serial.tools.list_ports

from . import scroll_frame


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
        self.win = tkinter.Tk()
        self.win.title("Python Modbus Device Editor")
        self.win.geometry("1400x750")

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

        # Верхняя часть окна с настройками подключения
        top_frame = self.create_frame(
            parent=self.win,
            id="nodel_top_frame",
            side=tkinter.TOP,
            fill=tkinter.X,
            expand=False,
            height=50,
        )

        mb_settings = self.create_group(
            parent=top_frame,
            id="nodel_mb_settings",
            title="Настройки подключения",
            side=tkinter.LEFT,
            fill=tkinter.BOTH,
            expand=False,
        )

        mb_port = self.create_combobox(
            parent=mb_settings,
            id="nodel_mb_port",
            title="Порт",
            dic=self.get_ports(),
            default=None,
            width=40,
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        mb_baudrate = self.create_combobox(
            parent=mb_settings,
            id="nodel_mb_baudrate",
            title="Скорость обмена",
            dic=self.gen_baudrate_dic(),
            default=9600,
            width=8,
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        mb_bytesize = self.create_combobox(
            parent=mb_settings,
            id="nodel_mb_bytesize",
            title="Биты данных",
            dic=self.gen_bytesize_dic(),
            default=8,
            width=8,
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        mb_parity = self.create_combobox(
            parent=mb_settings,
            id="nodel_mb_parity",
            title="Четность",
            dic=self.gen_parity_dic(),
            default="N",
            width=8,
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        mb_stopbits = self.create_combobox(
            parent=mb_settings,
            id="nodel_mb_stopbits",
            title="Стоп биты",
            dic=self.gen_stopbits_dic(),
            default=2,
            width=8,
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        mb_actions = self.create_group(
            parent=top_frame,
            id="nodel_mb_actions",
            title="Чтение/запись параметров",
            side=tkinter.LEFT,
            fill=tkinter.BOTH,
            expand=True,
        )

        self.mb_slave_id = self.create_spinbox(
            parent=mb_actions,
            id="nodel_mb_slave_id",
            title="Адрес",
            min_=0,
            max_=255,
            value_type="int",
            default=1,
            width=4,
            description=None,
            side=tkinter.LEFT,
        )

        self.btn_open_template = self.create_button(
            parent=mb_actions,
            id="nodel_btn_open_template",
            title="Открыть шаблон",
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        self.btn_read_params = self.create_button(
            parent=mb_actions,
            id="nodel_btn_read_params",
            title="Читать параметры",
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        self.btn_write_params = self.create_button(
            parent=mb_actions,
            id="nodel_btn_write_params",
            title="Записать параметры",
            side=tkinter.LEFT,
            anchor=tkinter.SW,
        )

        # Нижняя часть окна
        bottom_frame = self.create_frame(
            parent=self.win, id="nodel_bottom_frame", side=tkinter.TOP, fill=tkinter.BOTH, expand=True
        )

        # Левый фрейм
        self.left_frame = self.create_group(
            parent=bottom_frame,
            id="nodel_left_frame",
            title="Настройки устройства",
            side=tkinter.LEFT,
            fill=tkinter.BOTH,
            expand=True,
        )

        self.notebook = self.create_notebook(
            parent=self.left_frame,
            id="nodel_params_notebook",
            side=tkinter.TOP,
            fill=tkinter.BOTH,
            expand=True,
        )

        # Правый фрейм
        right_frame = self.create_group(
            parent=bottom_frame,
            id="nodel_right_frame",
            title="Журнал",
            side=tkinter.LEFT,
            fill=tkinter.Y,
        )

        self.log = self.create_scrolled_text(
            parent=right_frame,
            id="nodel_log",
            width=50,
            side=tkinter.LEFT,
            fill=tkinter.BOTH,
            expand=True,
        )
        self.log.configure(state="disabled")

    def _widget_commit(self, widget, widget_id, widget_type, parent_id, widget_opts):
        widget.id = widget_id
        widget.parent_id = parent_id
        widget.pack(widget_opts)
        widget.pack_info = self.get_pack_info(widget)
        widget.type = widget_type
        widget.visible = True
        self.widgets[widget_id] = widget

    def write_log(self, text):
        self.log.configure(state="normal")
        res = self.log.insert(tkinter.END, "{} | {} \n".format(f"{datetime.now():%H:%M:%S}", text))
        self.log.configure(state="disabled")
        self.log.see("end")
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

    def create_combobox(self, parent, id, title, dic, default, width, **opts):
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
            if widget.type == "spinbox":
                return widget.get()

            if widget.type == "combobox":
                dic = widget.dic
                value = widget.get()
                index = dic["enum_titles"].index(value)
                return dic["enum"][index]
        else:
            return None

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
        return {
            "slave_id": self.get_value("nodel_mb_slave_id"),
            "port": self.get_value("nodel_mb_port"),
            "baudrate": self.get_value("nodel_mb_baudrate"),
            "bytesize": self.get_value("nodel_mb_bytesize"),
            "parity": self.get_value("nodel_mb_parity"),
            "stopbits": self.get_value("nodel_mb_stopbits"),
        }

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

    def gen_baudrate_dic(self):
        enum = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        enum_titles = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        return {"enum": enum, "enum_titles": enum_titles}

    def gen_bytesize_dic(self):
        enum = [5, 6, 7, 8]
        enum_titles = ["5", "6", "7", "8"]
        return {"enum": enum, "enum_titles": enum_titles}

    def gen_parity_dic(self):
        enum = ["N", "E", "O"]
        enum_titles = ["N", "E", "O"]
        return {"enum": enum, "enum_titles": enum_titles}

    def gen_stopbits_dic(self):
        enum = [1, 2]
        enum_titles = ["1", "2"]
        return {"enum": enum, "enum_titles": enum_titles}
