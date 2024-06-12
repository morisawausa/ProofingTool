import os
import json
from GlyphsApp import *

class OCCTemplatePreferences( ):
	def __init__(self):
		self.templatePaths = []
		self.loadPreferences()

	def loadPreferences( self ):
		Glyphs.registerDefault("com.OCC.ProofingTool.templatefiles", ['demo.json'])
		try:
			self.templatePaths = Glyphs.defaults["com.OCC.ProofingTool.templatefiles"]
			if len(self.templatePaths) < 1:
				print( 'Loading demo template, which may not match your instances. Please review and edit the template for your font.' )
				self.templatePaths = ['demo.json']
		except:
			return False
		return True

	def savePreferences( self, files ):
		Glyphs.defaults["com.OCC.ProofingTool.templatefiles"] = files
		return True