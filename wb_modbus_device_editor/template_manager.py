import os
import tarfile

import jinja2
import requests
import semantic_version
import commentjson


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
            dict_info = commentjson.load(json_template)
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
            dict_info = commentjson.load(json_template)
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
        if parameters is not None:
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
            condition = condition.replace("||", " or ").replace("&&", " and ")
            return eval(condition, {"__builtins__": None}, values)
        except Exception as error:
            raise RuntimeError(f"Ошибка в выражении: {condition}\n") from error

    def translate(self, title, language="ru"):
        if (
            self._properties["device"]["translations"] is not None
            and language in self._properties["device"]["translations"]
        ):
            return self._properties["device"]["translations"][language].get(title, title)

        return title


class TemplateManager:
    _DEFAULT_TEMPLATES_DIR = "templates"
    _VERSION_FILENAME = "version"
    _OWNER = "wirenboard"
    _REPO = "wb-mqtt-serial"

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

    def _get_latest_master_tag(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/tags"
        tags = requests.get(url, timeout=1).json()  # get 30 latest tags bu default
        for tag in tags:
            version = semantic_version.Version.parse(tag["name"].replace("v", ""))
            if version[3:4] == ((),):  # master tags haven't prerelease and build parts
                return tag["name"]

    def _download_templates(self, owner, repo, tag, templates_dir):
        tarball_url = f"https://api.github.com/repos/{owner}/{repo}/tarball/tags/{tag}"
        # release_info = requests.get(release_url, timeout=1).json()
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
        latest_tag = self._get_latest_master_tag(self._OWNER, self._REPO)
        latest_version = latest_tag.replace("v", "")
        current_version = None

        if os.path.exists(self._version_filepath):
            with open(self._version_filepath, encoding="utf-8") as version_file:
                current_version = version_file.readline()

        if (
            not os.path.exists(self._templates_dir)
            or current_version is None
            or (semantic_version.Version(latest_version) > semantic_version.Version(current_version))
        ):
            self._download_templates(self._OWNER, self._REPO, latest_tag, self._templates_dir)
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

    def open_template(self,template_path):
        template = Template(template_path)
        template.update_properties()
        return template
