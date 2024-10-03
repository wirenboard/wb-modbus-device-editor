import ipaddress
import tkinter
import tkinter.scrolledtext as scrolltext
from datetime import datetime
from tkinter import filedialog, ttk

import scroll_frame
import serial.tools.list_ports


class Label(ttk.Label):
    def __init__(self, master, text, opts):
        super().__init__(master=master, text=text)
        self.type = "label"
        self.pack({"padx": 5, "pady": 5, **opts})


class Group(ttk.LabelFrame):
    def __init__(self, master, text, relief, opts):
        super().__init__(master, text=text, relief=relief)
        self.type = "group"
        self.pack({"padx": 5, "pady": 5, **opts})


class Spinbox(ttk.Spinbox):
    def __init__(self, master, title, minimum, maximum, value_type, default, width, description, opts):
        minimum = 0.0 if minimum == None else minimum
        maximum = 100.0 if maximum == None else maximum
        default = 0 if default == None else default
        fmt = "%.2f" if value_type == "double" else "%.0f"

        group = Group(master, text=title, relief=tkinter.FLAT, opts=opts)
        super().__init__(group, from_=minimum, to=maximum, format=fmt, width=width)
        self.set(default)
        self.type = "spinbox"
        self.pack({"padx": 5, "pady": 0, "side": tkinter.TOP, "anchor": tkinter.NW})

        if description:
            Label(group, f"min:{minimum} max:{maximum} default: {default}", anchor=tkinter.NW)


class Combobox(ttk.Combobox):
    def __init__(self, master, title, values_enum, default, width, opts, selected_func=None):
        values_list = list(values_enum.keys())
        values_titiles = list(values_enum.values())

        group = Group(master, text=title, relief=tkinter.FLAT, opts=opts)
        super().__init__(group, values=values_titiles, state="readonly", width=width)
        self.type = "combobox"
        self.pack({"padx": 5, "pady": 0, "side": tkinter.TOP, "anchor": tkinter.NW})

        if selected_func:
            self.bind("<<ComboboxSelected>>", selected_func)
        if default in values_list:
            index = values_list.index(default)
            self.current(index)
        elif len(values_list) >= 1:
            self.current(0)


class Button(ttk.Button):
    def __init__(self, master, text, command, opts):
        super().__init__(master, text=text, command=command)
        self.type = "button"
        self.pack({"padx": 5, "pady": 5, **opts})


class ScrolledText(scrolltext.ScrolledText):
    def __init__(self, master, width, opts):
        super().__init__(master, width=width, wrap="word")
        self.type = "scrolled_text"
        self.pack(opts)


class TextInput(ttk.Entry):
    def __init__(self, master, title, width, validation_func, opts):
        group = Group(master, text=title, relief=tkinter.FLAT, opts=opts)
        value = tkinter.StringVar()
        validatecommand = group.register(validation_func)
        super().__init__(
            group,
            textvariable=value,
            width=width,
            validate="focusout",
            validatecommand=(validatecommand, "%P"),
            state="normal",
        )
        self.type = "text_input"
        self.pack({"padx": 5, "pady": 0, "side": tkinter.TOP, "anchor": tkinter.NW})


class Viewport(scroll_frame.ScrollFrame):
    def __init__(self, master):
        super().__init__(master)
        self.type = "viewport"
        self.pack({"side": tkinter.LEFT, "fill": tkinter.BOTH, "expand": True})


class Row(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.type = "row"
        self.pack(padx=5, pady=5, side=tkinter.TOP, fill="x", expand="no")


class Notebook(ttk.Notebook):
    def __init__(self, master, opts):
        super().__init__(master)
        self.type = "notebook"
        self.pack(**opts)

        self.tabs = []

    def create_tab(self, title):
        tab = NotebookTab(self)
        self.add(tab, text=title)

        viewport = Viewport(tab)


class NotebookTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.type = "tab"


class Frame(ttk.Frame):
    def __init__(self, master, opts, height=0):
        super().__init__(master, height=height)
        self.pack({"padx": 5, "pady": 5, **opts})
        self.type = "frame"
