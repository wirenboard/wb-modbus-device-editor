import queue
import sys
import threading
import tkinter
import traceback

import pymodbus

from . import modbus_client, template_manager, tk_threading, ui_manager


class App:
    max_col = 2  # количество колонок с виджетами +1

    def __init__(self):
        # создаём объекты для работы
        self.ui = ui_manager.UiManager()
        self.ui.btn_open_template.bind("<ButtonPress-1>", self.btn_open_template_click)
        self.ui.btn_read_params.bind("<ButtonPress-1>", self.btn_read_params_click)
        self.ui.btn_write_params.bind("<ButtonPress-1>", self.btn_write_params_click)

        self.template_manager = template_manager.TemplateManager()
        self._template = None
        self.io_running = False
        self.io_lock = threading.Lock()

        self.client = None

        if self.template_manager.update_needed:
            self.ui.win.after(100, self.btn_update_template_click)
        else:
            self.ui.write_log("Настройте параметры подключения и откройте шаблон.")

        self.ui.win.mainloop()

    def btn_update_template_click(self):

        with self.io_lock:
            if self.io_running:
                self.ui.write_log("Выполняется операция ввода/вывода, дождитесь завершения")
                return

        self.ui.write_log("Обновление шаблонов, пожалуйста подождите. Это может занять около минуты.")

        # проверяем поток с обновлением шаблонов пореже - раз в 10 секунд чтобы не висел UI
        tk_threading.TaskInThread(
            self.ui.win,
            self.template_manager.update_templates,
            callback=self.btn_update_templates_callback,
            errback=self.btn_update_templates_errback,
            polling=10000,
        )

        with self.io_lock:
            self.io_running = True

    def btn_update_templates_callback(self, result):
        self.ui.write_log("Обновление завершено. Настройте параметры подключения и откройте шаблон.")
        with self.io_lock:
            self.io_running = False

    def btn_update_templates_errback(self, error):
        self.ui.write_log(f"Ошибка при обновлении шаблонов: {error}")
        with self.io_lock:
            self.io_running = False

    # действие при нажатии на кнопку Открыть шаблон
    def btn_open_template_click(self, event):

        with self.io_lock:
            if self.io_running:
                self.ui.write_log("Выполняется операция ввода/вывода, дождитесь завершения")
                return

        templates_dir = self.template_manager.templates_dir
        file_path = self.ui.open_file(templates_dir)
        if not file_path:
            return

        # удаляем виджеты от предыдущего шаблона
        self.ui.delete_widgets()

        self.ui.write_log("Чтение файла {}".format(file_path))
        tk_threading.TaskInThread(
            self.ui.win,
            self.load_template,
            kwargs={"file_path": file_path},
            callback=self.open_template_callback,
            errback=self.open_template_errback,
        )

        with self.io_lock:
            self.io_running = True

    def load_template(self, file_path):
        return self.template_manager.open_template(file_path)

    def open_template_errback(self, error):
        self.ui.write_log(f"Ошибка при открытии шаблона: {error}")
        with self.io_lock:
            self.io_running = False

    def open_template_callback(self, result):
        self._template = result

        self.create_interface()

        self.ui.write_log(f"Чтение шаблона завершено.")

        with self.io_lock:
            self.io_running = False

    def create_interface(self):
        # если у нас есть параметры без групп, например, режимы — создаём для них отдельную вкладку
        parameters = self._template.get_parameters_by_group_id(None)

        if len(parameters) > 0:
            parent = self.ui.create_tab("mode_params_group", "Режим")
            curr_frame = parent.curr_frame

            # перебираем безгрупные параметры и создаём для них виджеты
            for id, parameter in parameters.items():
                self.create_widget(id, parent, parameter)

        # создаём вкладки из групп без поля group
        if self.create_pages():
            # создаём группы внутри вкладок
            if self.create_groups():
                self.widgets_hide_by_condition()

    # создание страниц
    def create_pages(self):
        self.ui.write_log("Создаю вкладки.")

        try:
            groups = self._template.properties["device"]["groups"]
            if groups is not None:

                for id, group in groups.items():
                    # если у группы нет родителя, то создаём вкладку
                    if not group.get("group"):
                        title = self._template.translate(group["title"])
                        group_widget = self.ui.create_tab(id, title)
                        group_widget.condition = group.get("condition")

            return True
        except Exception as e:
            self.ui.write_log("Ошибка:")
            self.ui.write_log(traceback.format_exc())
            return False

    # создание групп
    def create_groups(self):
        self.ui.write_log("Создаю группы.")

        groups = self._template.properties["device"]["groups"]

        try:
            for id, group in groups.items():
                title = self._template.translate(group["title"])
                parent_id = group.get("group")
                parent = self.ui.get_widget(parent_id)

                # а тут магия распределения групп по вкладкам
                if parent != None:  # если у группы нет родителя, то есть это у нас вкладка, то
                    # проверяем, не вышли ли за пределы максимального числа колонок
                    if parent.curr_col < self.max_col:
                        # если не вышли, то получаем текущий фрейм (строку) и потом увеличиваем счётчик колонок
                        curr_frame = self.get_current_frame(parent)
                        parent.curr_col += 1
                    else:
                        # если счётчик колонок равен максимальном числу колонок на вкладке, то
                        # создаём новую строку, обнуляем счётчик колонок и увеличиваем счётчик строк
                        curr_frame = self.ui.create_row(parent, parent_id + "_row")
                        parent.curr_frame = curr_frame
                        parent.curr_col = 0
                        parent.curr_row += 1

                    # создаём новую группу с учётом магии выше
                    group_widget = self.ui.create_group(
                        curr_frame, id, title, side=tkinter.LEFT, anchor=tkinter.NW
                    )
                    # добавляем поле condition — это для того, чтобы понимать, надо ли показывать
                    # эту группу при выбранных параметрах
                    group_widget.condition = group.get("condition")
                else:
                    # а если родитель у группы есть, то получаем текущий виджет с нужным id
                    group_widget = self.ui.get_widget(id)

                # если виджет группы существует — создаём параметры в ней
                if group_widget is not None:
                    self.create_params(id, group_widget)
                else:
                    print("Виджет для группы {} не существует".format(id))
            return True
        except Exception as e:
            self.ui.write_log("Ошибка:")
            self.ui.write_log(traceback.format_exc())
            return False

    def create_params(self, group_id, group_widget):
        parameters = self._template.get_parameters_by_group_id(group_id)
        parent = self.get_current_frame(group_widget)

        for id, parameter in parameters.items():
            widget = self.create_widget(id, parent, parameter)
            widget.condition = parameter.get("condition")
            parent.condition = parameter.get("condition")

    def get_value_type_type(self, param):
        if "enum" in param:
            return "enum"

        if "scale" in param:
            return "double"

        return "int"

    def create_widget(self, id, parent, param):
        value_type = self.get_value_type_type(
            param
        )  # от типа значения зависит тип и настройки создаваемого виджета

        title = self._template.translate(param.get("title"))
        default = param.get("default")

        # есть перечисление — создаём combobox
        if value_type == "enum":
            enum = self._template.get_parameter_enum(id)
            widget = self.ui.create_combobox(
                parent=parent,
                id=id,
                title=title,
                dic=enum,
                default=default,
                width=50,
                side=tkinter.TOP,
                anchor=tkinter.NW,
            )
            widget.bind("<<ComboboxSelected>>", self.combobox_selected)
        # если это число, создаём spinbox и указываем ему нужный формат
        if value_type == "int" or value_type == "double":
            min_ = param.get("min")
            max_ = param.get("max")
            description = param.get("description")
            widget = self.ui.create_spinbox(
                parent=parent,
                id=id,
                title=title,
                min_=min_,
                max_=max_,
                value_type=value_type,
                default=default,
                width=5,
                description=description,
                side=tkinter.TOP,
                anchor=tkinter.NW,
            )

        return widget

    # получаем текущий фрейм
    def get_current_frame(self, parent):
        if parent.type == "tab":
            curr_frame = parent.curr_frame
        else:
            curr_frame = parent
        return curr_frame

    def combobox_selected(self, event):
        self.widgets_hide_by_condition()

    def widgets_hide_by_condition(self):
        values = self.ui.get_values()
        old_values = {}
        iterations = 0
        widgets = self.ui.get_widgets()

        while old_values != values and iterations < 10:
            for key, item in widgets.items():

                if item.type in ["group", "spinbox", "combobox"]:

                    if hasattr(item, "condition"):
                        condition = item.condition
                        if condition != None:
                            visible = self._template.calc_parameter_condition(condition, values)
                        else:
                            visible = True

                        if visible:
                            self.ui.widget_show(key)
                        else:
                            self.ui.widget_hide(key)
            old_values = values.copy()
            values = self.ui.get_values()
            iterations += 1

    def btn_read_params_click(self, event):

        with self.io_lock:
            if self.io_running:
                self.ui.write_log("Выполняется операция ввода/вывода, дождитесь завершения")
                return

        if self._template is None:
            self.ui.write_log("Сначала откройте шаблон")
            return

        parameters = self._template.properties["device"]["parameters"]
        if not parameters:
            self.ui.write_log(f"Нет доступных для ректирования параметров")
            return

        mb_params = self.ui.get_modbus_params()
        if mb_params["mode"] == "RTU":
            self.client = modbus_client.ModbusRTUClient(mb_params)
        elif mb_params["mode"] == "TCP":
            self.client = modbus_client.ModbusTCPClient(mb_params)
        elif mb_params["mode"] == "RTU over TCP":
            self.client = modbus_client.ModbusRTUoverTCPClient(mb_params)
        else:
            self.ui.write_log("Выбран неизвестный режим подключения!")
            return

        if not self.client.connect():
            if mb_params["mode"] == "RTU":
                msg = f"Невозможно открыть порт {mb_params['port']}"
            elif mb_params["mode"] in ["TCP", "RTU over TCP"]:
                msg = f"Невозможно открыть порт {mb_params['ip']}:{mb_params['port']}"
            self.ui.write_log(msg)
            return

        self.ui.write_log(f"Выполняется чтение параметров устройства")
        tk_threading.TaskInThread(
            self.ui.win,
            self.read_params_from_modbus,
            kwargs={"client": self.client, "slave_id": int(mb_params["slave_id"]), "params": parameters},
            callback=self.read_params_from_modbus_callback,
            errback=self.read_params_from_modbus_errback,
        )

        with self.io_lock:
            self.io_running = True

    def read_params_from_modbus_callback(self, result):
        try:
            failed = False
            for id, param, value in result:
                if value is None:
                    self.ui.write_log(
                        f"Не удалось прочитать параметр {self._template.translate(param['title'])} {param['address']}"
                    )
                    self.ui.widget_disable(id)
                    failed = True
                    continue

                try:
                    self.ui.set_value(id, value, scale=param.get("scale"))
                    self.ui.widget_enable(id)
                except ValueError:
                    self.ui.widget_disable(id)
                    self.ui.write_log(
                        f"Не удалось обработать прочитанное значение {value} параметра \"{self._template.translate(param['title'])}\" регистр {param['address']}. Параметр скрыт."
                    )

            if failed:
                self.ui.write_log(
                    "Не удалось прочитать некоторые параметры. Возможно их нет в этой версии прошивки устройства. Такие параметры будут недоступны для редактирования."
                )
            else:
                self.widgets_hide_by_condition()
                self.ui.write_log("Чтение параметров завершено")
        finally:
            self.client.disconnect()

            with self.io_lock:
                self.io_running = False

    def read_params_from_modbus_errback(self, error: Exception):
        self.ui.write_log(f"Ошибка во время чтения параметов: {error}")
        self.client.disconnect()

        with self.io_lock:
            self.io_running = False

    def read_params_from_modbus(self, client, slave_id, params):
        result = []

        for id, param in params.items():

            # если у параметра нет адреса, то его значение можно задать только извне и нельзя прочитать
            address = param.get("address")
            if address is None:
                continue

            # адреса пишут то в HEX то в DEC, надо определять и преобразовывать в DEC
            address = int(address, 0) if isinstance(address, str) else int(address)

            # бывает, что тип регистра не пишет, надо присвоить значение по умолчанию
            reg_type = "holding" if param.get("reg_type") is None else param.get("reg_type")

            if reg_type == "holding":
                try:
                    value = client.read_holding(slave_id=slave_id, reg_address=address)
                    result.append((id, param, value))
                except pymodbus.exceptions.ModbusIOException as e:
                    raise RuntimeError(
                        "Нет связи с устройством. Проверьте, что указаны верные параметры подключения, адрес устройства и выбран верный шаблон"
                    ) from e

        return result

    def btn_write_params_click(self, event):
        with self.io_lock:
            if self.io_running:
                self.ui.write_log("Выполняется операция ввода/вывода, дождитесь завершения")
                return

        if self._template is None:
            self.ui.write_log("Сначала откройте шаблон")
            return

        parameters = self._template.properties["device"]["parameters"]
        if not parameters:
            self.ui.write_log(f"Нет доступных для ректирования параметров")
            return

        mb_params = self.ui.get_modbus_params()
        if mb_params["mode"] == "RTU":
            self.client = modbus_client.ModbusRTUClient(mb_params)
        elif mb_params["mode"] == "TCP":
            self.client = modbus_client.ModbusTCPClient(mb_params)
        elif mb_params["mode"] == "RTU over TCP":
            self.client = modbus_client.ModbusRTUoverTCPClient(mb_params)
        else:
            self.ui.write_log("Выбран неизвестный режим подключения!")
            return

        if not self.client.connect():
            self.ui.write_log(f"Невозможно открыть порт {mb_params['port']}")
            return

        self.ui.write_log(f"Выполняется запись параметров")
        tk_threading.TaskInThread(
            self.ui.win,
            self.write_params_to_modbus,
            kwargs={"client": self.client, "slave_id": int(mb_params["slave_id"]), "params": parameters},
            callback=self.write_params_from_modbus_callback,
            errback=self.write_params_from_modbus_errback,
        )

        with self.io_lock:
            self.io_running = True

    def write_params_to_modbus(self, client, slave_id, params):
        result = []

        for id, param in params.items():
            reg_type = "holding" if param.get("reg_type") is None else param.get("reg_type")

            # если у параметра нет адреса, то его значение можно задать только извне и нельзя прочитать
            address = param.get("address")
            if address is None:
                continue

            address = int(address, 0) if isinstance(address, str) else int(address)

            if reg_type == "holding":
                value = self.ui.get_value(id)
                if value == None:
                    continue

                if "scale" in param:
                    value = float(value) / param["scale"]

                try:
                    value = client.write_holding(slave_id, address, value)
                    result.append((id, param, value))
                except pymodbus.exceptions.ModbusIOException as e:
                    raise RuntimeError(
                        "Нет связи с устройством. Проверьте, что указан верный адрес устройства и выбран верный шаблон"
                    ) from e

        return result

    def write_params_from_modbus_callback(self, result):
        try:
            failed = False
            for id, param, value in result:
                if value is None:
                    self.ui.write_log(
                        f"Не удалось записать параметр {self._template.translate(param['title'])} {param['address']}"
                    )
                    failed = True
            if failed:
                self.ui.write_log(
                    "Не удалось записать некоторые параметры. Возможно их нет в этой версии прошивки устройства. Такие параметры будут недоступны для редактирования."
                )
            else:
                self.ui.write_log("Запись параметров завершена.")
        finally:
            self.client.disconnect()

            with self.io_lock:
                self.io_running = False

    def write_params_from_modbus_errback(self, error):
        self.ui.write_log(f"Ошибка во время записи параметов: {error}")
        self.client.disconnect()

        with self.io_lock:
            self.io_running = False

    # взято из интернета: https://ru.stackoverflow.com/a/1413836
    def numeral_noun_declension(self, number, nominative_singular, genetive_singular, nominative_plural):
        diglast = number % 10
        return (
            (number in range(5, 20))
            and nominative_plural
            or (1 in (number, diglast))
            and nominative_singular
            or ({number, diglast} & {2, 3, 4})
            and genetive_singular
            or nominative_plural
        )


def main(argv):
    App()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
