import os
import pathlib
import platform
import re
import tarfile

import appdirs
import commentjson
import jinja2
import requests
import semantic_version


class TemplateException(Exception):
    pass


class Template:
    def __init__(self, template_path, full_read: bool):
        self._template_path = template_path
        if full_read:
            self._properties = self._get_template_full_info(self._template_path)
        else:
            self._properties = self._get_template_basic_info(self._template_path)

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
        if source == None or isinstance(source, dict):
            return source

        result = {}
        for item in source:
            id = item.pop("id")
            result[id] = item

        return result

  
    import re
    from typing import List, Dict, Any

    def convert_parameters_list_to_dict(self, source: Any) -> Any:
        """
        Преобразует список параметров в {new_id: param_dict}, при этом:
        - Генерирует уникальные new_id вида old_id_1, old_id_2, …
        - В condition убирает ВСЕ упоминания старых id:
            * isDefined(old_id) → либо "('new_id' in locals())" (singleton)
                            либо "( 'n1' in locals() or 'n2' in locals() … )"
            * Сам old_id (в equality/логике) → либо "new_id" (singleton)
                                            либо "(new1 or new2 or …)" (дубликаты)
        """
        # 1) Если None или dict — возвращаем без изменений
        if source is None or isinstance(source, dict):
            return source

        # 2) Ожидаем список параметров
        if not isinstance(source, list):
            raise TypeError(f"Ожидался список параметров или dict, получили {type(source)}")

        # 3) Считаем, сколько раз встречается каждый old_id
        counts: Dict[str, int] = {}
        for item in source:
            old = item.get("id")
            if not old:
                raise ValueError("Каждый параметр должен иметь поле 'id'")
            counts[old] = counts.get(old, 0) + 1

        # 4) Строим полную мапу old_id → [old_id_1, old_id_2, …]
        mapping_all: Dict[str, List[str]] = {
            old: [f"{old}_{i}" for i in range(1, cnt + 1)]
            for old, cnt in counts.items()
        }

        # 5) Самая магия: клонируем, делаем new_id и «раскрашиваем» условие
        local_counts: Dict[str, int] = {}
        new_params: List[Dict[str, Any]] = []

        for item in source:
            old = item["id"]
            # порядковый номер клона
            idx = local_counts.setdefault(old, 0)
            new_id = mapping_all[old][idx]
            local_counts[old] += 1

            clone = item.copy()
            clone["id"] = new_id

            cond = clone.get("condition")
            if cond:
                # 5a) isDefined(old) → объединение по new_id
                for oid, nids in mapping_all.items():
                    # шаблон точно на isDefined(old)
                    cond = re.sub(
                        rf"isDefined\(\s*{re.escape(oid)}\s*\)",
                        # singleton?
                        (f"('{nids[0]}' in locals())"
                        if len(nids) == 1
                        else # или or-цепочка всех вариантов
                        "(" + " or ".join(f"'{nid}' in locals()" for nid in nids) + ")"),
                        cond
                    )

                # 5b) замена самих вхождений old → new (или цепочка new)
                for oid, nids in mapping_all.items():
                    repl = (
                        nids[0]
                        if len(nids) == 1
                        else "(" + " or ".join(nids) + ")"
                    )
                    cond = re.sub(
                        rf"(?<!\w){re.escape(oid)}(?!\w)",
                        repl,
                        cond
                    )

                clone["condition"] = cond

            new_params.append(clone)

        # 6) Собираем итоговый словарь и убираем id из значений
        result: Dict[str, Dict[str, Any]] = {}
        for p in new_params:
            nid = p.pop("id")
            result[nid] = p

        return result


    def _get_template_full_info(self, template_path):
        with open(template_path, encoding="utf-8") as json_template:
            dict_info = commentjson.load(json_template)
            groups = dict_info["device"].get("groups", {})  # groups and parameters may have dict type
            parameters = dict_info["device"].get("parameters", {})
            full_info = {
                "title": dict_info.get("title", None),
                "device": {
                    "name": dict_info["device"]["name"],
                    "groups": self._convert_list_to_dict(groups),
                    "parameters": self.convert_parameters_list_to_dict(parameters),
                    "translations": dict_info["device"].get("translations"),
                    "setup": dict_info["device"].get("setup", None),
                },
            }
            return full_info

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
        for i, title in enumerate(enum_titles):
            enum_titles[i] = self.translate(title)

        return {"enum": enum, "enum_titles": enum_titles}

    def calc_parameter_condition(self, condition, values):
        try:
            condition = condition.replace("||", " or ").replace("&&", " and ")
            condition = re.sub(r"isDefined\(([A-Za-z1-9_]+)\)", r"('\g<1>' in locals())", condition)
            return eval(condition, {"__builtins__": None, "locals": locals}, values)
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
    _DEFAULT_TEMPLATES_DIR = appdirs.user_data_dir(appname="wb-modbus-device-editor", appauthor="WirenBoard")
    _SHA_FILENAME = "sha"  # commit sha
    _OWNER = "wirenboard"
    _REPO = "wb-mqtt-serial"

    def __init__(self, templates_dir: str = _DEFAULT_TEMPLATES_DIR) -> None:
        self._templates_dir = templates_dir
        self._sha_filepath = os.path.join(self._templates_dir, self._SHA_FILENAME)
        self._need_update, self._latest_sha = self._check_update_needed(
            self._sha_filepath, self._templates_dir
        )
        self._templates = {}

    @property
    def templates_dir(self):
        return self._templates_dir

    @property
    def templates(self) -> list:
        return self._templates

    @property
    def update_needed(self):
        return self._need_update

    def _check_update_needed(self, sha_filepath, templates_dir) -> bool:
        latest_sha = self._get_latest_master_sha(self._OWNER, self._REPO)
        current_sha = None

        if os.path.exists(sha_filepath):
            with open(sha_filepath, encoding="utf-8") as sha_file:
                current_sha = sha_file.readline()

        return (
            not os.path.exists(templates_dir) or current_sha is None or current_sha != latest_sha
        ), latest_sha

    def _get_templates_from_tar(self, tar_file: tarfile.TarFile):
        for member in tar_file:
            path_list = os.path.normpath(member.name).split(os.sep)
            if member.isfile() and path_list[1] == "templates":
                member.name = os.path.basename(member.name)
                yield member

    def _get_latest_master_sha(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/git/matching-refs/heads/master"
        res = requests.get(url, timeout=1).json()
        return res[0]["object"]["sha"]

    def _download_templates(self, owner, repo, templates_dir):
        tarball_url = f"https://api.github.com/repos/{owner}/{repo}/tarball/master"
        source_raw = requests.get(tarball_url, timeout=1, stream=True)
        source_tar = tarfile.open(fileobj=source_raw.raw, mode="r|gz")

        source_tar.extractall(path=templates_dir, members=self._get_templates_from_tar(source_tar))

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
        if self._need_update:
            self._download_templates(self._OWNER, self._REPO, self._templates_dir)

            with open(self._sha_filepath, "w", encoding="utf-8") as sha_file:
                sha_file.write(self._latest_sha)

            for template_name in os.listdir(self._templates_dir):

                if template_name == self._SHA_FILENAME:
                    continue

                template_path = os.path.abspath(os.path.join(self._templates_dir, template_name))
                template = Template(template_path, full_read=False)
                if template.properties.get("deprecated", None):
                    os.remove(template_path)
                    continue

    def open_template(self, template_path):
        template = Template(template_path, full_read=True)
        return template
