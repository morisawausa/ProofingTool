import os
import json
from GlyphsApp import *

class OCCTemplatePreferences( ):
	def __init__(self):
		self.templatePaths = []
		self.loadPreferences()

	def loadPreferences( self ):
		Glyphs.registerDefault("com.OCC.ProofingTool.templatefiles", [])
		try:
			self.templatePaths = Glyphs.defaults["com.OCC.ProofingTool.templatefiles"]
			if len(self.templatePaths) < 1:
				print( 'It looks like there aren’t previous templates to load. Please create a new template in the Edit tab or load a template file for your font.' )
				self.templatePaths = []
		except:
			return False
		return True

	def savePreferences( self, files ):
		Glyphs.defaults["com.OCC.ProofingTool.templatefiles"] = files
		return True