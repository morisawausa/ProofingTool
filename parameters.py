# -*- coding: utf-8 -*-

from timeit import default_timer

import re
import os
import json
from collections import OrderedDict

from GlyphsApp import *
from vanilla import *
from vanilla.dialogs import putFile, getFile
from GlyphsApp.UI import *

from templates import OCCTemplatesView
from preferences import OCCTemplatePreferences

ELEMENT_PADDING = 8
TEMPLATES_PANEL_HEIGHT_FACTOR = 0.65
EDIT_PANEL_HEIGHT_FACTOR = 0.35
LINE_POS = 10
LINE_HEIGHT = 30
HEIGHT_DIVIDER = 30
HEIGHT_BUTTON = 30
HEIGHT_LABEL = 20
WIDTH_LABEL = 40
WIDTH_TEXTBOX = 65
WIDTH_INPUT_NO = 35


def tryParseInt(value, default_value):
	try:
		return int(value)
	except ValueError as e:
		return default_value

def tryString(value, default_value):
	try:
		return value
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
		
		self.preferences = OCCTemplatePreferences()
		self.templateFiles = []
		self.templateFiles.extend( self.preferences.templatePaths )

		self.templates = OCCTemplatesView()

		self.instances = self.templates.instanceList

		self.interpolated_instances = {}

		self.outputPath = None

		self.glyphs = list(filter(lambda g: g.category == 'Letter' and g.subCategory == 'Uppercase' and g.script == 'latin', Glyphs.font.glyphs))
		self.templateGlyphs = []

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
			'exports': [],
			'point_sizes': [],
			'aligned': False,
			'document': {'width': 11, 'height': 8.5},
			'title': '',
			'footer': '',
			'mode': 'waterfall',
			'reinterpolate': False,
			'glyphs': [[]]
		}


		self.group = Group((self.window_width, 0, self.window_width, self.window_height))


		#
		# Segmented Button at the top of View:
		# Lets you switch between Template List and Template Editing Mode
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
		WIDTH_THIRD = windowSize[2]/3 - ELEMENT_PADDING/3


		#
		# TEMPLATES TAB
		#

		self.group.templates = Group(windowSize)
		self.group.templates.list = List(
			(0, 0, -0, self.window_height * TEMPLATES_PANEL_HEIGHT_FACTOR),
			map(lambda x: self.formatTemplateForDisplayList(x), self.templates.data),
			columnDescriptions=[{"title": "Templates"}],
			selectionCallback=self.triggerLoadSelectedTemplate,
			editCallback=self.triggerTemplateListEdit,
			drawFocusRing=False,
			allowsSorting=False,
			allowsEmptySelection=True,
			allowsMultipleSelection=True,
			rowHeight=20.0
		)


		LINE_POS = self.window_height * TEMPLATES_PANEL_HEIGHT_FACTOR

		self.group.templates.addTemplate = Button(
			(-100-ELEMENT_PADDING, LINE_POS - HEIGHT_BUTTON, 50, HEIGHT_BUTTON), "+",
			callback=self.triggerOpenTemplate)
		self.group.templates.addTemplate.setToolTip("Load new template(s) to list")

		self.group.templates.removeTemplate = Button(
			(-50-ELEMENT_PADDING, LINE_POS - HEIGHT_BUTTON, 50, HEIGHT_BUTTON), "-",
			callback=self.triggerRemoveTemplate)
		self.group.templates.removeTemplate.setToolTip("Remove selected template(s) from the list")

		LINE_POS += 10

		# self.group.templates.applyTemplate = Button(
		# (0, LINE_POS, WIDTH_FULL, HEIGHT_BUTTON),
		# "Apply Selected Template", callback=self.triggerApplyTemplate, sizeStyle="regular" )
		# self.group.templates.applyTemplate.setToolTip("Note: any edits to the proof will be reverted back to the saved template.")
		# self.group.templates.applyTemplate.enable( False )

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
		instances_LIST = [x for x in I_instances_LIST]

		self.group.edit.list = List(
			(0, LINE_POS, -0, self.window_height * EDIT_PANEL_HEIGHT_FACTOR),
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
			editCallback=self.triggerInstanceListEdit,
			drawFocusRing=False,
			allowsSorting=False,
			allowsEmptySelection=True,
			rowHeight=20.0
		)
		self.group.edit.list.setToolTip("Use the +/- buttons to add styles to the list, or edit the .json template file in a Text Editor and reload.")

		LINE_POS += self.window_height * EDIT_PANEL_HEIGHT_FACTOR

		self.group.edit.addRow = Button(
			(-100-ELEMENT_PADDING, LINE_POS - HEIGHT_BUTTON, 50, HEIGHT_BUTTON), "+",
			callback=self.triggerAddRowToParametersList)

		self.group.edit.removeRow = Button(
			(-50-ELEMENT_PADDING, LINE_POS - HEIGHT_BUTTON, 50, HEIGHT_BUTTON), "-",
			callback=self.triggerRemoveSelectedFromParametersList)

		LINE_POS += 10

		#
		# Glyph Selection
		#
		self.group.edit.glyphSelection = SegmentedButton((0, LINE_POS, WIDTH_FULL - ELEMENT_PADDING, HEIGHT_BUTTON), [dict(title="Template Glyphs"), dict(title="Grid Selection"), dict(title="Edit View")], sizeStyle="regular")
		self.group.edit.glyphSelection.setToolTip("Choose which glyphs to use.")

		LINE_POS += LINE_HEIGHT + 7

		#
		# Proof Settings
		#
		self.group.edit.proofMode = SegmentedButton((0, LINE_POS, WIDTH_FULL - ELEMENT_PADDING, HEIGHT_BUTTON), [dict(title="Waterfall"), dict(title="Paragraphs")], callback=self.triggerProofModeChange, sizeStyle="regular")
		self.group.edit.proofMode.setToolTip("Choose the layout mode: waterfall mode stacks styles line by line, while paragraph mode will output the glyphs together in a paragraph per style.")

		LINE_POS += LINE_HEIGHT + 10

		#
		# Layout Settings
		#
		self.group.edit.layout = Box((0, LINE_POS, -0, 100), u"")

		BOX_POS = 0

		X_POS = ELEMENT_PADDING
		self.group.edit.layout.paddinglabel = TextBox((X_POS, BOX_POS+5, WIDTH_TEXTBOX, HEIGHT_LABEL), "Padding", sizeStyle="small")
		X_POS += WIDTH_TEXTBOX + ELEMENT_PADDING
		self.group.edit.layout.linelabel = TextBox((X_POS, BOX_POS+5, 115, HEIGHT_LABEL), "Line Gap", sizeStyle="mini")
		X_POS += 115 + ELEMENT_PADDING
		self.group.edit.layout.line = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['line'], sizeStyle="small", continuous=False, callback=self.triggerParametersEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING
		self.group.edit.layout.blocklabel = TextBox((X_POS, BOX_POS+5, 115, HEIGHT_LABEL), "Paragraph Gap", sizeStyle="mini")
		X_POS += 115 + ELEMENT_PADDING
		self.group.edit.layout.block = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['block'], sizeStyle="small", continuous=False, callback=self.triggerParametersEdit)
		
		BOX_POS += LINE_HEIGHT

		X_POS = ELEMENT_PADDING
		self.group.edit.layout.marginlabel = TextBox((X_POS, BOX_POS+5, WIDTH_TEXTBOX, HEIGHT_LABEL), "Margins", sizeStyle="small")
		X_POS += WIDTH_TEXTBOX + ELEMENT_PADDING
		self.group.edit.layout.toplabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Top", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.top = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['top'], sizeStyle="small", continuous=False, callback=self.triggerParametersEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING

		self.group.edit.layout.leftlabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Left", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.left = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['left'], sizeStyle="small", continuous=False, callback=self.triggerParametersEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING

		self.group.edit.layout.rightlabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Right", alignment="left", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.right = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['right'], sizeStyle="small", continuous=False, callback=self.triggerParametersEdit)
		X_POS += WIDTH_INPUT_NO + ELEMENT_PADDING

		self.group.edit.layout.botlabel = TextBox((X_POS, BOX_POS+5, WIDTH_LABEL, HEIGHT_LABEL), "Bottom", sizeStyle="mini")
		X_POS += WIDTH_LABEL
		self.group.edit.layout.bottom = EditText((X_POS, BOX_POS, WIDTH_INPUT_NO, HEIGHT_LABEL), self.parameters['padding']['bottom'], sizeStyle="small", continuous=False, callback=self.triggerParametersEdit)

		BOX_POS += LINE_HEIGHT + 3

		self.group.edit.layout.prooffooterlabel = TextBox((ELEMENT_PADDING, BOX_POS, WIDTH_TEXTBOX, HEIGHT_LABEL), "Footer", sizeStyle="small")
		self.group.edit.layout.prooffooter = EditText(( WIDTH_TEXTBOX + ELEMENT_PADDING, BOX_POS, -ELEMENT_PADDING, HEIGHT_LABEL+5), self.parameters['footer'], continuous=False, callback=self.triggerParametersEdit)

		LINE_POS += 100
		self.group.edit.show(False)

		LINE_POS += HEIGHT_DIVIDER


		#
		# GLOBAL BUTTONS AND OUTPUT
		#
		self.group.output = Group( (ELEMENT_PADDING, -160, windowSize[2], 150) )
		LINE_POS = 0
		
		self.group.output.refreshInstances =  CheckBox(
			(ELEMENT_PADDING, LINE_POS, -ELEMENT_PADDING, HEIGHT_LABEL), "Re-export Instances", value=False)
		self.group.output.refreshInstances.setToolTip("Uncheck this to adjust the proof with existing styles. Keep checked for any changes in the list of styles.")

		LINE_POS += LINE_HEIGHT

		self.group.output.refreshProof = SquareButton(
		(0, LINE_POS, -0, HEIGHT_BUTTON+10),
		"❇️ Proof", callback=self.triggerProofUpdate, sizeStyle="regular" );
		self.group.output.refreshProof.setToolTip("Update the proof with applied template or edited settings. ")

		#
		# Output Settings
		#
		LINE_POS += HEIGHT_DIVIDER+20

		self.group.output.proofnamelabel = TextBox((0, LINE_POS,  WIDTH_TEXTBOX+20, HEIGHT_LABEL), "Proof Name", sizeStyle="regular")
		self.group.output.proofname = EditText((ELEMENT_PADDING + WIDTH_TEXTBOX+20, LINE_POS, -0, HEIGHT_LABEL+5), self.parameters['title'], continuous=False, callback=self.triggerParametersEdit)

		LINE_POS += LINE_HEIGHT

		self.group.output.saveTemplate = Button((0, LINE_POS, WIDTH_THIRD, HEIGHT_BUTTON), "📋 Save As Template", callback=self.triggerSaveProofAsTemplate)
		self.group.output.saveproofas = Button((WIDTH_THIRD+ELEMENT_PADDING/2, LINE_POS, WIDTH_THIRD, HEIGHT_BUTTON), "📄 Save PDF", callback=self.saveProofAs, sizeStyle="regular")
		self.group.output.printproof = Button((WIDTH_THIRD*2+ELEMENT_PADDING, LINE_POS, WIDTH_THIRD, HEIGHT_BUTTON), "🖨 Print Proof", callback=self.printProof, sizeStyle="regular")


		parent_window.g = self.group
		self.setActiveSection(0)

		if len(self.group.templates.list) > 0:
			self.group.templates.list.setSelection([0])
			self.loadSelectedTemplate(0)

	def printProof(self, sender):
		if self.printProofCallback is not None:
			self.printProofCallback()

	def saveProofAs(self, sender):
		name = self.group.output.proofname.get()
		name = name + '.pdf' if name != '' else 'UntitledProof.pdf'
		result = putFile(
			title="Save Proof",
			messageText="Save Proof As...",
			fileName=name)
		if self.saveProofCallback is not None and result is not None:
			self.outputPath = result
			self.saveProofCallback(result)

	def triggerParametersEdit(self, sender):
		self.parameters = self.getParameterSet()

	def triggerInstanceListEdit(self, sender):
		self.group.output.refreshInstances.set(1)

	def triggerTemplateListEdit(self, sender):
		self.preferences.savePreferences(self.templateFiles)

	def triggerLoadSelectedTemplate(self, sender):
		selectionIndices = self.group.templates.list.getSelection()
		if len(selectionIndices) > 0:
			selectedIndex = selectionIndices[-1]
			self.loadSelectedTemplate(selectedIndex)

	def triggerProofModeChange(self, sender):
		index = int(sender.get())
		self.proof_mode = 'waterfall' if index == 0 else 'paragraphs'

	# def triggerApplyTemplate(self, sender):
	# 	self.group.output.refreshInstances.set(1)
	# 	self.tryRerender()

	def triggerProofUpdate( self, sender ):
		self.tryRerender()

	def loadSelectedTemplate(self, selectedIndex):
		template = self.templates.data[selectedIndex]
		self.glyphs = list()
		for n in template["glyphs"]:
			if n == "newGlyph": #linebreak 
				newGlyph = GSControlLayer(10)
				newGlyph.name = 'newGlyph'
				self.glyphs.append( newGlyph )
			else:
				self.glyphs.append( Glyphs.font.glyphs[n] )

		self.templateGlyphs = self.glyphs.copy() #store for refrence
		lines = list(map(lambda row: {"Style": row['style'], "Point Size": row['size']}, template['lines']))

		# settings
		self.group.output.proofname.set(tryString(template['name'], ''))
		# margins
		self.group.edit.layout.left.set(tryParseInt(template['proof']['margins']['left'], 0))
		self.group.edit.layout.right.set(tryParseInt(template['proof']['margins']['right'], 0))
		self.group.edit.layout.top.set(tryParseInt(template['proof']['margins']['top'], 0))
		self.group.edit.layout.bottom.set(tryParseInt(template['proof']['margins']['bottom'], 0))

		self.group.edit.layout.block.set(tryParseInt(template['proof']['padding']['block'], 0))
		self.group.edit.layout.line.set(tryParseInt(template['proof']['padding']['line'], 0))

		self.proof_mode = template['proof']['mode']
		self.group.edit.proofMode.set(0 if self.proof_mode == 'waterfall' else 1)
		self.group.edit.glyphSelection.set(0)

		self.group.edit.layout.prooffooter.set(tryString(template['proof']['footer'], ''))

		self.group.edit.list._editCallback = None
		self.group.edit.list.set(lines)


	def formatTemplateForDisplayList(self, template):
		return {'Templates': template['name']}


	def triggerSaveProofAsTemplate(self, sender):
		name = self.group.output.proofname.get()
		name = name if name != "" else "Proof"
		filename = '-'.join(name.lower().split(' ')) + '.json'
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
			"mode": self.proof_mode,
			"footer": self.group.edit.layout.prooffooter.get()
		}

		template['glyphs'] = list(map(lambda g: g.name, self.glyphs))

		outfile = putFile(
			title="Save Template",
			messageText="Save Proof As Template...",
			fileName=filename)
		
		if outfile is not None:
			with open(outfile, 'w') as file:
				json.dump(template, file, indent=4)

			self.processTemplateFiles([outfile])


	def triggerOpenTemplate(self, sender):
		template_files = GetFile("Choose a Proof Template file (ending in '.json')", True, ["json"])
		# self.preferences.setDirectoryPath( template_files )
		self.processTemplateFiles( template_files )

	def triggerRemoveTemplate(self, sender):
		for index in reversed(self.group.templates.list.getSelection()):
			del self.group.templates.list[index]
			filepathRemove = self.templateFiles[index]
			self.templateFiles.remove(filepathRemove)
			self.preferences.savePreferences(self.templateFiles)

	def processTemplateFiles(self, template_files ):
		modified_indices = []
		if template_files is not None and len(template_files) > 0:
			for filepath in template_files:
				with open(filepath, 'r') as template_file:
					name = filepath.split(os.path.sep)[-1]
					template = self.templates.parseTemplateFile(name, template_file)
					if template is not None:
						display = self.formatTemplateForDisplayList(template);
						
						self.templateFiles.append(filepath)

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
				self.loadSelectedTemplate(modified_indices[-1])
				self.group.templates.list.setSelection([modified_indices[-1]])

 
	def triggerSetActiveSection(self, sender):
		self.setActiveSection(int(sender.get()))

	def triggerAddRowToParametersList(self, sender):
		self.group.output.refreshInstances.set(1)
		if len(self.group.edit.list) > 0:
			last_style = self.group.edit.list[-1]['Style']
			last_ptsz = self.group.edit.list[-1]['Point Size']
			self.group.edit.list.append({"Style": last_style, "Point Size": last_ptsz})
		else:
			self.group.edit.list.append({
				"Style": next(iter(self.instances)),
				"Point Size": 24})

	def triggerRemoveSelectedFromParametersList(self, sender):
		self.group.output.refreshInstances.set(1)
		for index in reversed(self.group.edit.list.getSelection()):
			del self.group.edit.list[index]

	def parametersChanged(self, parameters, glyphs):
		glyphsChanged = parameters['glyphs'][0] != self.parameters['glyphs'][0]
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
				print(f"Generating Proof [{self.parameters['title']}]...")

				self.parametersChangedCallback(newParamSet, newGlyphSet)


	def setActiveSection(self, index):
		if index != 0 and index != 1 and index != 2: return
		self.group.sections.set(index)
		self.group.templates.show(index == 0)
		self.group.edit.show(index == 1)


	def getGlyphSet(self):
		index = int(self.group.edit.glyphSelection.get())
		if index == 1:
			self.glyphs = list(filter(lambda g: g.selected, Glyphs.font.glyphs))
		elif index == 2:
			if Glyphs.font.currentTab is not None:
				self.glyphs = list(map(lambda l: l.parent, Glyphs.font.currentTab.layers))
		else:
			self.glyphs = self.templateGlyphs
		return [self.glyphs]

	def getParameterSet(self):
		if( self.group.output.refreshInstances.get() == 1 ):
			instances = []
		else:
			instances = self.parameters['instances']
		point_sizes = []

		pre_interpolation = default_timer()

		for i, item in enumerate(self.group.edit.list):
			size_dirty = item['Point Size']
			size_clean = re.sub('[^0-9]', '', str(size_dirty))
			size = tryParseInt(size_clean, 72)

			styles = []

			if len(self.instances) > 0:
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
				print(f"[unknown style] couldn’t find a unique style matching '{item['Style']}'; skipping.")

		# print('[profile] time to interpolate: %.03f seconds' % (default_timer() - pre_interpolation))

		parameters = {
			'padding': {
				'left': tryParseInt(self.group.edit.layout.left.get(), self.parameters['padding']['left']),
				'right': tryParseInt(self.group.edit.layout.right.get(), self.parameters['padding']['right']),
				'top': tryParseInt(self.group.edit.layout.top.get(), self.parameters['padding']['top']),
				'bottom': tryParseInt(self.group.edit.layout.bottom.get(), self.parameters['padding']['bottom']),
				'line': tryParseInt(self.group.edit.layout.line.get(), self.parameters['padding']['line']),
				'block': tryParseInt(self.group.edit.layout.block.get(), self.parameters['padding']['block'])
			},
			'glyphs': self.glyphs,
			'instances': instances,
			'exports': self.interpolated_instances,
			'point_sizes': list(map(int, point_sizes)),
			'aligned': True,
			'document': {'width': 11, 'height': 8.5},
			'title': tryString(self.group.output.proofname.get(), self.parameters['title']),
			'footer': tryString(self.group.edit.layout.prooffooter.get(), self.parameters['footer']),
			'mode': self.proof_mode,
			'reinterpolate': self.group.output.refreshInstances.get()
		}
		#print('PARAMS', parameters)
		return parameters
