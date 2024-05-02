# py-modbus-device-editor
Утилита редактирования параметров Modbus-устройств

![Screenshot](images/main_window.png)

Артефакты, доступные для установки, вы можете взять в списке релизов.

# Linux

Установите пакет, используя пакетный менеджер.
Для запуска утилиты наберите в командной строке

```sh
wb-modbus-device-editor
```

 # Windows

Распакуйте архив в удобное вам расположение, распакованные файлы должны находиться в одной директории. Внутри архива находится исполняемый .exe файл и папка с внутренними ресурсами утилиты. 

Для удобства использования вы можете сделать ярлык запускаемого exe-файла и поместить его на ваш рабочий стол.

# Использование

При запуске утилита проверяет наличие обновлений репозитория wb-mqtt-serial, и при выпуске новой версии подгружает свежие версии шаблонов. 

Для настройки параметров подключения выберите в выпадающих списках слева нужные значения. Затем нажмите кнопку "Открыть шаблон". Откроется папка с файлами шаблонов, выберите из них нужный. После этого утилита создаст в интерфейсе виджеты, соответствующие параметрам и групам выбранного шаблона. Для больших файлов время отображения может составлять несколько секунд.

Для того чтобы прочитать текущие значения параметров, нажмите кнопку "Читать параметры". На основе прочитанных значений изменится внешний вид: параметры, недоступные для редактирования (например, ввиду выбранного режима работы) будут скрыты, а доступные - показаны.

Для того чтобы записать текущие значения после просмотра и редактирования, нажмите "Записать параметры", и утилита обновит параметры вашего устройства.