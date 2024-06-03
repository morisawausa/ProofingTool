#MenuTitle: Proofing Tool
# -*- coding: utf-8 -*-
__doc__="""
Opens the Proofing Window for the active Glyphs file.
"""

from GlyphsApp import *
import traceback

from proofing import OCCProofingTool

class ProofingTool():

	def __init__(self):
		Glyphs.showMacroWindow()
		if Glyphs.font:
			print("\n🙌 Welcome to the Proofing Tool 🙌\n\n")
			self.application = OCCProofingTool()
		else:
			print("There are no fonts open yet 😥 Please open a file and run the tool again.")

if __name__ == '__main__':
	tool = ProofingTool()