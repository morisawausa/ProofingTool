import os
import json
from GlyphsApp import *

TEMPLATE_DIRECTORY = 'data'


class OCCTemplatesView():
    def __init__(self):
        self.data = self.parseTemplateDirectory(TEMPLATE_DIRECTORY)


    def parseTemplateDirectory(self, directory):
        if not os.path.isdir(directory): return []

        templates_files = filter(lambda f: '.json' in f, os.listdir(directory))
        templates = []

        for i, template_name in enumerate(templates_files):
            with open(os.path.join(directory, template_name), 'r') as template_file:
                try:
                    template = json.load(template_file)
                    row = self.validateAndFormatTemplate(template_name, template, i)
                    templates.append(row)

                except Exception as error:
                    print(error)

        return templates


    def validateAndFormatTemplate(self, template_name, template, index):

        if template.has_key('name'):
            name = template['name']
        else:
            print('[%s]\t"%s" does not have a template name specified. Naming it "Template %i"' % (template_name, template_name, index))
            name = 'Template %i' % index

        if template.has_key('lines'):
            lines = []
            for linenum, line in enumerate(template['lines']):
                if not line.has_key('style'):
                    print('[%s]\tline %i has no style specified, skipping...' % (template_name, linenum))
                    continue

                if not line.has_key('size'):
                    print('[%s]\tline %i has no size specified, skipping...' % (template_name, linenum))
                    continue

                if len(filter(lambda m: m.name == line['style'], Glyphs.font.masters)) != 1:
                    print('[%s]\tline %i does not specify an existing master in this typeface, skipping...' % (template_name, linenum))
                    continue

                if not isinstance(line['size'], int):
                    print('[%s]\tline %i does not specify a numerical size, skipping...' % (template_name, linenum))
                    continue

                lines.append(line)

        else:
            print('[%s]\t"%s" does not have any lines specified. "' % (template_name, template_name))
            lines = []

        proof = {
            "margins": {
                "left": 20,
                "right": 70,
                "top": 20,
                "bottom": 100,
            },
            "padding": {
                "line": 20,
                "block": 20
            }
        }

        if template.has_key('proof'):
            if template['proof'].has_key('margins'):
                proof['margins']['left'] = template['proof']['margins']['left'] if hasattr(template['proof']['margins'], 'left') else 20
                proof['margins']['right'] = template['proof']['margins']['right'] if hasattr(template['proof']['margins'], 'right') else 70
                proof['margins']['top'] = template['proof']['margins']['top'] if hasattr(template['proof']['margins'], 'top') else 20
                proof['margins']['bottom'] = template['proof']['margins']['bottom'] if hasattr(template['proof']['margins'], 'bottom') else 100

            if template['proof'].has_key('padding'):
                proof['padding']['line'] = template['proof']['padding']['line'] if hasattr(template['proof']['padding'], 'line') else 20
                proof['padding']['block'] = template['proof']['padding']['block'] if hasattr(template['proof']['padding'], 'block') else 20

        else:
            print('[%s]\t"%s" does not specify margin and padding information. Setting defaults. "' % (template_name, template_name))


        return template


    def getTemplateList(self):
        pass

    def getTemplate(self, index):
        pass
