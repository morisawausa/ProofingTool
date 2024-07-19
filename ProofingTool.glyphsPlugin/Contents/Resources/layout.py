# -*- coding: utf-8 -*-

from pstats import Stats

PROFILE = False
SPACE = 1000


class OCCProofingLayout(object):
	def __init__(self, glyphs, parameters, width, height, upm):
		self.width = width
		self.height = height
		# self.glyphs = list(filter(lambda g: g.name is not None, glyphs[0]))
		self.glyphs = glyphs[0]
		self.parameters = parameters

		# 0. Determine page constraints based on document size in inches.
		self.em_per_u = 1.0 / upm
		self.in_per_pt = 0.0138889
		self.px_per_in = width / parameters['document']['width']
		self.line_height_factor = 1.25
		self.line_padding = parameters['gaps']['line']
		self.block_padding = parameters['gaps']['block']
		self.block_glyph_index = 0
		self.pages = []

	def get_layer(self, glyph, style_name):
		interpolatedFont = self.parameters['exports'][style_name]
		if glyph in interpolatedFont.glyphs:
			interpolatedGlyph = interpolatedFont.glyphs[glyph]
			layer = interpolatedGlyph.layers[interpolatedFont.masters[0].id]
			return layer
		else:
			print(glyph, "does not exist in the instance")

	def get_scalefactor(self, pts_per_em):
		return self.em_per_u * \
			self.in_per_pt * \
			self.px_per_in * \
			pts_per_em

	def get(self):
		return self.pages


class OCCProofingParagraphLayout(OCCProofingLayout):
	def __init__(self, glyphs, parameters, width, height, upm):
		super(OCCProofingParagraphLayout, self).__init__(glyphs, parameters, width, height, upm)

		page_index = 0
		pages = [[]]

		# 1. determine which parameter group takes defines the shortest line.
		#    and define the block size.
		parameter_rows = list(enumerate(zip(parameters['instances'], parameters['point_sizes'])))
		# If we don't have any rendering criteria, we can't render. Fail early.

		if len(parameter_rows) == 0:
			self.pages = []
			return

		page_origin_x_px = parameters['gaps']['left']
		available_space_x_px = self.width - self.parameters['gaps']['right']
		page_origin_y_px = self.height - parameters['gaps']['top']

		block_advance_position_x_px = 0
		block_advance_position_y_px = 0

		for i, (style_name, point_size) in parameter_rows:
			master = self.parameters['exports'][style_name].masters[0]
			# each of these represents a paragraph.
			u_to_px = self.get_scalefactor(point_size)
			height_px = (master.ascender - master.descender) * u_to_px + self.line_padding

			block_advance_position_x_px = 0
			block_advance_position_y_px += height_px

			page_start_index = len(pages[page_index])
			# backtracked = False
			i = 0

			while i < len(self.glyphs):

				if page_origin_y_px - block_advance_position_y_px < self.parameters['gaps']['bottom']:
					# we've fallen off the end of the page, time to add another one.
					block_advance_position_y_px = height_px
					block_advance_position_x_px = 0

					pages.append([])

					if page_start_index > 0:  # if we have some unrelated glyphs on the previous page, shift em down
						page_previous_block = pages[page_index][:page_start_index]
						pages[page_index] = page_previous_block
						i = 0

					page_start_index = 0
					page_index += 1

				this_glyph = self.glyphs[i]
				glyph_name = this_glyph.name

				if (glyph_name == 'newGlyph'):
					# print('paragraph break')
					block_advance_position_y_px += height_px
					block_advance_position_x_px = 0
				else:
					layer = self.get_layer(glyph_name, style_name)
					orphan_layer = layer.copy()
					orphan_layer.parent = layer.parent
					width_px = (orphan_layer.width * u_to_px)

					# if this glyph would knock us over the end of the line,
					# reset the height and x position, and retry.
					if block_advance_position_x_px + width_px > available_space_x_px:
						block_advance_position_y_px += height_px
						block_advance_position_x_px = 0
						continue

					draw = {
						'path': orphan_layer,
						'scale': u_to_px,
						'x': page_origin_x_px + block_advance_position_x_px,
						'y': page_origin_y_px - block_advance_position_y_px
					}

					pages[page_index].append(draw)
					block_advance_position_x_px += width_px

				# apply a kerning transform here.
				# interpolatedFontProxy doesn't have kerning :c :c :c
				# if i < len(self.glyphs[0]) - 1:
				# 	next_glyph = self.glyphs[0][i + 1]
				# 	print(dir(master[1].font))
				# 	k = master[1].font.kerningForPair(master[1].id, glyph.rightKerningKey, next_glyph.leftKerningKey)
				# 	print(k)
				# 	print(k * u_to_px)
				# 	next_layer = self.get_layer(next_glyph, master[1])

				# next step. Check whether the width is too big for the and wrap the advance height.
				if block_advance_position_x_px > available_space_x_px:
					block_advance_position_y_px += height_px
					block_advance_position_x_px = 0

				i += 1

			block_advance_position_y_px += self.block_padding

		self.pages = pages


class OCCProofingWaterfallLayout(OCCProofingLayout):
	def __init__(self, glyphs, parameters, width, height, upm):
		super(OCCProofingWaterfallLayout, self).__init__(glyphs, parameters, width, height, upm)

		if PROFILE:
			import cProfile
			__profile = cProfile.Profile()
			__profile.enable()

		parameter_rows = list(enumerate(zip(parameters['instances'], parameters['point_sizes'])))
		# If we don't have any rendering criteria, we can't render. Fail early.
		if len(parameter_rows) == 0:
			self.pages = []
			return

		heights_per_line = list(map(self.get_line_heights, parameter_rows))

		self.block_line_heights = list(map(lambda a: int(a[1]), heights_per_line))
		self.block_line_origin = (self.block_line_heights[0] - self.line_padding) if len(self.block_line_heights) > 0 else 0
		self.block_height = sum(self.block_line_heights) + self.block_padding

		# 2. layout each block.
		pages = [[]]
		page_index = 0

		page_origin_x_px = parameters['gaps']['left']
		page_origin_y_px = self.height - parameters['gaps']['top']

		block_index = 0

		block_origin_x_px = page_origin_x_px
		block_origin_y_px = page_origin_y_px

		block_advance_position_x_px = 0
		block_advance_position_y_px = self.block_line_origin

		# NOTE: we need to properly select a length for the glyphset.
		# this should be done by normalizing the glyphs passed to layout
		# in the parameters file, perhaps supplying notdef or space
		# as a glyph when once glyph is present in one font, and not in the
		# other one.

		# Helper Methods for Profiling
		def select_second_element(a):
			return a[1]

		while len(self.glyphs[self.block_glyph_index:]) > 0:

			# If we have a block-size that fits onto a single page, check for when a block runs off the page,
			# and advance it to the next page.
			if block_origin_y_px - self.block_height < parameters['gaps']['bottom'] and self.block_glyph_index > 0:
				# This block overshoots the end of the page.
				# time to create a new page, and reset the block data.
				pages.append([])
				page_index += 1
				block_origin_y_px = page_origin_y_px
				block_advance_position_y_px = self.block_line_origin

			# we need to know what the line offset is, so that we can shift to
			# the next page, if we need to.

			# First, get the line-length for this line
			bounds_per_line = list(map(self.get_line_lengths, parameter_rows))
			block_line_length = min(list(map(select_second_element, bounds_per_line)))

			# Then layout the line with this length
			block_glyphs = list(self.glyphs[self.block_glyph_index: self.block_glyph_index + block_line_length])

			for i, (style_name, point_size) in parameter_rows:
				# print('master = %d' % (i + 1))
				# print('page = %d' % (page_index + 1))
				# print('origin = %d\n' % (block_origin_y_px - block_advance_position_y_px))

				# Layout the current line.
				u_to_px = self.get_scalefactor(point_size)

				for glyph in block_glyphs:
					glyph_name = glyph.name
					if glyph_name != 'newGlyph':
						layer = self.get_layer(glyph.name, style_name)
						orphan_layer = layer.copy()
						orphan_layer.parent = layer.parent
						# print(orphan_layer)
						draw = {
							'path': orphan_layer,
							'scale': u_to_px,
							'x': block_origin_x_px + block_advance_position_x_px,
							'y': block_origin_y_px - block_advance_position_y_px
						}
						pages[page_index].append(draw)
						block_advance_position_x_px += (orphan_layer.width * u_to_px)

				block_advance_position_y_px += self.block_line_heights[i + 1] if len(self.block_line_heights) > i + 1 else 0
				block_advance_position_x_px = 0

				# I need something here to advance the page pointer.
				if block_origin_y_px - block_advance_position_y_px <= parameters['gaps']['bottom']:
					pages.append([])
					page_index += 1
					block_origin_y_px = page_origin_y_px
					block_advance_position_y_px = self.block_line_origin

			# Dec/Increment parameters for the next block
			block_advance_position_y_px = self.block_line_origin
			self.block_glyph_index += block_line_length
			block_origin_y_px -= self.block_height
			block_index += 1

		self.pages = pages

		if PROFILE:
			__profile.disable()
			__stats = Stats(__profile)
			__stats.sort_stats('cumulative').print_stats()

	def get_line_heights(self, data):
		line_index, (style_name, point_size) = data
		u_to_px = self.get_scalefactor(point_size)
		master = self.parameters['exports'][style_name].masters[0]
		# GSinterpolatedFont outputs only one master and one instance.
		height_px = (master.ascender - master.descender) * u_to_px + self.line_padding

		return line_index, height_px

	def get_line_lengths(self, data):
		# line_index, ((font_index, style_name), point_size) = data
		line_index, (style_name, point_size) = data

		u_to_px = self.get_scalefactor(point_size)
		advance_px = self.parameters['gaps']['left']
		glyph_count = 0
		available_space_px = self.width - self.parameters['gaps']['right']

		while advance_px < available_space_px and self.block_glyph_index + glyph_count < len(self.glyphs):
			this_glyph = self.glyphs[self.block_glyph_index + glyph_count]
			glyph_name = this_glyph.name

			if glyph_name == 'newGlyph':
				width_px = 0
				advance_px = available_space_px
			else:
				layer = self.get_layer(glyph_name, style_name)
				width_px = layer.width * u_to_px
			advance_px += width_px
			glyph_count += 1

		line_length = glyph_count - 1 if advance_px > available_space_px else glyph_count

		return line_index, line_length


PROOFING_LAYOUTS = {
	'paragraph': OCCProofingParagraphLayout,
	'waterfall': OCCProofingWaterfallLayout
}
