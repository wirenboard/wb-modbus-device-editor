import json
import traceback


class TemplateReader:
    template = None

    def read_template(self, file_patch):
        with open(file_patch, "r", encoding="utf-8") as j:
            self.template = json.load(j)

    def get_title(self):
        return self.template.get("title")

    def get_device_name(self):
        return self.template["device"].get("name")

    def get_groups(self):
        return self.template["device"].get("groups")

    def get_params(self):
        return self.template["device"].get("parameters")

    def get_setups(self):
        return self.template["device"].get("setups")

    def get_params_by_group(self, group_id):
        res = []
        params = self.get_params()
        for param in params:
            if param.get("group") == group_id:
                res.append(param)
        return res

    def get_group_by_param_id(self, param_id):
        params = self.get_params()
        for (i,) in range(len(params)):
            param = params[i]
            if param.get("id") == param_id:
                return param.get("group")

    def get_params_without_group(self):
        res = {}
        params = self.get_params()
        for i in range(len(params)):
            param = params[i]
            if param.get("group") == None:
                res[i] = param
        return res

    def get_translate(self, string, language="ru"):
        device = self.template["device"]

        if "translations" in device:
            if language in device["translations"]:
                if string in device["translations"][language]:
                    return device["translations"][language][string]
                else:
                    return string
            else:
                return string
        else:
            return string

    def get_enum_dic(self, param):
        enum = param["enum"]
        enum_titles = param["enum_titles"]

        for i in range(len(enum_titles)):
            enum_titles[i] = self.get_translate(enum_titles[i])

        dic = {"enum": enum, "enum_titles": enum_titles}
        return dic

    def calc_condition(self, condition, values):
        try:
            return eval(condition, {}, values)
        except Exception as e:
            raise Exception("Ошибка в выражении: {}\n {}".format(condition, traceback.format_exc()))

            return False
