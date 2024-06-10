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
			self.templatePaths = Glyphs.defaults["com.motsuka.OCCProofingTool.templatefiles"]
			if len(self.templatePaths) < 1:
				print( 'Loading demo template, which may not match your instances. Please review and edit the template for your font.' )
				self.templatePaths = ['data/demo.json']
		except:
			return False
		return True

	def savePreferences( self, files ):
		Glyphs.defaults["com.motsuka.OCCProofingTool.templatefiles"] = files
		return True