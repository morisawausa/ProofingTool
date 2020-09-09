#MenuTitle: Modular Proof
# -*- coding: utf-8 -*-
__doc__="""
Starts the proofing environment
"""

from AppKit import *
from vanilla import *
from vanilla.dialogs import putFile
from GlyphsApp.UI import *

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.drawBotContext import DrawBotContext
from drawBot.ui.drawView import DrawView

from layout import OCCProofingLayout

TEXT_PLACEMENT = 20
WINDOW_WIDTH = 400 # In PIXELS
PAGE_WIDTH = 8.5 # in inches
PAGE_HEIGHT = 11.0 # in inches
LETTER_PORTAIT_RATIO = PAGE_HEIGHT / PAGE_WIDTH

ELEMENT_PADDING = 5
SECTION_SELECTOR_HEIGHT = 20
MAIN_PANEL_HEIGHT_FACTOR = 0.6

MASTERS_LIST = map(lambda m: m.name, Glyphs.font.masters)
GLYPHS = filter(lambda g: g.subCategory == 'Uppercase' and g.script == 'latin',  Glyphs.font.glyphs)

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

        self.outputPath = None

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
        }


        self.group = Group((self.window_width, 0, self.window_width, self.window_height))


        #
        # Segmented Button at the top of View:
        # Lets you switch between templates, edit, and glyphs.
        #

        self.group.sections = SegmentedButton(
            (ELEMENT_PADDING, ELEMENT_PADDING, self.window_width - 2 * ELEMENT_PADDING, SECTION_SELECTOR_HEIGHT),
            [dict(title="Templates"), dict(title="Edit"), dict(title="Glyphs")],
            callback=self.triggerSetActiveSection)

        primaryGroupPosSize = (ELEMENT_PADDING,
            2*ELEMENT_PADDING + SECTION_SELECTOR_HEIGHT,
            self.window_width - 2 * ELEMENT_PADDING,
            self.window_height * (MAIN_PANEL_HEIGHT_FACTOR + 0.15))




        self.group.templates = Group(primaryGroupPosSize)
        self.group.templates.text = TextBox((0, 0, -0, -0), "Templates View")
        self.group.templates.show(False)




        self.group.parameters = Group(primaryGroupPosSize)
        # self.group.parameters.text = TextBox((0, 0, -0, -0), "Parameters View")
        self.group.parameters.list = List(
            (0, 0, -0, self.window_height * MAIN_PANEL_HEIGHT_FACTOR),
            [{"Style": MASTERS_LIST[5], "Point Size": 72}],
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
            selectionCallback=self.triggerParametersListSelection,
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

        self.group.glyphsset = Group(primaryGroupPosSize)
        self.group.glyphsset.text = TextBox((0, 0, -0, -0), "Glyphs View")
        self.group.glyphsset.show(False)

        self.group.line = HorizontalLine((ELEMENT_PADDING, primaryGroupPosSize[3] - 2 * ELEMENT_PADDING, self.window_width - 2 * ELEMENT_PADDING, 1))


        self.group.globals = SegmentedButton(
            (ELEMENT_PADDING, primaryGroupPosSize[3], self.window_width - 2 * ELEMENT_PADDING, SECTION_SELECTOR_HEIGHT),
            [dict(title="Margins & Padding", width=(self.window_width - 2 * ELEMENT_PADDING) / 2), dict(title="Output", width=(self.window_width - 2 * ELEMENT_PADDING) / 2)],
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
        self.group.margins.top = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET, OFFSET_TOP, 100, 20), self.parameters['padding']['top'], sizeStyle="small", callback=self.triggerParametersListEdit)

        self.group.margins.leftlabel = TextBox((OFFSET_LEFT, OFFSET_TOP + 24, 25, 20), "Left  |", alignment="right", sizeStyle="mini")
        self.group.margins.left = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET, OFFSET_TOP + 20, 50, 20), self.parameters['padding']['left'], sizeStyle="small", callback=self.triggerParametersListEdit)

        self.group.margins.rightlabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 105, OFFSET_TOP + 24, 100, 20), "Right", alignment="left", sizeStyle="mini")
        self.group.margins.right = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET+50, OFFSET_TOP + 20, 50, 20), self.parameters['padding']['right'], sizeStyle="small", callback=self.triggerParametersListEdit)

        self.group.margins.botlabel = TextBox((OFFSET_LEFT, OFFSET_TOP + 44, 25, 20), "Bot", alignment="right", sizeStyle="mini")
        self.group.margins.bottom = EditText((OFFSET_LEFT+ENTRY_BOX_OFFSET, OFFSET_TOP + 40, 100, 20), self.parameters['padding']['bottom'], sizeStyle="small", callback=self.triggerParametersListEdit)

        self.group.margins.divider = VerticalLine((globalsGroupPosSize[2] / 2.0 + 2, ELEMENT_PADDING, 1, -ELEMENT_PADDING))

        self.group.margins.paddinglabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 200, OFFSET_TOP - 20, 100, 20), "Padding", sizeStyle="small")

        self.group.margins.linelabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 165, OFFSET_TOP + 4, 30, 20), "Line", alignment="right", sizeStyle="mini")
        self.group.margins.line = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET + 200, OFFSET_TOP, 100, 20), self.parameters['padding']['line'], sizeStyle="small", callback=self.triggerParametersListEdit)

        self.group.margins.blocklabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET + 165, OFFSET_TOP + 24, 30, 20), "Block", alignment="right", sizeStyle="mini")
        self.group.margins.block = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET + 200, OFFSET_TOP + 20, 100, 20), self.parameters['padding']['block'], sizeStyle="small", callback=self.triggerParametersListEdit)

        self.group.margins.show(False)


        self.group.output = Group(globalsGroupPosSize)

        self.group.output.saveprooflabel = TextBox((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP - 20,100,20),"Proof Info", sizeStyle="small")

        self.group.output.proofnamelabel = TextBox((OFFSET_LEFT - 10,OFFSET_TOP + 4, 35,20), "Name", alignment="right", sizeStyle="mini")
        self.group.output.proofname = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP,300,20), callback=self.triggerParametersListEdit)

        self.group.output.prooffooterlabel = TextBox((OFFSET_LEFT - 10,OFFSET_TOP + 24,35,20), "Footer", alignment="right", sizeStyle="mini")
        self.group.output.prooffooter = EditText((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP + 20,300,20), callback=self.triggerParametersListEdit)

        self.group.output.saveproof = Button((OFFSET_LEFT + ENTRY_BOX_OFFSET,OFFSET_TOP + 45,50,20), "Save", sizeStyle="small", callback=self.saveProof )
        self.group.output.saveproof.enable(False)

        self.group.output.saveproofas = Button((OFFSET_LEFT + ENTRY_BOX_OFFSET + 45 + ELEMENT_PADDING,OFFSET_TOP + 45,75,20), "Save As...", sizeStyle="small", callback=self.saveProofAs)

        self.group.output.printproof = Button((OFFSET_LEFT + ENTRY_BOX_OFFSET + 250, OFFSET_TOP + 45,50,20), "Print", sizeStyle="small", callback=self.printProof)


        self.group.output.show(False)


        # self.group.proofname = EditText(
        #     (ELEMENT_PADDING, self.window_height - 20 - ELEMENT_PADDING, self.window_width * 0.75, 20),
        #     placeholder="Proof Name...")

        # self.group.saveButton = Button(
        #     (self.window_width * 0.75 + 2 * ELEMENT_PADDING,
        #      self.window_height - 20 - ELEMENT_PADDING,
        #      self.window_width * 0.25 - 3 * ELEMENT_PADDING,
        #      20), "Save Proof")


        parent_window.g = self.group

        self.setActiveSection(1)
        self.setActiveGlobal(0)

        if self.parametersChangedCallback is not None:
            self.parametersChangedCallback(self.getParameterSet())


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


    def setProofTitle(self, sender):
        print(sender.get())

    def triggerParametersListEdit(self, sender):
        self.parametersChangedCallback(self.getParameterSet())


    def triggerParametersListSelection(self, sender):
        self.group.parameters.removeRow.enable(len(sender.getSelection()) > 0)

    def triggerSetActiveSection(self, sender):
        self.setActiveSection(int(sender.get()))

    def triggerSetActiveGlobal(self, sender):
        self.setActiveGlobal(int(sender.get()))

    def triggerAddRowToParametersList(self, sender):
        self.group.parameters.list.append({
            "Style": MASTERS_LIST[0],
            "Point Size": 12})

    def triggerRemoveSelectedFromParametersList(self, sender):
        for index in reversed(self.group.parameters.list.getSelection()):
            del self.group.parameters.list[index]


    def setActiveSection(self, index):
        if index != 0 and index != 1 and index != 2: return

        self.group.sections.set(index)
        self.group.templates.show(index == 0)
        self.group.parameters.show(index == 1)
        self.group.glyphsset.show(index == 2)

    def setActiveGlobal(self, index):
        if index != 0 and index != 1: return

        self.group.globals.set(index)
        self.group.margins.show(index == 0)
        self.group.output.show(index == 1)


    def getParameterSet(self):

        masters = []
        point_sizes = []

        for item in self.group.parameters.list:
            point_sizes.append(int(item['Point Size']))
            master = filter(lambda m: m.name == item['Style'], Glyphs.font.masters)
            masters.append(master[0])


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
            'point_sizes': map(int, point_sizes),
            'aligned': False,
            'document': {'width': 11, 'height': 8.5},
            'title': self.group.output.proofname.get(),
            'footer': self.group.output.prooffooter.get()
        }

        return parameters




class OCCProofingTool:
    def __init__(self):
        # Unit Arithmetic
        self.em_per_u = 1.0 / Glyphs.font.upm
        self.in_per_pt = 0.0138889
        self.px_per_in = 612 / PAGE_WIDTH


        self.height, self.width = _drawBotDrawingTool.sizes('Letter')
        self.window_width, self.window_height = WINDOW_WIDTH, (WINDOW_WIDTH * (11.0 / 8.5))

        self.mainWindow = Window(
            (self.window_width * 2, self.window_height),
            "Modular Proof",
            textured=False)

        self.drawView = DrawView((0, 0, self.window_width, -0))
        self.mainWindow.drawing = self.drawView;
        self.kerning = False

        self.layersets = []

        self.parameters = {}

        self.parametersView = OCCParametersView(
            self.window_width,
            self.window_height,
            self.mainWindow,
            parametersChangedCallback=self.updateParametersAndRedraw,
            saveProofCallback=self.saveProof,
            printProofCallback=self.printProof)

        self.mainWindow.open()

    def updateParametersAndRedraw(self, parameters):
        self.parameters = parameters
        self.layersets = map(lambda _: GLYPHS, parameters['masters'])
        self.draw(preview=True)

    def calculate_scale(self, pts_per_em):
        return self.em_per_u * \
            self.in_per_pt * \
            self.px_per_in * \
            pts_per_em


    def saveProof(self, filename):
        self.draw(preview=False)
        _drawBotDrawingTool.saveImage(filename)

    def printProof(self):
        self.draw(preview=False)
        _drawBotDrawingTool.printImage()


    def draw(self, preview = True):
        proof = OCCProofingLayout(self.layersets[0], self.parameters, self.width, self.height, Glyphs.font.upm).get()
        # print(test_proof)

        # proof = self.layout(self.width, self.height)
        context = DrawBotContext()

        _drawBotDrawingTool.newDrawing()
        _drawBotDrawingTool.fontSize(8)

        # ==
        # Render full document
        # ==
        if self.parameters['title'] != '' and self.parameters['footer'] != '':
            text = '%s - %s' % (self.parameters['title'], self.parameters['footer'])
        elif self.parameters['title'] != '' or self.parameters['footer'] != '':
            text = self.parameters['title'] + self.parameters['footer']
        else:
            text = ''

        for i, page in enumerate(proof if preview else proof):
            _drawBotDrawingTool.newPage(self.width, self.height)
            _drawBotDrawingTool.fontSize(8)

            _drawBotDrawingTool.fill(1,1,1)
            _drawBotDrawingTool.rect(0,0,self.width, self.height)
            _drawBotDrawingTool.fill(0,0,0)

            for layer in page:
                _drawBotDrawingTool.drawPath(layer.completeBezierPath)

            _drawBotDrawingTool.fill(0.5, 0.5, 0.5)

            page = 'pg. %s' % str(i+1)

            if self.parameters['padding']['bottom'] > TEXT_PLACEMENT:
                _drawBotDrawingTool.text(text, (self.parameters['padding']['left'], TEXT_PLACEMENT))
                _drawBotDrawingTool.text(page, (self.width - self.parameters['padding']['left'] - 20, TEXT_PLACEMENT))

        # _drawBotDrawingTool.printImage()
        #_drawBotDrawingTool.saveImage("/Users/nic/Desktop/proof.pdf")

        _drawBotDrawingTool._drawInContext(context)
        pdfDocument = context.getNSPDFDocument()
        self.drawView.setPDFDocument(pdfDocument)


OCCProofingTool()
