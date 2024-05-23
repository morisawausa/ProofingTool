import os
import json
from GlyphsApp import *

class OCCTemplatePreferences( ):
	def __init__(self):
		self.rootFolder = 'data'

	def getDirectoryPath( self ):
		self.loadPreferences( )
		return self.rootFolder

	def setDirectoryPath( self, path ):		
		self.rootFolder = path
		self.savePreferences()

	def savePreferences( self ):
		Glyphs.defaults["com.motsuka.OCCProofingTool.directory"] = self.rootFolder
		return True

	def loadPreferences( self ):
		Glyphs.registerDefault("com.motsuka.OCCProofingTool.directory", 'data')
		try:
			self.rootFolder = Glyphs.defaults["com.motsuka.OCCProofingTool.directory"]
		except:
			return False
		return True