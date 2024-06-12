# encoding: utf-8

###########################################################################################################
#
#
#	Proofing Tool Plugin
#
#	Read the docs:
#	https://github.com/morisawausa/ProofingTool
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

from proofing import OCCProofingTool

class ProofingTool(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = 'Proofing Tool'
		self.proofer = None

	@objc.python_method
	def start(self):
		newMenuItem = NSMenuItem(self.name, self.showWindow_)
		Glyphs.menu[FILE_MENU].append(newMenuItem)

	def showWindow_(self, sender):
		"""Do something like show a window """
		Glyphs.showMacroWindow()
		if Glyphs.font:
			print("\n❇️ Welcome to the Proofing Tool \n")
			if Glyphs.font.instances:
				if not self.proofer or not self.proofer.mainWindow._window:
					self.proofer = OCCProofingTool()
				else:
					self.proofer.mainWindow.show()
			else:
				print("There are no exports set up yet 😥 Please define at least one instance and run the tool again.")
		else:
			print("There isn’t a font open yet 😥 Please open a file and run the tool again.")


	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
