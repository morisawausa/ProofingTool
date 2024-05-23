import os
import json
from GlyphsApp import *

from preferences import OCCTemplatePreferences

class OCCTemplatesView( ):

	def __init__(self):
		prefs = OCCTemplatePreferences()
		self.data = self.parseTemplateDirectory('data')
		self.instanceList = self.getInstanceList()
		# directory = prefs.getDirectoryPath()
		# self.data = self.parseTemplateDirectory(directory)

	def getInstanceList(self):
		instances = {}
		for instance in Glyphs.font.instances:
			if instance.type == 0: #check for static instances, 0 is static, 1 is variable
				name = instance.name
				if instance.preferredFamilyName:
					name = instance.preferredFamilyName
					if instance.preferredSubfamilyName:
						name += " " + instance.preferredSubfamilyName
					else:
						name += " " + instance.name
				instances[name] = instance
		return instances

	def parseTemplateDirectory(self, directory):
		if not os.path.isdir(directory): return []

		templates_files = list(filter(lambda f: '.json' in f, os.listdir(directory)))
		templates = []

		for i, template_name in enumerate(templates_files):
			with open(os.path.join(directory, template_name), 'r') as template_file:
				template = self.parseTemplateFile(template_name, template_file)
				if template is not None:
					templates.append(template)

		return templates


	def parseTemplateFile(self, name, file):
		try:
			print('[%s]\tloading template...' % (name))
			template = json.load(file)
			result = self.validateAndFormatTemplate(name, template)
			print('[%s]\tdone.\n' % (name))
			return result

		except Exception as error:
			print('[%s]\terror parsing this template\'s json:' % name)
			print('[%s]\t%s' % (name, str(error)))

			return None


	def validateAndFormatTemplate(self, template_name, template):
		instances = self.getInstanceList()
		instance_names = instances.keys()

		if 'name' in template:
			name = template['name']
		else:
			print('[%s]\t"%s" does not have a template name specified. Naming it "%s"' % (template_name, template_name, template_name))
			name = template_name

		default_style = None
		default_size = 24

		if 'style' in template:
			# if len(list(filter(lambda i: i.name == template['style'], Glyphs.font.instance_names))) == 1:
			if template['style'] in instance_names:
				default_style = template['style']
			else:
				print("[%s]\tthe template specifies a default style (%s), but it’s not a style of the current typeface." % (template_name, template['style']))
		else:
			print("[%s]\t the template does not specify a default style." % template_name)

		if 'size' in template:
			if isinstance(template['size'], int):
				default_size = template['size']
			else:
				print("[%s]\tthe proof specifies a default size (%s), but it’s not a whole number." % (template_name, template['size']))
		else:
			print("[%s]\tthe template does not specify a default size." % template_name)


		glyphs = []

		if 'glyphs' in template:
			if isinstance(template['glyphs'], list):
				glyphs = template['glyphs']

			else:
				print('[%s]\tthe template provides a "glyphs" key, but it\'s not a list of glyph names.' % (template_name))
		else:
			print('[%s]\tthe template does not provide a "glyphs" key.' % (template_name))


		if 'lines' in template:
			lines = []
			for linenum, line in enumerate(template['lines']):
				if not ('style' in line):
					if default_style is not None:
						line['style'] = default_style
					else:
						print('[%s]\tline %i has no style specified and no default style is set.' % (template_name, linenum + 1))
						continue

				if len(list(filter(lambda i: i == line['style'], instances))) != 1:
					if default_style is not None:
						print(u'[%s]\t⚠️ line %i specifies "%s," which is not an instance in this typeface. Replacing with the default "%s."' % (template_name, linenum + 1, line['style'], default_style))
						line['style'] = default_style
					else:
						print(u'[%s]\t⚠️ line %i specifies "%s," which is not an instance in this typeface. Since no valid default style is specified, we’re skipping the line.' % (template_name, linenum + 1, line['style']))
						continue

				if not ('size' in line):
					print('[%s]\tline %i has no size specified, setting default of %s.' % (template_name, linenum + 1, default_size))
					line['size'] = default_size

				if not isinstance(line['size'], int):
					print('[%s]\tline %i does not specify a whole number size, replacing it with the default (%s)...' % (template_name, linenum + 1, default_size))
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
			},
			"mode": "waterfall"
		}

		if 'proof' in template:
			if 'margins' in template['proof']:
				proof['margins']['left'] = template['proof']['margins']['left'] if 'left' in template['proof']['margins'] else 20
				proof['margins']['right'] = template['proof']['margins']['right'] if 'right' in template['proof']['margins'] else 70
				proof['margins']['top'] = template['proof']['margins']['top'] if 'top' in template['proof']['margins'] else 20
				proof['margins']['bottom'] = template['proof']['margins']['bottom'] if 'bottom' in template['proof']['margins']else 100

			if 'padding' in template['proof']:
				proof['padding']['line'] = template['proof']['padding']['line'] if 'line' in template['proof']['padding'] else 20
				proof['padding']['block'] = template['proof']['padding']['block'] if 'block' in template['proof']['padding'] else 20

			if 'mode' in template['proof']:
				proof['mode'] = template['proof']['mode']

		else:
			print('[%s]\t"%s" does not specify margin and padding information. Setting defaults. "' % (template_name, template_name))

		return {
			"name": name,
			"lines": lines,
			"proof": proof,
			"glyphs": glyphs
		}
