# encoding=utf-8
# created @2024/5/31
# created by zhanzq
#
import os
import re
import json


class TPL_Item(dict):
    def __init__(self, domain, intent, slot_names, full_template, tpl):
        self.domain = domain
        self.intent = intent
        self.slot_names = slot_names
        self.full_template = full_template
        self.tpl = tpl
        self.update({
            'domain': domain,
            'intent': intent,
            'slot_names': slot_names,
            'full_template': full_template,
            'tpl': tpl
        })

    def __getitem__(self, key):
        return self.__dict__.get(key)


class TPL:
    def __init__(self, keyword_dct_or_path):
        if type(keyword_dct_or_path) is dict:
            self.keyword_dct = keyword_dct_or_path
        else:
            assert os.path.exists(keyword_dct_or_path), f"keyword_dct file not found in path: {keyword_dct_or_path}"
            try:
                with open(keyword_dct_or_path, "r") as reader:
                    self.keyword_dct = json.load(fp=reader)
            except:
                print(f"keyword_dct file is empty or its content not json")
                self.keyword_dct = {}
        self.tpl_lst = []

    def load_tpl(self, tpl_path):
        with open(tpl_path, "r") as reader:
            tpl_dct = json.load(fp=reader)

            for domain, domain_dct in tpl_dct.items():
                for intent, intent_lst in domain_dct.items():
                    for template in intent_lst:
                        self.add_tpl(domain=domain, intent=intent, template=template)
        print(f"total loads {len(self.tpl_lst)} tpl items")

        return

    def add_tpl(self, domain, intent, template):
        full_template, slot_names = self.pre_process_template(template)
        tpl_item = TPL_Item(domain=domain, intent=intent, slot_names=slot_names, full_template=full_template,
                            tpl=template)
        self.tpl_lst.append(tpl_item)
        return

    def pre_process_template(self, template):
        keyword_dct = self.keyword_dct
        keywords = re.findall(pattern="{<(.*?)>}", string=template)
        for keyword in keywords:
            pattern_str = "{<" + keyword + ">}"
            repl_str = "(" + keyword_dct.get(keyword, keyword) + ")"
            template = template.replace(pattern_str, repl_str)
        slot_names = keywords

        return template, slot_names

    def match_tpl(self, query):
        for tpl_item in self.tpl_lst:
            domain = tpl_item.get("domain")
            intent = tpl_item.get("intent")
            slot_names = tpl_item.get("slot_names")
            tpl = tpl_item.get("tpl")
            full_template = tpl_item.get("full_template")
            if re.findall(pattern=full_template, string=query):
                # 使用正则表达式匹配query
                match = re.search(pattern=full_template, string=query)
                slots = dict(zip(slot_names, match.groups()))

                return domain, intent, slots

        return None, None, None


def main():
    query = "30分钟以后打开电灯"
    keyword_dct_path = "/Users/zhanzq/gitProjects/smart_light/data/keyword_dct.json"
    tpl_service = TPL(keyword_dct_or_path=keyword_dct_path)
    tpl_service.load_tpl(tpl_path="/Users/zhanzq/gitProjects/smart_light/data/template.json")
    domain, intent, slot = tpl_service.match_tpl(query=query)
    nlu_info = {
        "domain": domain,
        "intent": intent,
        "slot": slot
    }

    print(nlu_info)


if __name__ == "__main__":
    main()
