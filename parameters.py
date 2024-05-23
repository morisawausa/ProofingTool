# -*- coding: utf-8 -*-

from timeit import default_timer

import re
import os
import json
from collections import OrderedDict

from GlyphsApp import *
# from AppKit import *
from vanilla import *
from vanilla.dialogs import putFile, getFile
from GlyphsApp.UI import *

from templates import OCCTemplatesView

ELEMENT_PADDING = 5
MAIN_PANEL_HEIGHT_FACTOR = 0.5
LINE_POS = 10
LINE_HEIGHT = 30
HEIGHT_DIVIDER = 40
HEIGHT_BUTTON = 30
HEIGHT_LABEL = 20
WIDTH_LABEL = 30
WIDTH_TEXTBOX = 60
WIDTH_INPUT_NO = 50


def tryParseInt(value, default_value):
	try:
		return int(value)
	except ValueError as e:
		return default_value

class OCCParametersView:

	def __init__(self, width_px, height_px, parent_window,
		parametersChangedCallback=None,
		saveProofCallback=None,
		printProofCallback=None):

		self.window_width = width_px
		self.window_height = height_px
		self.parametersChangedCallback = parametersChangedCallback
		self.saveProofCallback = saveProofCallback
		self.printProofCallback = printProofCallback
		
		self.instances = {}
		for instance in Glyphs.font.instances:
			if instance.type == 0: #check for static instances, 0 is static, 1 is variable
				self.instances[instance.name] = instance

		self.templates = OCCTemplatesView()

		self.interpolated_instances = {}

		self.outputPath = None

		self.glyphs = list(filter(lambda g: g.category == 'Letter' and g.subCategory == 'Uppercase' and g.script == 'latin', Glyphs.font.glyphs))

		self.proof_mode = 'waterfall'
		self.parameters = {
			'padding': {
				'left': 20,
				'right': 50,
				'top': 20,
				'bottom': 50,
				'line': 10,
				'block': 20
			},
			'instances': [],
			'point_sizes': [],
			'aligned': False,
			'document': {'width': 11, 'height': 8.5},
			'title': '',
			'footer': '',
			'mode': 'waterfall',
			'glyphs': [[]]
		}


		self.group = Group((self.window_width, 0, self.window_width, self.window_height))


		#
		# Segmented Button at the top of View:
		# Lets you switch between templates, edit, and glyphs.
		#

		self.group.sections = SegmentedButton(
			(ELEMENT_PADDING, ELEMENT_PADDING, self.window_width - 2 * ELEMENT_PADDING, LINE_HEIGHT),
			[dict(title="File"), dict(title="Edit")],
			callback=self.triggerSetActiveSection)

		windowSize = (ELEMENT_PADDING,
			2*ELEMENT_PADDING + LINE_HEIGHT,
			self.window_width - 2 * ELEMENT_PADDING,
			self.window_height - 2 * ELEMENT_PADDING)

		WIDTH_FULL = windowSize[2]
		WIDTH_HALF = windowSize[2]/2 - ELEMENT_PADDING/2


		#
		# TEMPLATES TAB
		#

		self.group.templates = Group(windowSize)
		self.group.templates.list = List(
			(0, 0, -0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR),
			map(lambda x: self.formatTemplateForDisplayList(x), self.templates.data),
			columnDescriptions=[{"title": "Templates"}],
			selectionCallback=self.triggerLoadSelectedTemplate,
			drawFocusRing=False,
			allowsSorting=False,
			allowsEmptySelection=True,
			allowsMultipleSelection=False,
			rowHeight=20.0
		)

		self.group.templates.openTemplate = Button(
			(0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR, WIDTH_HALF, HEIGHT_BUTTON), "Open Template",
			callback=self.triggerOpenTemplate)

		self.group.templates.loadTemplate = Button(
			(WIDTH_HALF + ELEMENT_PADDING, self.window_height * MAIN_PANEL_HEIGHT_FACTOR, WIDTH_HALF, HEIGHT_BUTTON), "Save Proof as Template",
			callback=self.triggerSaveProofAsTemplate)

		#
		# Output Settings
		#
		LINE_POS = self.window_height * MAIN_PANEL_HEIGHT_FACTOR + HEIGHT_BUTTON + LINE_HEIGHT


		self.group.templates.proofnamelabel = TextBox((0, LINE_POS,  WIDTH_TEXTBOX, HEIGHT_LABEL), "Filename", sizeStyle="small")
		self.group.templates.proofname = EditText((ELEMENT_PADDING + WIDTH_TEXTBOX, LINE_POS, WIDTH_FULL - WIDTH_TEXTBOX - ELEMENT_PADDING, HEIGHT_LABEL), continuous=False, callback=self.triggerParametersListEdit)

		LINE_POS += HEIGHT_DIVIDER

		self.group.templates.saveproofas = SquareButton((0, LINE_POS, WIDTH_HALF, HEIGHT_BUTTON+20), "Save As PDF", callback=self.saveProofAs, sizeStyle="regular")
		self.group.templates.printproof = SquareButton((WIDTH_HALF+ELEMENT_PADDING, LINE_POS, WIDTH_HALF, HEIGHT_BUTTON+20), "Print", callback=self.printProof, sizeStyle="regular")

		self.group.templates.show(False)


		#
		# EDIT TAB
		#

		self.group.edit = Group(windowSize)
		LINE_POS = 0

		#
		# Edit Instances List
		#
		I_instances_LIST = self.instances
		#M_instances_LIST = list(map(lambda m: m.name, Glyphs.font.instances))
		instances_LIST = sorted(I_instances_LIST)

		self.group.edit.list = List(
			(0, LINE_POS, -0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR),
			[{"Style": instances_LIST[0], "Point Size": 72}],
			columnDescriptions=[
				{
					"title": "Style",
					"cell": PopUpButtonListCell(instances_LIST),
					"binding": "selectedValue"
				},
				{
					"title": "Point Size"
				}
			],
			editCallback=self.triggerParametersListEdit,
			drawFocusRing=False,
			allowsSorting=False,
			allowsEmptySelection=True,
			rowHeight=20.0
		)

		LINE_POS += self.window_height * MAIN_PANEL_HEIGHT_FACTOR

		self.group.edit.addRow = Button(
			(0, LINE_POS - HEIGHT_BUTTON, 50, HEIGHT_BUTTON), "+",
			callback=self.triggerAddRowToParametersList)

		self.group.edit.removeRow = Button(
			(50 + ELEMENT_PADDING, LINE_POS - HEIGHT_BUTTON, 50, HEIGHT_BUTTON), "-",
			callback=self.triggerRemoveSelectedFromParametersList)

		LINE_POS += 10

		#
		# Glyph Selection
		#
		# self.group.edit.glyphsLabel = TextBox((ELEMENT_PADDING, LINE_POS, WIDTH_TEXTBOX, HEIGHT_BUTTON), "Glyphs")
		self.group.edit.glyphSelection = SegmentedButton((0, LINE_POS, WIDTH_FULL - ELEMENT_PADDING, HEIGHT_BUTTON), [dict(title="Glyphs from Grid Selection"), dict(title="Glyphs from active Edit View")], callback=self.triggerGlyphSelectionChange, sizeStyle="regular")

		LINE_POS += LINE_HEIGHT + 7

		# self.group.edit.proofModeLabel = TextBox((ELEMENT_PADDING, LINE_POS, WIDTH_TEXTBOX, HEIGHT_BUTTON), "Layout")
		self.group.edit.proofMode = SegmentedButton((0, LINE_POS, WIDTH_FULL - ELEMENT_PADDING, HEIGHT_BUTTON), [dict(title="Waterfall"), dict(title="Paragraphs")], callback=self.triggerProofModeChange, sizeStyle="regular")
		LINE_POS += LINE_HEIGHT + 10

		#
		# Layout Settings
		#
		self.group.edit.layout = Box((0, LINE_POS, -0, 100), u"")

		BOX_POS = 0

		X_POS = ELEMENT_PADDING
		self.group.edit.layout.paddinglabel = TextBox((X_POS, BOX_POS+5, WIDTH_TEXTBOX, HEIGHT_LABEL), "Padding", sizeStyle="small")
		X_POS += WIDTH_TEXTBOX + ELEMENT_PADDING
		self.group.edit.layout.linelabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Line", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.line = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['line'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING
		self.group.edit.layout.blocklabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Block", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.block = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['block'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)
		
		BOX_POS += LINE_HEIGHT

		X_POS = ELEMENT_PADDING
		self.group.edit.layout.marginlabel = TextBox((X_POS, BOX_POS+5, WIDTH_TEXTBOX, HEIGHT_LABEL), "Margins", sizeStyle="small")
		X_POS += WIDTH_TEXTBOX + ELEMENT_PADDING
		self.group.edit.layout.toplabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Top", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.top = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['top'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING

		self.group.edit.layout.leftlabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Left", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.left = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['left'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING

		self.group.edit.layout.rightlabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Right", alignment="left", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.right = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['right'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING

		self.group.edit.layout.botlabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Bot", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.bottom = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['bottom'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)

		BOX_POS += LINE_HEIGHT + 3

		self.group.edit.layout.prooffooterlabel = TextBox((ELEMENT_PADDING, BOX_POS, WIDTH_TEXTBOX, HEIGHT_LABEL), "Footer", sizeStyle="small")
		self.group.edit.layout.prooffooter = EditText(( WIDTH_TEXTBOX + ELEMENT_PADDING, BOX_POS, WIDTH_FULL - WIDTH_TEXTBOX - ELEMENT_PADDING, HEIGHT_LABEL), continuous=False, callback=self.triggerParametersListEdit)

		LINE_POS += LINE_HEIGHT + 90

		self.group.edit.refreshProof = SquareButton(
		(0, LINE_POS, WIDTH_FULL, HEIGHT_BUTTON + 20),
		"Update Proof", callback=self.triggerProofUpdate, sizeStyle="regular" );




		self.group.edit.show(False)


		# #
		# # Globals Tabbed View
		# #

		# self.group.globals = SegmentedButton(
		#     (ELEMENT_PADDING, windowSize[3], self.window_width - 2 * ELEMENT_PADDING, LINE_HEIGHT),
		#     [dict(title="Layout", width=(self.window_width - 2 * ELEMENT_PADDING) / 2), dict(title="Output", width=(self.window_width - 2 * ELEMENT_PADDING) / 2)],
		#     callback=self.triggerSetActiveGlobal)

		# globalsGroupPosSize = (
		#     ELEMENT_PADDING,
		#     windowSize[3] + LINE_HEIGHT + ELEMENT_PADDING,
		#     self.window_width - 2 * ELEMENT_PADDING,
		#     self.window_height * 0.2)


		parent_window.g = self.group

		self.setActiveSection(0)
		# self.setActiveGlobal(0)

		if len(self.group.templates.list) > 0:
			self.group.templates.list.setSelection([0])
			self.loadSelectedTemplate([0])


	def printProof(self, sender):
		if self.printProofCallback is not None:
			self.printProofCallback()

	def saveProof(self, sender):
		if self.outputPath is not None:
			self.saveProofCallback(self.outputPath)

	def saveProofAs(self, sender):
		name = self.group.templates.proofname.get()
		name = name + '.pdf' if name != '' else 'Untitled.pdf'

		result = putFile(
			title="Save Proof",
			messageText="Save Proof As...",
			fileName=name)

		if self.saveProofCallback is not None and result is not None:
			self.outputPath = result
			self.group.templates.saveproof.enable(True)
			self.saveProofCallback(result)


	def triggerParametersListEdit(self, sender):
		# self.tryRerender()
		print( 'updated proof parameters')

	def triggerParametersListSelection(self, sender):
		self.group.edit.removeRow.enable(len(sender.getSelection()) > 0)

	def triggerLoadSelectedTemplate(self, sender):
		self.loadSelectedTemplate(self.group.templates.list.getSelection())

	def triggerProofModeChange(self, sender):
		index = int(sender.get())
		self.proof_mode = 'waterfall' if index == 0 else 'paragraphs'
		# self.tryRerender()

	def triggerProofUpdate( self, sender):
		self.tryRerender()

	def loadSelectedTemplate(self, indices):
		for i in indices:

			# set this first
			template = self.templates.data[i]
			valid_names = list(filter(lambda n: n in Glyphs.font.glyphs, template['glyphs']))
			self.glyphs = list(map(lambda n: Glyphs.font.glyphs[n], valid_names))

			lines = list(map(lambda row: {"Style": row['style'], "Point Size": row['size']}, template['lines']))

			# margins
			self.group.edit.layout.left.set(tryParseInt(template['proof']['margins']['left'], 0))
			self.group.edit.layout.right.set(tryParseInt(template['proof']['margins']['right'], 0))
			self.group.edit.layout.top.set(tryParseInt(template['proof']['margins']['top'], 0))
			self.group.edit.layout.bottom.set(tryParseInt(template['proof']['margins']['bottom'], 0))

			self.group.edit.layout.block.set(tryParseInt(template['proof']['padding']['block'], 0))
			self.group.edit.layout.line.set(tryParseInt(template['proof']['padding']['line'], 0))

			self.proof_mode = template['proof']['mode']
			self.group.edit.proofMode.set(0 if self.proof_mode == 'waterfall' else 1)
			self.group.edit.glyphSelection.set(0 if self.proof_mode == 'waterfall' else 1)

			self.group.edit.list._editCallback = None
			self.group.edit.list.set(lines)
			self.group.edit.list._editCallback = self.triggerParametersListEdit

		self.tryRerender()


	def formatTemplateForDisplayList(self, template):
		return {'Templates': template['name']}


	def triggerSaveProofAsTemplate(self, sender):
		name = self.group.templates.proofname.get()
		print(name)
		print(name != "")
		name = name if name != "" else "Proof"
		print(name)
		filename = '-'.join(name.lower().split(' ')) + '.json'

		print(filename)

		template = OrderedDict()
		template['name'] = name
		template['lines'] = list(map(lambda l: {"style": l["Style"], "size": int(l["Point Size"])}, self.group.edit.list))
		template['proof'] = {
			"margins": {
				"left": int(self.group.edit.layout.left.get()),
				"right": int(self.group.edit.layout.right.get()),
				"top": int(self.group.edit.layout.top.get()),
				"bottom": int(self.group.edit.layout.bottom.get())
			},
			"padding": {
				"block": int(self.group.edit.layout.block.get()),
				"line": int(self.group.edit.layout.line.get())
			},
			"mode": self.proof_mode
		}

		template['glyphs'] = list(map(lambda g: g.name, self.glyphs))

		outfile = putFile(
			title="Save Template",
			messageText="Save Proof As Template...",
			fileName=filename)

		if outfile is not None:
			with open(outfile, 'w') as file:
				json.dump(template, file, indent=4)



	def triggerOpenTemplate(self, sender):

		template_files = GetFile("Choose a Proof Template file (ending in '.json')", True, ["json"])
		modified_indices = []
		if template_files is not None and len(template_files) > 0:
			for filepath in template_files:
				with open(filepath, 'r') as template_file:
					name = filepath.split(os.path.sep)[-1]
					template = self.templates.parseTemplateFile(name, template_file)
					if template is not None:
						display = self.formatTemplateForDisplayList(template);
						try:
							i = self.group.templates.list.index(display)
							self.templates.data[i] = template
							self.group.templates.list[i] = display
							modified_indices.append(i)
						except ValueError:
							self.templates.data.append(template)
							self.group.templates.list.append(display)
							modified_indices.append(len(self.group.templates.list) - 1)

			if len(modified_indices) > 0:
				self.loadSelectedTemplate([modified_indices[-1]])
				self.group.templates.list.setSelection([modified_indices[-1]])



	def triggerSetActiveSection(self, sender):
		self.setActiveSection(int(sender.get()))

	# def triggerSetActiveGlobal(self, sender):
	#     self.setActiveGlobal(int(sender.get()))

	def triggerAddRowToParametersList(self, sender):
		if len(self.group.edit.list) > 0:
			last_style = self.group.edit.list[-1]['Style']
			last_ptsz = self.group.edit.list[-1]['Point Size']
			self.group.edit.list.append({"Style": last_style, "Point Size": last_ptsz})

		else:
			self.group.edit.list.append({
				"Style": self.instances[0],
				"Point Size": 24})

	def triggerRemoveSelectedFromParametersList(self, sender):
		for index in reversed(self.group.edit.list.getSelection()):
			del self.group.edit.list[index]

	def triggerGlyphSelectionChange( self, sender):
		index = int(sender.get())
		if index == 0:
			self.glyphs = list(filter(lambda g: g.selected, Glyphs.font.glyphs))
		else:
			if Glyphs.font.currentTab is not None:
				self.glyphs = list(map(lambda l: l.parent, Glyphs.font.currentTab.layers))

	def parametersChanged(self, parameters, glyphs):
		glyphsChanged = glyphs[0] != self.parameters['glyphs'][0]

		layoutChanged = parameters['padding'] != self.parameters['padding']
		instancesChanged = parameters['instances'] != self.parameters['instances']
		sizesChanged = parameters['point_sizes'] != self.parameters['point_sizes']
		titleChanged = parameters['title'] != self.parameters['title']
		footerChanged = parameters['footer'] != self.parameters['footer']
		modeChanged = parameters['mode'] != self.parameters['mode']

		paramsChanged = layoutChanged or instancesChanged or sizesChanged or modeChanged
		metadataChanged = titleChanged or footerChanged

		return glyphsChanged or paramsChanged or metadataChanged


	def tryRerender(self):
		if self.parametersChangedCallback is not None:

			newParamSet = self.getParameterSet()
			newGlyphSet = self.getGlyphSet()

			# check to see if the parameters actually changed.
			if self.parametersChanged(newParamSet, newGlyphSet):

				# cache latest parameter state.
				self.parameters = newParamSet
				self.parameters['glyphs'] = newGlyphSet

				self.parametersChangedCallback(newParamSet, newGlyphSet)



	def setActiveSection(self, index):
		if index != 0 and index != 1 and index != 2: return
		self.group.sections.set(index)
		self.group.templates.show(index == 0)
		self.group.edit.show(index == 1)


	def getGlyphSet(self):
		return [self.glyphs]


	def getParameterSet(self):

		instances = []
		point_sizes = []

		pre_interpolation = default_timer()

		for i, item in enumerate(self.group.edit.list):
			size_dirty = item['Point Size']
			size_clean = re.sub('[^0-9]', '', str(size_dirty))
			size = tryParseInt(size_clean, 72)

			styles = []

			if len(self.instances) > 0:
				# styles = filter(lambda i: i.instances[0].name == item['Style'], self.instances) # NOTE: Changed from .instances to .instances
				if item['Style'] in self.instances.keys():
					style_name = item['Style']
					instances.append( style_name )
					if style_name not in self.interpolated_instances:
						# we haven't interpolated this instance yet.
						# interpolate the instance and store it in our shared instance cache for future use.
						instance = self.instances[style_name]
						# NOTE(nic): trying out `interpolatedFontProxy` here instead of `interpolatedFont`.
						# accoding to [the docs](https://docu.glyphsapp.com/#GSInstance.interpolatedFontProxy),
						# iterpolatedFontProxy interpolates glyphs on demand, rather than interpolating the entire instance.
						# This means we do work proportional to the glyphs in the proof, rather than in the font.
						self.interpolated_instances[style_name] = instance.interpolatedFontProxy            
				point_sizes.append(size)

			else:
				print("[unknown style] couldn’t find a unique style matching '%s'; skipping." % item['Style'] )

		print( self.interpolated_instances )       
		print('[profile] time to interpolate: %.03f seconds' % (default_timer() - pre_interpolation))

		parameters = {
			'padding': {
				'left': tryParseInt(self.group.edit.layout.left.get(), self.parameters['padding']['left']),
				'right': tryParseInt(self.group.edit.layout.right.get(), self.parameters['padding']['right']),
				'top': tryParseInt(self.group.edit.layout.top.get(), self.parameters['padding']['top']),
				'bottom': tryParseInt(self.group.edit.layout.bottom.get(), self.parameters['padding']['bottom']),
				'line': tryParseInt(self.group.edit.layout.line.get(), self.parameters['padding']['line']),
				'block': tryParseInt(self.group.edit.layout.block.get(), self.parameters['padding']['block'])
			},
			'instances': instances,
			'exports': self.interpolated_instances,
			'point_sizes': list(map(int, point_sizes)),
			'aligned': True,
			'document': {'width': 11, 'height': 8.5},
			'title': self.group.templates.proofname.get(),
			'footer': self.group.edit.layout.prooffooter.get(),
			'mode': self.proof_mode
		}
		#print('PARAMS', parameters)
		return parameters
