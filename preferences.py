import os
import json
from GlyphsApp import *

class OCCTemplatePreferences( ):
	def __init__(self):
		self.templatePaths = []
		self.loadPreferences()

	def loadPreferences( self ):
		Glyphs.registerDefault("com.motsuka.OCCProofingTool.templatefiles", ['data/demo.json'])
		try:
			# self.templatePaths = ['data/demo.json']
			self.templatePaths = Glyphs.defaults["com.motsuka.OCCProofingTool.templatefiles"]
		except:
			return False
		return True

	def savePreferences( self, files ):
		Glyphs.defaults["com.motsuka.OCCProofingTool.templatefiles"] = files
		return True