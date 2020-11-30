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

        default_style = None
        default_size = 24

        if template.has_key('style'):
            if len(filter(lambda m: m.name == template['style'], Glyphs.font.masters)) == 1:
                default_style = template['style']
            else:
                print("[%s]\tthe template specifies a default style (%s), but it's not a style of the current typeface." % (template_name, template['style']))
        else:
            print("[%s]\tthe template does not specify a default style." % template_file)

        if template.has_key('size'):
            if isinstance(template['size'], int):
                default_size = template['size']
            else:
                print("[%s]\tthe proof specifies a default size (%s), but it's not a whole number." % (template_name, template['size']))
        else:
            print("[%s]\tthe template does not specify a default size." % template_file)


        glyphs = []

        if template.has_key("glyphs"):
            if isinstance(template['glyphs'], list):
                glyphs = template['glyphs']

            else:
                print('[%s]\tthe template provides a "glyphs" key, but it\'s not a list of glyph names.' % (template_name))
        else:
            print('[%s]\tthe template does not provide a "glyphs" key.' % (template_name))


        if template.has_key('lines'):
            lines = []
            for linenum, line in enumerate(template['lines']):
                if not line.has_key('style'):
                    if default_style is not None:
                        line['style'] = default_style
                    else:
                        print('[%s]\tline %i has no style specified and no default style is set.' % (template_name, linenum))
                        continue

                if len(filter(lambda m: m.name == line['style'], Glyphs.font.masters)) != 1:
                    if default_style is not None:
                        print('[%s]\tline %i specifies "%s," which is not an instance in this typeface. Replacing with the default "%s."' % (template_name, linenum, line['style'], default_style))
                        line['style'] = default_style
                    else:
                        print('[%s]\tline %i specifies "%s," which is not an instance in this typeface. Since no valid default style is specified, I\'m skipping the line.' % (template_name, linenum, line['style']))
                        continue

                if not line.has_key('size'):
                    print('[%s]\tline %i has no size specified, setting default of %s.' % (template_name, linenum, default_size))
                    line['size'] = default_size

                if not isinstance(line['size'], int):
                    print('[%s]\tline %i does not specify a whole number size, replacing it with the default (%s)...' % (template_name, linenum, default_size))
                    line['size'] = default_size

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

        return {
            "name": name,
            "lines": lines,
            "proof": proof,
            "glyphs": glyphs
        }
