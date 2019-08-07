#!/usr/bin/env python3

import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
gi.require_version('Pango', '1.0')
from gi.repository import Pango
gi.require_version('PangoCairo', '1.0')
from gi.repository import PangoCairo
import cairo
import math

POINTS_PER_MM = 2.8346457

PAGE_WIDTH = 210
PAGE_HEIGHT = 297

# The margin from the edge of the page to the start of the cards
MARGIN = 15
# The margin inside the card for the text
INNER_MARGIN = 2.5

N_COLUMNS = 4
N_ROWS = 5
CARDS_PER_PAGE = N_COLUMNS * N_ROWS

CARD_WIDTH = (PAGE_WIDTH - MARGIN * 2) / N_COLUMNS
CARD_HEIGHT = (PAGE_HEIGHT - MARGIN * 2) / N_ROWS

def start_page(cr):
    for i in range(N_COLUMNS + 1):
        cr.move_to(i * CARD_WIDTH + MARGIN, MARGIN)
        cr.rel_line_to(0, PAGE_HEIGHT - MARGIN * 2)
    for i in range(N_ROWS + 1):
        cr.move_to(MARGIN, i * CARD_HEIGHT + MARGIN)
        cr.rel_line_to(PAGE_WIDTH - MARGIN * 2, 0)

    cr.stroke()

def render_paragraph(cr, x, y, width, height, text):
    font_size = 12

    while True:
        layout = PangoCairo.create_layout(cr)
        fd = Pango.FontDescription.from_string("Sans {}".format(font_size))
        layout.set_font_description(fd)
        layout.set_width(width * POINTS_PER_MM * Pango.SCALE)
        layout.set_text(text, -1)

        (ink_rect, logical_rect) = layout.get_pixel_extents()

        if (ink_rect.height / POINTS_PER_MM <= height and
            ink_rect.width / POINTS_PER_MM) <= width:
            break

        font_size *= 0.75

    cr.save()

    cr.move_to(x, y)

    # Remove the mm scale
    cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)

    PangoCairo.show_layout(cr, layout)

    cr.restore()

    return logical_rect.height / POINTS_PER_MM

def draw_card(cr, x, y, text, logo):
    logo_dim = logo.get_dimensions()
    logo_scale = (CARD_WIDTH - INNER_MARGIN * 2) / logo_dim.width

    cr.save()
    cr.translate(MARGIN + x * CARD_WIDTH + INNER_MARGIN,
                 MARGIN + (y + 1) * CARD_HEIGHT -
                 logo_dim.height * logo_scale -
                 INNER_MARGIN)
    cr.scale(logo_scale, logo_scale)
    logo.render_cairo(cr)
    cr.restore()

    paragraph_height = (CARD_HEIGHT -
                        INNER_MARGIN * 2 -
                        logo_dim.height * logo_scale)

    render_paragraph(cr,
                     MARGIN + x * CARD_WIDTH + INNER_MARGIN,
                     MARGIN + y * CARD_HEIGHT + INNER_MARGIN,
                     CARD_WIDTH - INNER_MARGIN * 2,
                     paragraph_height,
                     text)

def render_file(cr, filename, logo_file):
    logo = Rsvg.Handle.new_from_file(logo_file)

    with open(filename, 'rt') as f:
        card_num = 0

        for line in f:
            line = line.strip()
            if line.startswith('#') or len(line) <= 0:
                continue

            in_page = card_num % CARDS_PER_PAGE

            if in_page == 0:
                start_page(cr)

            draw_card(cr,
                      in_page % N_COLUMNS,
                      in_page // N_COLUMNS,
                      line,
                      logo)

            card_num += 1

            if card_num % CARDS_PER_PAGE == 0:
                cr.show_page()

        if card_num % CARDS_PER_PAGE != 0:
            cr.show_page()

surface = cairo.PDFSurface("superbatalo.pdf",
                           PAGE_WIDTH * POINTS_PER_MM,
                           PAGE_HEIGHT * POINTS_PER_MM)

cr = cairo.Context(surface)

# Use mm for the units from now on
cr.scale(POINTS_PER_MM, POINTS_PER_MM)

# Use ½mm line width
cr.set_line_width(0.5)

render_file(cr, "roloj.txt", "logo.svg")
render_file(cr, "konkursoj.txt", "logo.svg")
render_file(cr, "povoj.txt", "logo.svg")
