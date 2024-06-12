from GlyphsApp import *
from GlyphsApp.UI import *
from timeit import default_timer
from vanilla import *
from vanilla.dialogs import putFile
from datetime import datetime

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.drawBotContext import DrawBotContext
from drawBot.ui.drawView import DrawView

from layout import PROOFING_LAYOUTS
from parameters import OCCParametersView

TEXT_PLACEMENT = 20
WINDOW_WIDTH = 500 # In PIXELS
TIMING = False # For performance-testing how long proofs take to generate

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
			"Proofing Tool",
			textured=False)

		self.drawView = DrawView((0, 0, self.window_width, -0))
		self.mainWindow.drawing = self.drawView;
		self.mainWindow.drawing.introText = TextBox((0, self.window_height/2, self.window_width, 50), "Select a template or load a new template (+) to apply.", sizeStyle="regular", alignment = "center")
		self.kerning = False
		self.debug = False

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
		self.mainWindow.drawing.introText.show(0)		

		proof_mode = self.parameters['mode']
		# choose the right layout class based on the layout mode: 'waterfall' or 'paragraphs'
		if TIMING: pre_generate_proof = default_timer() 
		proof = PROOFING_LAYOUTS[proof_mode](self.glyphs, self.parameters, self.width, self.height, Glyphs.font.upm).get()
		if TIMING: post_generate_proof = default_timer() 

		context = DrawBotContext()

		if TIMING: pre_render_proof = default_timer() 
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

		#print('PROOF', proof)
		#print('CANVAS', self.width, self.height)

		for i, page in enumerate(proof if preview else proof):
			_drawBotDrawingTool.newPage(self.width, self.height)
			_drawBotDrawingTool.fontSize(8)

			_drawBotDrawingTool.fill(1,1,1)
			_drawBotDrawingTool.rect(0,0,self.width, self.height)
			_drawBotDrawingTool.fill(0,0,0)

			for layer in page:
				path = _drawBotDrawingTool.BezierPath( layer['path'].completeBezierPath )
				path.scale(layer['scale'])
				path.translate( layer['x'], layer['y'] )
				_drawBotDrawingTool.drawPath(path)

			_drawBotDrawingTool.fill(0.5, 0.5, 0.5)

			page = 'pg. %s' % str(i+1)

			if self.parameters['gaps']['bottom'] > TEXT_PLACEMENT:
				_drawBotDrawingTool.text(text, (self.parameters['gaps']['left'], TEXT_PLACEMENT))
				_drawBotDrawingTool.text(page, (self.width - self.parameters['gaps']['left'] - 20, TEXT_PLACEMENT))

		#_drawBotDrawingTool.printImage()
		#_drawBotDrawingTool.saveImage("/Users/nic/Desktop/proof.pdf")

		_drawBotDrawingTool._drawInContext(context)
		pdfDocument = context.getNSPDFDocument()
		self.drawView.setPDFDocument(pdfDocument)

		if TIMING:
			post_render_proof = default_timer()
			print('[profile] time to compile: %.03f seconds' % (post_generate_proof - pre_generate_proof))
			print('[profile] time to render: %.03f seconds' % (post_render_proof - pre_render_proof))
			print('[profile] done.\n')
		print('Done.')
