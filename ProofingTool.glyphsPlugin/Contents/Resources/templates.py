import os
import json
from GlyphsApp import *


DEBUG = False

class OCCTemplatesView:

	def __init__(self, preferences):
		self.templateFiles = preferences.templatePaths
		self.data = self.parseTemplatePaths(self.templateFiles)
		self.instanceList = self.getInstanceList()

	def getInstanceList(self):
		instances = {}
		for instance in Glyphs.font.instances:
			if instance.type == 0:  # check for static instances, 0 is static, 1 is variable
				name = instance.name
				if instance.preferredFamilyName:
					name = instance.preferredFamilyName
					if instance.preferredSubfamilyName:
						name += " " + instance.preferredSubfamilyName
					else:
						name += " " + instance.name
				instances[name] = instance
		return instances

	def parseTemplatePaths(self, files):
		templates = []
		for i, template_path in enumerate(files):
			if not os.path.isfile(template_path):
				print(f"⚠️ [Missing Template] {template_path}\tnot found")
				continue
			try:
				with open(template_path, 'r') as template_file:
					template = self.parseTemplateFile(template_path, template_file)
					if template is not None:
						templates.append(template)
			except Exception as e:
				print(f"An error occurred while processing the file {template_path}: {e}")
		return templates

	def parseTemplateFile(self, name, file):
		try:
			if DEBUG:
				print(f'[{name}]\tloading template...')
			template = json.load(file)
			result = self.validateAndFormatTemplate(name, template)
			if DEBUG:
				print(f'[{name}]\tdone loading.\n')
			return result

		except Exception as error:
			if DEBUG:
				print(f'[{name}]\terror parsing this template\'s json:')
				print(f'[{name}]\t{error}')

			return None

	def validateAndFormatTemplate(self, template_name, template):
		instances = self.getInstanceList()
		instance_names = instances.keys()

		if 'name' in template:
			name = template['name']
		else:
			if DEBUG:
				print(f'[{template_name}]\t"{template_name}" does not have a template name specified. Naming it "{template_name}"')
			name = template_name

		default_style = None
		default_size = 24

		if 'style' in template:
			if template['style'] in instance_names:
				default_style = template['style']
			else:
				if DEBUG:
					print(f'[{template_name}]\tthe template specifies a default style ({template["style"]}), but it’s not a style of the current typeface.')
		else:
			if DEBUG:
				print(f'[{template_name}]\tthe template does not specify a default style.')

		if 'size' in template:
			if isinstance(template['size'], int):
				default_size = template['size']
			else:
				if DEBUG:
					print(f'[{template_name}]\tthe proof specifies a default size ({template["size"]}), but it’s not a whole number.')
		else:
			if DEBUG:
				print(f'[{template_name}]\tthe template does not specify a default size.')

		glyphs = []

		if 'glyphs' in template:
			if isinstance(template['glyphs'], list):
				glyphs = template['glyphs']
			else:
				if DEBUG:
					print(f'[{template_name}]\tthe template provides a "glyphs" key, but it’s not a list of glyph names.')
		else:
			if DEBUG:
				print(f'[{template_name}]\tthe template does not provide a "glyphs" key.')

		if 'lines' in template:
			lines = []
			for linenum, line in enumerate(template['lines']):
				if 'style' not in line:
					if default_style is not None:
						line['style'] = default_style
					else:
						if DEBUG:
							print(f'[{template_name}]\tline {linenum + 1} has no style specified and no default style is set.')
						continue

				if len(list(filter(lambda i: i == line['style'], instances))) != 1:
					if default_style is not None:
						if DEBUG:
							print(f'[{template_name}]\t⚠️ line {linenum + 1} specifies "{line["style"]}," which is not an instance in this typeface. Replacing with the default "{default_style}".')
						line['style'] = default_style
					else:
						if DEBUG:
							print(f'[{template_name}]\t⚠️ line {linenum + 1} specifies "{line["style"]}," which is not an instance in this typeface. Since no valid default style is specified, we’re skipping the line.')
						continue

				if 'size' not in line:
					if DEBUG:
						print(f'[{template_name}]\tline {linenum + 1} has no size specified, setting default of {default_size}.')
					line['size'] = default_size

				if not isinstance(line['size'], int):
					if DEBUG:
						print(f'[{template_name}]\tline {linenum + 1} does not specify a whole number size, replacing it with the default ({default_size})...')
					line['size'] = default_size

				lines.append(line)
		else:
			if DEBUG:
				print(f'[{template_name}]\t"{template_name}" does not have any lines specified.')
			lines = []

		proof = {
			"margins": {
				"left": 20,
				"right": 70,
				"top": 20,
				"bottom": 100,
			},
			"gaps": {
				"line": 20,
				"block": 20
			},
			"mode": "waterfall",
			"footer" : ""
		}

		if 'proof' in template:
			if 'margins' in template['proof']:
				proof['margins']['left'] = template['proof']['margins']['left']
				proof['margins']['right'] = template['proof']['margins']['right']
				proof['margins']['top'] = template['proof']['margins']['top']
				proof['margins']['bottom'] = template['proof']['margins']['bottom']

			if 'gaps' in template['proof']:
				proof['gaps']['line'] = template['proof']['gaps']['line']
				proof['gaps']['block'] = template['proof']['gaps']['block']

			if 'mode' in template['proof']:
				proof['mode'] = template['proof']['mode']

			if 'footer' in template['proof']:
				proof['footer'] = template['proof']['footer']
		else:
			if DEBUG:
				print(f'[{template_name}]\t"{template_name}" does not specify margin and gap information. Setting defaults.')

		return {
			"name": name,
			"lines": lines,
			"proof": proof,
			"glyphs": glyphs
		}
