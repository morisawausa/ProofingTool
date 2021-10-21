#MenuTitle: Modular Proof
# -*- coding: utf-8 -*-
__doc__="""
Starts the proofing environment
"""
# import sys
# parent_dir = os.path.abspath(os.path.dirname(__file__))
# vendor_dir = os.path.join(parent_dir, 'lib')
# sys.path.append(vendor_dir)

from timeit import default_timer

from AppKit import *
from vanilla import *
from vanilla.dialogs import putFile
from GlyphsApp.UI import *
from datetime import datetime

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.drawBotContext import DrawBotContext
from drawBot.ui.drawView import DrawView

from layout import PROOFING_LAYOUTS
from parameters import OCCParametersView

TEXT_PLACEMENT = 20
WINDOW_WIDTH = 400 # In PIXELS
TIMING = True

GLYPHS = list(filter(lambda g: g.subCategory == 'Uppercase' and g.script == 'latin',  Glyphs.font.glyphs))


class OCCProofingTool:
    def __init__(self):
        # Unit Arithmetic
        self.em_per_u = 1.0 / Glyphs.font.upm
        self.in_per_pt = 0.0138889
        self.px_per_in = 612.0 / 8.5 # Drawbot pixel / inch ratio


        self.height, self.width = _drawBotDrawingTool.sizes('Letter')
        self.window_width, self.window_height = WINDOW_WIDTH, (WINDOW_WIDTH * (11.0 / 8.5))

        self.mainWindow = Window(
            (self.window_width * 2, self.window_height),
            "Modular Proof",
            textured=False)

        self.drawView = DrawView((0, 0, self.window_width, -0))
        self.mainWindow.drawing = self.drawView;
        self.kerning = False

        self.glyphs = []

        self.parameters = {}

        self.parametersView = OCCParametersView(
            self.window_width,
            self.window_height,
            self.mainWindow,
            parametersChangedCallback=self.updateParametersAndRedraw,
            saveProofCallback=self.saveProof,
            printProofCallback=self.printProof)

        self.mainWindow.open()

    def updateParametersAndRedraw(self, parameters, glyphs):
        self.parameters = parameters
        self.glyphs = glyphs
        self.draw(preview=True)

    def saveProof(self, filename):
        self.draw(preview=False)
        _drawBotDrawingTool.saveImage(filename)

    def printProof(self):
        self.draw(preview=False)
        _drawBotDrawingTool.printImage()


    def draw(self, preview = True):

        proof_mode = self.parameters['mode']
        # choose the right layout class based on the layout mode: 'waterfall' or 'paragraphs'
        pre_generate_proof = default_timer()
        proof = PROOFING_LAYOUTS[proof_mode](self.glyphs, self.parameters, self.width, self.height, Glyphs.font.upm).get()
        post_generate_proof = default_timer()

        context = DrawBotContext()

        pre_render_proof = default_timer()
        _drawBotDrawingTool.newDrawing()
        _drawBotDrawingTool.fontSize(8) # used to specify the font-size for the metadata at the bottom of the page.

        # ==
        # Render full document
        # ==
        now = datetime.now()
        text = now.strftime("%m/%d/%Y %H:%M")
        if self.parameters['title'] != '' and self.parameters['footer'] != '':
            text = ('%s - %s' % (self.parameters['title'], self.parameters['footer'])) + ' - ' + text
        elif self.parameters['title'] != '' or self.parameters['footer'] != '':
            text = self.parameters['title'] + self.parameters['footer'] + ' - ' + text

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

        #_drawBotDrawingTool.printImage()
        #_drawBotDrawingTool.saveImage("/Users/nic/Desktop/proof.pdf")

        _drawBotDrawingTool._drawInContext(context)
        pdfDocument = context.getNSPDFDocument()
        self.drawView.setPDFDocument(pdfDocument)

        post_render_proof = default_timer()

        print('[profile] time to compile: %.03f seconds' % (post_generate_proof - pre_generate_proof))
        print('[profile] time to render: %.03f seconds' % (post_render_proof - pre_render_proof))
        print('[profile] done.\n')


OCCProofingTool()
