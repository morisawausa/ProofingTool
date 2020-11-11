import os
import json

TEMPLATE_DIRECTORY = 'data'


class OCCTemplatesView():
    def __init__(self):
        self.data = self.parseTemplateDirectory(TEMPLATE_DIRECTORY)


    def parseTemplateDirectory(self, directory):
        if not os.path.isdir(directory): return []

        templates_files = filter(lambda f: '.json' in f, os.listdir(directory))
        templates = []

        for template_name in templates_files:
            with open(os.path.join(directory, template_name), 'r') as template_file:
                try:
                    template = json.load(template_file)
                    row, valid = self.validateAndFormatTemplate(template)
                    if valid:
                        templates.append(row)

                except Exception as error:
                    print(error)

        return templates


    def validateAndFormatTemplate(self, template):
        return template, True


    def getTemplateList(self):
        pass

    def getTemplate(self, index):
        pass
