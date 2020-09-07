# -*- coding: utf-8 -*-

from math import ceil

class OCCProofingLayout:
    def __init__(self, glyphs, parameters, width, height, upm):
        self.width = width
        self.height = height
        self.glyphs = glyphs
        self.parameters = parameters

        # 0. Determine page constraints based on document size in inches.
        self.em_per_u = 1.0 / upm
        self.in_per_pt = 0.0138889
        self.px_per_in = width / parameters['document']['width']
        self.line_height_factor = 1.25
        self.line_padding = 20

        # 1. determine which parameter group takes defines the shortest line.
        #    and define the block size.
        self.block_glyph_index = 0

        parameter_rows = list(enumerate(zip(parameters['masters'], parameters['point_sizes'])))
        heights_per_line = map(self.get_line_heights, parameter_rows)

        self.block_line_heights = map(lambda a: int(a[1]), heights_per_line)
        self.block_line_origin = (self.block_line_heights[0] - self.line_padding) if len(self.block_line_heights) > 0 else 0
        self.block_height = sum(self.block_line_heights)

        # print('block_line_height: %s px' % self.block_line_height)
        # print('block_total_height: %s px' % self.block_height)

        # 2. layout each block.
        pages = [[]]

        page_index = 0
        page_origin_x_px = parameters['padding']['left']
        page_origin_y_px = self.height - parameters['padding']['top']

        block_index = 0
        # block_line_glyph_index = 0

        block_origin_x_px = page_origin_x_px
        block_origin_y_px = page_origin_y_px

        block_advance_position_x_px = 0
        block_advance_position_y_px = self.block_line_origin

        # print(map(lambda a: a.name, self.glyphs))

        while len(self.glyphs[self.block_glyph_index:]) > 0:
            # print('new block: %s' % block_index)
            # print('page height: %s' % self.height)
            # print('block line_heights', self.block_line_heights)
            # print('block height: %s' % self.block_height)
            # print('block_origin y: %s' % block_origin_y_px)

            if block_origin_y_px - self.block_height < parameters['padding']['bottom']:
                # This block overshoots the end of the page.
                # time to create a new page, and reset the block data.
                pages.append([])
                page_index += 1
                block_origin_y_px = page_origin_y_px
                block_advance_position_y_px = self.block_line_origin



            # First, get the line-length for this line
            bounds_per_line = map(self.get_line_lengths, parameter_rows)
            block_line_length = min(map(lambda a: a[1], bounds_per_line))

            # block_line_length = 2


            # Then layout the line with this length
            block_glyphs = self.glyphs[ self.block_glyph_index : self.block_glyph_index + block_line_length ]

            for i, (master, point_size) in parameter_rows:
                # Layout the current line.
                u_to_px = self.get_scalefactor(point_size)
                for glyph in block_glyphs:
                    orphan_layer = glyph.layers[master.id].copyDecomposedLayer()
                    transform = (
                        u_to_px, # x-axis scale factor,
                        0.0, # y-axis skew factor,
                        0.0, # x-axis skew factor,
                        u_to_px, # y-axis scale factor,
                        block_origin_x_px + block_advance_position_x_px, # x-axis translation
                        block_origin_y_px - block_advance_position_y_px  # y-axis translation
                    )
                    orphan_layer.applyTransform(transform)
                    pages[page_index].append(orphan_layer)
                    block_advance_position_x_px += round(orphan_layer.width * u_to_px)

                block_advance_position_y_px += self.block_line_heights[i + 1] if len(self.block_line_heights) > i + 1 else 0
                block_advance_position_x_px = 0


            # Dec/Increment parameters for the next block
            block_advance_position_y_px = self.block_line_origin
            self.block_glyph_index += block_line_length
            block_origin_y_px -= self.block_height
            block_index += 1

        self.pages = pages


    def get_scalefactor(self, pts_per_em):
        return self.em_per_u * \
            self.in_per_pt * \
            self.px_per_in * \
            pts_per_em


    def get_line_heights(self, (line_index, (master, point_size))):
        u_to_px = self.get_scalefactor(point_size)
        height_px = (master.ascender - master.descender) * u_to_px + self.line_padding

        return line_index, height_px


    def get_line_lengths(self, (line_index, (master, point_size))):

        u_to_px = self.get_scalefactor(point_size)
        advance_px = self.parameters['padding']['left']
        glyph_count = 0

        # print('')
        # print('starting glyph index: %s' % self.block_glyph_index)


        while advance_px < (self.width - self.parameters['padding']['right']) and self.block_glyph_index + glyph_count < len(self.glyphs):
            glyph = self.glyphs[self.block_glyph_index + glyph_count]
            layer = glyph.layers[master.id]
            width_px = layer.width * u_to_px
            # print('current advance_px: %s' % advance_px)
            # print('first_glyph_name: %s' % glyph.name)
            # print('first_layer_name: %s' % layer.name)
            # print('first_layer_width: %s' % round(width_px))
            advance_px += width_px
            glyph_count += 1

        # print('final glyph_count: %s' % glyph_count)
        return line_index, glyph_count

        #
        # print('document width: %s' % (self.width - self.parameters['padding']['right']))
        # print('\n')
        #
        # while advance_px < self.width - self.parameters['padding']['right'] and glyph_index < len(self.glyphs):
        #     main_layer = self.glyphs[glyph_index].layers[master.id]
        #     advance_px += main_layer.width * u_to_px
        #     glyph_index += 1
        #     glyph_count += 1
        #
        #     print('iteration %s:' % glyph_count)
        #     print('advance_px %s:' % advance_px)
        #     print('glyph_index_in_set %s:' % glyph_index)
        #     print('\n')
        #
        # return line_index, glyph_count - 1


    def get(self):
        return self.pages
