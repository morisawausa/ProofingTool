# -*- coding: utf-8 -*-

from timeit import default_timer

import re
import os
import json
from collections import OrderedDict

from GlyphsApp import *
from AppKit import *
from vanilla import *
from vanilla.dialogs import putFile, getFile
from GlyphsApp.UI import *

from templates import OCCTemplatesView

ELEMENT_PADDING = 5
SECTION_SELECTOR_HEIGHT = 20
MAIN_PANEL_HEIGHT_FACTOR = 0.6

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
        self.templates = OCCTemplatesView()
        self.instance_masters = map(lambda i: i.name, Glyphs.font.instances)
        self.interpolated_instances = {}

        self.outputPath = None

        self.glyphs = filter(lambda g: g.category == 'Letter' and g.subCategory == 'Uppercase' and g.script == 'latin', Glyphs.font.glyphs)

        self.proof_mode = 'waterfall'
        self.parameters = {
            'padding': {
                'left': 20,
                'right': 70,
                'top': 20,
                'bottom': 100,
                'line': 20,
                'block': 20
            },
            'masters': [],
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
            (ELEMENT_PADDING, ELEMENT_PADDING, self.window_width - 2 * ELEMENT_PADDING, SECTION_SELECTOR_HEIGHT),
            [dict(title="Templates"), dict(title="Glyphs"), dict(title="Edit")],
            callback=self.triggerSetActiveSection)

        primaryGroupPosSize = (ELEMENT_PADDING,
            2*ELEMENT_PADDING + SECTION_SELECTOR_HEIGHT,
            self.window_width - 2 * ELEMENT_PADDING,
            self.window_height * (MAIN_PANEL_HEIGHT_FACTOR + 0.15))


        self.group.templates = Group(primaryGroupPosSize)
        self.group.templates.list = List(
            (0, 0, -0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR),
            map(lambda x: self.formatTemplateForDisplayList(x), self.templates.data),
            columnDescriptions=[{"title": "Name"}],
            selectionCallback=self.triggerLoadSelectedTemplate,
            drawFocusRing=False,
            allowsSorting=False,
            allowsEmptySelection=True,
            allowsMultipleSelection=False,
            rowHeight=20.0
        )

        self.group.templates.openTemplate = Button(
            (0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR, 150, 30), "Open Template",
            callback=self.triggerOpenTemplate)

        self.group.templates.loadTemplate = Button(
            (150 + ELEMENT_PADDING, self.window_height * MAIN_PANEL_HEIGHT_FACTOR, 200, 30), "Save Proof as Template",
            callback=self.triggerSaveProofAsTemplate)

        self.group.templates.show(False)


        #
        # Edit View List
        #
        I_MASTERS_LIST = self.instance_masters
        M_MASTERS_LIST = map(lambda m: m.name, Glyphs.font.masters)
        MASTERS_LIST = sorted(list(set(I_MASTERS_LIST + M_MASTERS_LIST)))

        self.group.parameters = Group(primaryGroupPosSize)

        self.group.parameters.list = List(
            (0, 0, -0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR),
            [{"Style": MASTERS_LIST[0], "Point Size": 72}],
            columnDescriptions=[
                {
                    "title": "Style",
                    "cell": PopUpButtonListCell(MASTERS_LIST),
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
        self.group.parameters.addRow = Button(
            (0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR, 50, 30), "+",
            callback=self.triggerAddRowToParametersList)

        self.group.parameters.removeRow = Button(
            (50 + ELEMENT_PADDING, self.window_height * MAIN_PANEL_HEIGHT_FACTOR, 50, 30), "-",
            callback=self.triggerRemoveSelectedFromParametersList)

        self.group.parameters.show(False)

        #
        # Glyphset View
        #

        self.group.glyphsset = Group(primaryGroupPosSize)
        self.group.glyphsset.selectionLabel = TextBox((0, 10, -0, -0), "Glyphs From Selection")
        self.group.glyphsset.selectionDescription = TextBox((0, 35, primaryGroupPosSize[2] / 2, -0), "Select the glyphs for this proof in the Font Window.", sizeStyle="small")

        self.group.glyphsset.fromSelectionButton = Button(
        (primaryGroupPosSize[2] / 2 + ELEMENT_PADDING, 35, primaryGroupPosSize[2] / 2 - 2 * ELEMENT_PADDING, 20),
        "From Selection", callback=self.triggerSetGlyphsFromSelection )

        EDIT_VIEW_OFFSET = 200

        self.group.glyphsset.line = HorizontalLine((0, EDIT_VIEW_OFFSET - 25, -0, 2))

        self.group.glyphsset.editViewLabel = TextBox((0, EDIT_VIEW_OFFSET, -0, -0), "Glyphs From Edit View")
        self.group.glyphsset.editViewDescription = TextBox((0, EDIT_VIEW_OFFSET + 25, primaryGroupPosSize[2] / 2, -0), "Use the edit view to create the content of this proof.", sizeStyle="small")

        self.group.glyphsset.fromEditViewButton = Button(
        (primaryGroupPosSize[2] / 2 + ELEMENT_PADDING, EDIT_VIEW_OFFSET + 25, primaryGroupPosSize[2] / 2 - 2 * ELEMENT_PADDING, 20),
        "From Current Edit View", callback=self.triggerSetGlyphsFromEditView );


        self.group.glyphsset.show(False)

        self.group.line = HorizontalLine((ELEMENT_PADDING, primaryGroupPosSize[3] - 2 * ELEMENT_PADDING, self.window_width - 2 * ELEMENT_PADDING, 1))



        #
        # Globals Tabbed View
        #

        self.group.globals = SegmentedButton(
            (ELEMENT_PADDING, primaryGroupPosSize[3], self.window_width - 2 * ELEMENT_PADDING, SECTION_SELECTOR_HEIGHT),
            [dict(title="Layout", width=(self.window_width - 2 * ELEMENT_PADDING) / 2), dict(title="Output", width=(self.window_width - 2 * ELEMENT_PADDING) / 2)],
            callback=self.triggerSetActiveGlobal)

        globalsGroupPosSize = (
            ELEMENT_PADDING,
            primaryGroupPosSize[3] + SECTION_SELECTOR_HEIGHT + ELEMENT_PADDING,
            self.window_width - 2 * ELEMENT_PADDING,
            self.window_height * 0.2)

        self.group.margins = Group(globalsGroupPosSize)

        OFFSET_TOP = 25
        OFFSET_LEFT = 15
        ENTRY_BOX_OFFSET = 30

        self.group.margins.marginlabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET, OFFSET_TOP - 20, 100, 20), "Margins", sizeStyle="small")

        self.group.margins.toplabel = TextBox((OFFSET_LEFT, OFFSET_TOP + 4, 25, 20), "Top |", alignment="right", sizeStyle="mini")
        self.group.margins.top = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET, OFFSET_TOP, 100, 20), self.parameters['padding']['top'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)

        self.group.margins.leftlabel = TextBox((OFFSET_LEFT, OFFSET_TOP + 24, 25, 20), "Left  |", alignment="right", sizeStyle="mini")
        self.group.margins.left = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET, OFFSET_TOP + 20, 50, 20), self.parameters['padding']['left'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)

        self.group.margins.rightlabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 105, OFFSET_TOP + 24, 100, 20), "Right", alignment="left", sizeStyle="mini")
        self.group.margins.right = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET+50, OFFSET_TOP + 20, 50, 20), self.parameters['padding']['right'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)

        self.group.margins.botlabel = TextBox((OFFSET_LEFT, OFFSET_TOP + 44, 25, 20), "Bot", alignment="right", sizeStyle="mini")
        self.group.margins.bottom = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET, OFFSET_TOP + 40, 100, 20), self.parameters['padding']['bottom'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)

        self.group.margins.divider = VerticalLine((globalsGroupPosSize[2] / 2.0 + 2, ELEMENT_PADDING, 1, -ELEMENT_PADDING))

        self.group.margins.paddinglabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 200, OFFSET_TOP - 20, 100, 20), "Padding", sizeStyle="small")

        self.group.margins.linelabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 165, OFFSET_TOP + 4, 30, 20), "Line", alignment="right", sizeStyle="mini")
        self.group.margins.line = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET + 200, OFFSET_TOP, 125, 20), self.parameters['padding']['line'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)

        self.group.margins.blocklabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 165, OFFSET_TOP + 24, 30, 20), "Block", alignment="right", sizeStyle="mini")
        self.group.margins.block = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET + 200, OFFSET_TOP + 20, 125, 20), self.parameters['padding']['block'], sizeStyle="small", continuous=False, callback=self.triggerParametersListEdit)
        self.group.margins.proofMode = SegmentedButton((OFFSET_LEFT + ENTRY_BOX_OFFSET + 200, OFFSET_TOP + 40, 125, 20), [dict(title="Waterfall"), dict(title="Paragraphs")], callback=self.triggerProofModeChange, sizeStyle="mini")


        self.group.margins.show(False)


        self.group.output = Group(globalsGroupPosSize)

        self.group.output.saveprooflabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP - 20,100,20),"Proof Info", sizeStyle="small")

        self.group.output.proofnamelabel = TextBox((OFFSET_LEFT - 10,OFFSET_TOP + 4, 35,20), "Name", alignment="right", sizeStyle="mini")
        self.group.output.proofname = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP,300,20), continuous=False, callback=self.triggerParametersListEdit)

        self.group.output.prooffooterlabel = TextBox((OFFSET_LEFT - 10,OFFSET_TOP + 24,35,20), "Footer", alignment="right", sizeStyle="mini")
        self.group.output.prooffooter = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP + 20,300,20), continuous=False, callback=self.triggerParametersListEdit)

        self.group.output.saveproof = Button((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP + 45,50,20), "Save", sizeStyle="small", callback=self.saveProof )
        self.group.output.saveproof.enable(False)

        self.group.output.saveproofas = Button((OFFSET_LEFT + ENTRY_BOX_OFFSET + 45 + ELEMENT_PADDING,OFFSET_TOP + 45,75,20), "Save As...", sizeStyle="small", callback=self.saveProofAs)

        self.group.output.printproof = Button((OFFSET_LEFT + ENTRY_BOX_OFFSET + 250, OFFSET_TOP + 45,50,20), "Print", sizeStyle="small", callback=self.printProof)


        self.group.output.show(False)


        parent_window.g = self.group

        self.setActiveSection(0)
        self.setActiveGlobal(0)

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
        name = self.group.output.proofname.get()
        name = name + '.pdf' if name != '' else 'Untitled.pdf'

        result = putFile(
            title="Save Proof",
            messageText="Save Proof As...",
            fileName=name)

        if self.saveProofCallback is not None and result is not None:
            self.outputPath = result
            self.group.output.saveproof.enable(True)
            self.saveProofCallback(result)


    def triggerParametersListEdit(self, sender):
        self.tryRerender()

    def triggerParametersListSelection(self, sender):
        self.group.parameters.removeRow.enable(len(sender.getSelection()) > 0)

    def triggerLoadSelectedTemplate(self, sender):
        self.loadSelectedTemplate(self.group.templates.list.getSelection())

    def triggerProofModeChange(self, sender):
        index = int(sender.get())
        self.proof_mode = 'waterfall' if index == 0 else 'paragraphs'
        self.tryRerender()


    def loadSelectedTemplate(self, indices):
        for i in indices:

            # set this first
            template = self.templates.data[i]
            valid_names = filter(lambda n: n in Glyphs.font.glyphs, template['glyphs'])
            self.glyphs = map(lambda n: Glyphs.font.glyphs[n], valid_names)

            lines = map(lambda row: {"Style": row['style'], "Point Size": row['size']}, template['lines'])

            # margins
            self.group.margins.left.set(tryParseInt(template['proof']['margins']['left'], 0))
            self.group.margins.right.set(tryParseInt(template['proof']['margins']['right'], 0))
            self.group.margins.top.set(tryParseInt(template['proof']['margins']['top'], 0))
            self.group.margins.bottom.set(tryParseInt(template['proof']['margins']['bottom'], 0))

            self.group.margins.block.set(tryParseInt(template['proof']['padding']['block'], 0))
            self.group.margins.line.set(tryParseInt(template['proof']['padding']['line'], 0))


            self.proof_mode = template['proof']['mode']
            self.group.margins.proofMode.set(0 if self.proof_mode == 'waterfall' else 1)

            # NOTE(nic): we need to disable the callback when we update the list,
            # otherwise the editCallback will be called multiple times, resulting
            # in unnecessary re-renders.
            self.group.parameters.list._editCallback = None
            self.group.parameters.list.set(lines)
            self.group.parameters.list._editCallback = self.triggerParametersListEdit

        self.tryRerender()


    def formatTemplateForDisplayList(self, template):
        return {'Name': template['name']}


    def triggerSaveProofAsTemplate(self, sender):
        name = self.group.output.proofname.get()
        print(name)
        print(name != "")
        name = name if name != "" else "Proof"
        print(name)
        filename = '-'.join(name.lower().split(' ')) + '.json'

        print(filename)

        template = OrderedDict()
        template['name'] = name
        template['lines'] = map(lambda l: {"style": l["Style"], "size": int(l["Point Size"])}, self.group.parameters.list)
        template['proof'] = {
            "margins": {
                "left": int(self.group.margins.left.get()),
                "right": int(self.group.margins.right.get()),
                "top": int(self.group.margins.top.get()),
                "bottom": int(self.group.margins.bottom.get())
            },
            "padding": {
                "block": int(self.group.margins.block.get()),
                "line": int(self.group.margins.line.get())
            },
            "mode": self.proof_mode
        }

        template['glyphs'] = map(lambda g: g.name, self.glyphs)

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

    def triggerSetActiveGlobal(self, sender):
        self.setActiveGlobal(int(sender.get()))

    def triggerAddRowToParametersList(self, sender):
        if len(self.group.parameters.list) > 0:
            last_style = self.group.parameters.list[-1]['Style']
            last_ptsz = self.group.parameters.list[-1]['Point Size']
            self.group.parameters.list.append({"Style": last_style, "Point Size": last_ptsz})

        else:
            self.group.parameters.list.append({
                "Style": self.instance_masters[0],
                "Point Size": 24})

    def triggerRemoveSelectedFromParametersList(self, sender):
        for index in reversed(self.group.parameters.list.getSelection()):
            del self.group.parameters.list[index]

    def triggerSetGlyphsFromSelection(self, sender):
        self.glyphs = filter(lambda g: g.selected, Glyphs.font.glyphs)
        self.tryRerender()


    def triggerSetGlyphsFromEditView(self, sender):
        if Glyphs.font.currentTab is not None:
            self.glyphs = map(lambda l: l.parent, Glyphs.font.currentTab.layers)
            self.tryRerender()


    def parametersChanged(self, parameters, glyphs):
        glyphsChanged = glyphs[0] != self.parameters['glyphs'][0]

        layoutChanged = parameters['padding'] != self.parameters['padding']
        mastersChanged = parameters['masters'] != self.parameters['masters']
        sizesChanged = parameters['point_sizes'] != self.parameters['point_sizes']
        titleChanged = parameters['title'] != self.parameters['title']
        footerChanged = parameters['footer'] != self.parameters['footer']
        modeChanged = parameters['mode'] != self.parameters['mode']

        paramsChanged = layoutChanged or mastersChanged or sizesChanged or modeChanged
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
        self.group.glyphsset.show(index == 1)
        self.group.parameters.show(index == 2)

    def setActiveGlobal(self, index):
        if index != 0 and index != 1: return

        self.group.globals.set(index)
        self.group.margins.show(index == 0)
        self.group.output.show(index == 1)


    def getGlyphSet(self):
        return [self.glyphs]


    def getParameterSet(self):

        masters = []
        point_sizes = []

        pre_interpolation = default_timer()

        for i, item in enumerate(self.group.parameters.list):
            size_dirty = item['Point Size']
            size_clean = re.sub('[^0-9]', '', str(size_dirty))
            size = tryParseInt(size_clean, 72)

            master = []

            if len(self.instance_masters) > 0:
                # master = filter(lambda i: i.masters[0].name == item['Style'], self.instance_masters) # NOTE: Changed from .masters to .instances

                master = filter(lambda i: i == item['Style'], self.instance_masters)

                if len(master) > 0:
                    master_name = master[0]

                    if master_name not in self.interpolated_instances:
                        # we haven't interpolated this instance yet.
                        # interpolate the instance and store it in our shared instance cache for future use.
                        instance = filter(lambda i: i.name == master_name, Glyphs.font.instances)

                        # NOTE(nic): trying out `interpolatedFontProxy` here instead of `interpolatedFont`.
                        # accoding to [the docs](https://docu.glyphsapp.com/#GSInstance.interpolatedFontProxy),
                        # iterpolatedFontProxy interpolates glyphs on demand, rather than interpolating the entire instance.
                        # This means we do work proportional to the glyphs in the proof, rather than in the font.
                        self.interpolated_instances[master_name] = instance[0].interpolatedFontProxy

                    master = [ self.interpolated_instances[master_name].masters[0] ]


            if len(master) == 0:
                # we didn't find any matching instance names, look up the name to see
                # if it occurs in the masters.
                master = filter(lambda m: m.name == item['Style'], Glyphs.font.masters)

            if len(master) == 1:
                masters.append([0, master[0]])
                point_sizes.append(size)

            else:
                print("[unknown style] couldn't find a unique style matching '%s'; skipping." % item['Style'] )

        print('[profile] time to interpolate: %.03f seconds' % (default_timer() - pre_interpolation))

        parameters = {
            'padding': {
                'left': tryParseInt(self.group.margins.left.get(), self.parameters['padding']['left']),
                'right': tryParseInt(self.group.margins.right.get(), self.parameters['padding']['right']),
                'top': tryParseInt(self.group.margins.top.get(), self.parameters['padding']['top']),
                'bottom': tryParseInt(self.group.margins.bottom.get(), self.parameters['padding']['bottom']),
                'line': tryParseInt(self.group.margins.line.get(), self.parameters['padding']['line']),
                'block': tryParseInt(self.group.margins.block.get(), self.parameters['padding']['block'])
            },
            'masters': masters,
            'instances': self.interpolated_instances,
            'point_sizes': map(int, point_sizes),
            'aligned': True,
            'document': {'width': 11, 'height': 8.5},
            'title': self.group.output.proofname.get(),
            'footer': self.group.output.prooffooter.get(),
            'mode': self.proof_mode
        }

        return parameters
