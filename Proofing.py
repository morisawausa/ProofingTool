#MenuTitle: Modular Proof
# -*- coding: utf-8 -*-
__doc__="""
Starts the proofing environment
"""

from AppKit import *
from vanilla import *
from GlyphsApp.UI import *

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.drawBotContext import DrawBotContext
from drawBot.ui.drawView import DrawView

WINDOW_WIDTH = 400 # In PIXELS
PAGE_WIDTH = 8.5 # in inches
PAGE_HEIGHT = 11.0 # in inches
LETTER_PORTAIT_RATIO = PAGE_HEIGHT / PAGE_WIDTH

ELEMENT_PADDING = 5
SECTION_SELECTOR_HEIGHT = 20
MASTERS_LIST = map(lambda m: m.name, Glyphs.font.masters)
GLYPHS = filter(lambda g: g.subCategory == 'Uppercase' and g.script == 'latin',  Glyphs.font.glyphs)


class OCCDrawingView:
    def __init__(self, width_px, height_px, parent_window):
        pass


class OCCParametersView:
    def __init__(self, width_px, height_px, parent_window, parametersChangedCallback=None):
        self.window_width = width_px
        self.window_height = height_px
        self.parametersChangedCallback = parametersChangedCallback

        self.group = Group((self.window_width, 0, self.window_width, self.window_height))

        self.group.sections = SegmentedButton(
            (ELEMENT_PADDING, ELEMENT_PADDING, self.window_width - 2 * ELEMENT_PADDING, SECTION_SELECTOR_HEIGHT),
            [dict(title="Templates"), dict(title="Parameters"), dict(title="Glyphset")],
            callback=self.triggerSetActiveSection)

        primaryGroupPosSize = (ELEMENT_PADDING,
            2*ELEMENT_PADDING + SECTION_SELECTOR_HEIGHT,
            self.window_width - 2 * ELEMENT_PADDING,
            self.window_height * 0.75)




        self.group.templates = Group(primaryGroupPosSize)
        self.group.templates.text = TextBox((0, 0, -0, -0), "Templates View")
        self.group.templates.show(False)




        self.group.parameters = Group(primaryGroupPosSize)
        # self.group.parameters.text = TextBox((0, 0, -0, -0), "Parameters View")
        self.group.parameters.list = List(
            (0, 0, -0, self.window_height * 0.7),
            [{"Line": 1, "Style": MASTERS_LIST[0], "Point Size": 12}],
            columnDescriptions=[
                {
                    "title": "Line",
                    "editable": False
                },
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
            (0, self.window_height * 0.7, 50, 30), "+",
            callback=self.triggerAddRowToParametersList)

        self.group.parameters.removeRow = Button(
            (50 + ELEMENT_PADDING, self.window_height * 0.7, 50, 30), "-",
            callback=self.triggerRemoveSelectedFromParametersList)

        self.group.parameters.show(False)

        self.group.glyphsset = Group(primaryGroupPosSize)
        self.group.glyphsset.text = TextBox((0, 0, -0, -0), "Glyphs View")
        self.group.glyphsset.show(False)

        # self.group.proofname = EditText(
        #     (ELEMENT_PADDING, self.window_height - 20 - ELEMENT_PADDING, self.window_width * 0.75, 20),
        #     placeholder="Proof Name...")

        self.group.saveButton = Button(
            (self.window_width * 0.75 + 2 * ELEMENT_PADDING,
             self.window_height - 20 - ELEMENT_PADDING,
             self.window_width * 0.25 - 3 * ELEMENT_PADDING,
             20), "Save Proof")


        parent_window.g = self.group

        self.setActiveSection(1)
        if self.parametersChangedCallback is not None:
            self.parametersChangedCallback(self.getParameterSet())


    def setProofTitle(self, sender):
        print(sender.get())

    def triggerParametersListEdit(self, sender):
        self.parametersChangedCallback(self.getParameterSet())


    def triggerParametersListSelection(self, sender):
        self.group.parameters.removeRow.enable(len(sender.getSelection()) > 0)

    def triggerSetActiveSection(self, sender):
        self.setActiveSection(int(sender.get()))

    def triggerAddRowToParametersList(self, sender):
        self.group.parameters.list.append({
            "Line": len(self.group.parameters.list) + 1,
            "Style": MASTERS_LIST[0],
            "Point Size": 12})

    def triggerRemoveSelectedFromParametersList(self, sender):
        for index in reversed(self.group.parameters.list.getSelection()):
            del self.group.parameters.list[index]

        for i, element in enumerate(self.group.parameters.list):
            self.group.parameters.list[i]["Line"] = i + 1


    def setActiveSection(self, index):
        if index != 0 and index != 1 and index != 2: return

        self.group.sections.set(index)
        self.group.templates.show(index == 0)
        self.group.parameters.show(index == 1)
        self.group.glyphsset.show(index == 2)

    def getParameterSet(self):

        masters = []
        point_sizes = []

        for item in self.group.parameters.list:
            point_sizes.append(int(item['Point Size']))
            master = filter(lambda m: m.name == item['Style'], Glyphs.font.masters)
            masters.append(master[0])

        parameters = {
            'padding': {'left': 20, 'right': 70, 'top': 20, 'bottom': 100, 'line': 100},
            'masters': masters,
            'point_sizes': map(int, point_sizes),
            'aligned': False
        }

        return parameters




class OCCProofingTool:
    def __init__(self):
        # Unit Arithmetic
        self.em_per_u = 1.0 / Glyphs.font.upm
        self.in_per_pt = 0.0138889
        self.px_per_in = WINDOW_WIDTH / PAGE_WIDTH


        self.width, self.height = _drawBotDrawingTool.sizes('Letter')
        self.window_width, self.window_height = WINDOW_WIDTH, (WINDOW_WIDTH * (float(self.height) / float(self.width)))

        print(self.window_width, self.window_height)

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
            parametersChangedCallback=self.updateParametersAndRedraw)

        self.mainWindow.open()



    def calculate_scale(self, pts_per_em):
        return self.em_per_u * \
            self.in_per_pt * \
            self.px_per_in * \
            pts_per_em

    def updateParametersAndRedraw(self, parameters):
        self.parameters = parameters
        self.layersets = map(lambda _: GLYPHS, parameters['masters'])
        self.draw()


    def draw(self):
        proof = self.layout(self.width, self.height)
        context = DrawBotContext()

        _drawBotDrawingTool.newDrawing()
        _drawBotDrawingTool.fontSize(10)

        for page in proof:
            _drawBotDrawingTool.newPage(self.width, self.height)
            _drawBotDrawingTool.save()

            _drawBotDrawingTool.fill(1,1,1)
            _drawBotDrawingTool.rect(0,0,self.width, self.height)
            _drawBotDrawingTool.fill(0,0,0)

            for layer in page:
                _drawBotDrawingTool.drawPath(layer.completeBezierPath)

            _drawBotDrawingTool.fill(0.5, 0.5, 0.5)
            _drawBotDrawingTool.text("test", (self.parameters['padding']['left'], self.parameters['padding']['top']))

            _drawBotDrawingTool.restore()

        _drawBotDrawingTool.saveImage("/Users/nic/Desktop/proof.pdf")

        _drawBotDrawingTool._drawInContext(context)
        pdfDocument = context.getNSPDFDocument()
        self.drawView.setPDFDocument(pdfDocument)





    def layout(self, width, height):
        """Takes a list of lists of layers,
        and applies a positioning transform to each one,
        followed by a scale transform.
        """
        result = [[]]
        page_index = 0

        padding_px = self.parameters['padding']
        lineheight_ratio = 1.75
        base_y_offset_px = 0

        def get_max_heights_and_lineheights():
            max_heights_u = []
            for i, sequence in enumerate(self.layersets):
                M = self.parameters['masters'][i]
                max_heights_u.append( max(map(lambda g: g.layers[M.id].master.ascender - min(0, g.layers[M.id].master.ascender), sequence)) )

            return max_heights_u

        def get_scalefactors():
            result = []
            for i, sequence in enumerate(self.layersets):
                result.append(self.calculate_scale(self.parameters['point_sizes'][i]))

            return result;


        max_heights_u = get_max_heights_and_lineheights()
        u_to_pxs = get_scalefactors()

        max_u_to_px = max(u_to_pxs)
        sequence_advance_px = sum(map(lambda (h,s): h * s * lineheight_ratio, zip(max_heights_u, u_to_pxs))) + padding_px['line']

        for i, sequence in enumerate(self.layersets):
            u_to_px = u_to_pxs[i]
            M = self.parameters['masters'][i]
            max_height_u = max_heights_u[i]

            # reset advances
            advance_y_px = height - padding_px['top'] - (max_height_u * u_to_px) - base_y_offset_px
            advance_x_px = padding_px['left']

            for j, glyph in enumerate(sequence):
                main_layer = glyph.layers[M.id]

                if self.parameters['aligned']:
                    layer_width_px = max(map(lambda (k,s): s[j].layers[self.parameters['masters'][k].id].width, enumerate(self.layersets))) * u_to_px
                else:
                    layer_width_px = main_layer.width * u_to_px

                # Check page boundaries
                if (advance_x_px + layer_width_px > width - padding_px['right']):
                    advance_x_px = padding_px['left']
                    advance_y_px -= sequence_advance_px

                    if advance_y_px < padding_px['bottom']:
                        page_index += 1

                        if page_index >= len(result): result.append([])

                        advance_y_px = height - padding_px['top'] - (max_height_u * u_to_px) - base_y_offset_px

                orphan_layer = main_layer.copyDecomposedLayer()
                orphan_layer.applyTransform((u_to_px, 0.0, 0.0, u_to_px, advance_x_px, advance_y_px))
                advance_x_px += layer_width_px
                result[page_index].append(orphan_layer)

            page_index = 0
            base_y_offset_px += lineheight_ratio * max_height_u * u_to_px

        return result

OCCProofingTool()
