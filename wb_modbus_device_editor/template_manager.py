import os
import tarfile

import jinja2
import jsonslicer
import requests
import semantic_version


class Template:
    def __init__(self, template_path):
        self._template_path = template_path
        self._basic_properties = self._get_template_basic_info(self._template_path)
        self._properties = None

    @property
    def basic_properties(self) -> dict:
        return self._basic_properties

    @property
    def properties(self) -> dict:
        return self._properties

    def _get_template_basic_info(self, template_path):
        with open(template_path, encoding="utf-8") as json_template:
            for info in jsonslicer.JsonSlicer(
                json_template, (""), path_mode="full", yajl_allow_comments=True
            ):
                dict_info = info[0]
                basic_info = {
                    "title": dict_info.get("title", None),
                    "device_type": dict_info.get("device_type", None),
                    "group": dict_info.get("device_type", None),
                    "deprecated": dict_info.get("deprecated", None),
                    "translates": dict_info.get("translates", None),
                }
                return basic_info

    def _convert_list_to_dict(self, source):
        if source == None or type(source) == dict:
            return source

        result = {}
        for item in source:
            id = item["id"]
            item.pop("id")
            result[id] = item
        return result

    def _get_template_full_info(self, template_path):
        with open(template_path, encoding="utf-8") as json_template:
            for info in jsonslicer.JsonSlicer(
                json_template, (""), path_mode="full", yajl_allow_comments=True
            ):
                dict_info = info[0]
                groups = dict_info["device"].get("groups")  # groups and parameters mey have dict type
                parameters = dict_info["device"].get("parameters")
                full_info = {
                    "title": dict_info.get("title", None),
                    "device": {
                        "name": dict_info["device"]["name"],
                        "groups": self._convert_list_to_dict(groups),
                        "parameters": self._convert_list_to_dict(parameters),
                        "translations": dict_info["device"].get("translations"),
                        "setup": dict_info["device"].get("setup", None),
                    },
                }
                return full_info

    def update_properties(self):
        self._properties = self._get_template_full_info(self._template_path)

    def get_parameters_by_group_id(self, group_id) -> list:
        if self._properties is None:
            return None

        parameters = self._properties["device"]["parameters"]
        result = {}
        for id, parameter in parameters.items():
            if parameter.get("group") == group_id:
                result.update({id: parameter})
        return result

    def get_parameter_enum(self, parameter_id) -> dict:
        parameter = self._properties["device"]["parameters"][parameter_id]
        enum = parameter["enum"]
        enum_titles = parameter["enum_titles"]
        for enum_title in enum_titles:
            enum_title = self.translate(enum_title)

        return {"enum": enum, "enum_titles": enum_titles}

    def calc_parameter_condition(self, condition, values):

        try:
            condition = condition.replace("||", " or ").replace("&&", " and ").replace("!", " not ")
            return eval(condition, {}, values)
        except (SyntaxError, SyntaxError) as error:
            raise RuntimeError(f"Ошибка в выражении: {condition}\n") from error

    def translate(self, title, language="ru"):
        if (
            "translations" in self._properties["device"]
            and language in self._properties["device"]["translations"]
        ):
            return self._properties["device"]["translations"][language].get(title, title)

        return title


class TemplateManager:
    _DEFAULT_TEMPLATES_DIR = "templates"
    _VERSION_FILENAME = "version"
    _RELEASE_URL = "https://api.github.com/repos/wirenboard/wb-mqtt-serial/releases/latest"

    def __init__(self, templates_dir: str = _DEFAULT_TEMPLATES_DIR) -> None:
        self._templates_dir = templates_dir
        self._version_filepath = os.path.join(self._templates_dir, self._VERSION_FILENAME)
        self._templates = {}

    @property
    def templates_dir(self):
        return self._templates_dir

    @property
    def templates(self) -> list:
        return self._templates

    def _get_templates_from_tar(self, tar_file: tarfile.TarFile):
        for member in tar_file:
            path_list = os.path.normpath(member.name).split(os.sep)
            if member.isfile() and path_list[1] == "templates":
                member.name = os.path.basename(member.name)
                yield member

    def _download_templates(self, tarball_url, templates_dir):
        source_raw = requests.get(tarball_url, timeout=1, stream=True)
        source_tar = tarfile.open(fileobj=source_raw.raw, mode="r|gz")
        source_tar.extractall(
            path=templates_dir,
            members=self._get_templates_from_tar(source_tar),
            filter="data",
        )

        template_loader = jinja2.FileSystemLoader(searchpath=templates_dir)
        template_env = jinja2.Environment(loader=template_loader)

        for file in os.listdir(templates_dir):
            if file.endswith(".jinja"):
                dest_file = os.path.join(templates_dir, file.removesuffix(".jinja"))
                template_file = template_env.get_template(file)
                template_file.stream().dump(dest_file)

        for template_name in os.listdir(self._templates_dir):
            template_path = os.path.abspath(os.path.join(self._templates_dir, template_name))
            if template_name.endswith(".jinja"):
                os.remove(template_path)
                continue

    def update_templates(self):
        response = requests.get(self._RELEASE_URL, timeout=1).json()
        latest_version = response["tag_name"].removeprefix("v")
        current_version = None

        if os.path.exists(self._version_filepath):
            with open(self._version_filepath, encoding="utf-8") as version_file:
                current_version = version_file.readline()

        if (
            not os.path.exists(self._templates_dir)
            or current_version is None
            or (semantic_version.Version(latest_version) > semantic_version.Version(current_version))
        ):
            self._download_templates(response["tarball_url"], self._templates_dir)
            with open(self._version_filepath, "w", encoding="utf-8") as version_file:
                version_file.write(latest_version)

        for template_name in os.listdir(self._templates_dir):

            if template_name == self._VERSION_FILENAME:
                continue

            template_path = os.path.abspath(os.path.join(self._templates_dir, template_name))
            template = Template(template_path)
            if template.basic_properties.get("deprecated", None):
                os.remove(template_path)
                continue

            self._templates[template_path] = template
