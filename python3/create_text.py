#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
#  FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
#
# -----------------------------------------------------------------------------
import freetype
import os
import numpy as np
import matplotlib.pyplot as plt
import string

CREATE_FONT_INFO_TEXT_USED_DEFAULT = string.ascii_lowercase + string.ascii_uppercase + string.digits
#CREATE_FONT_INFO_TEXT_USED_DEFAULT = 'ABCDEFGHIJKLMNOPRSTUVWXYZ' + string.digits

def create_font_info(font_face, text_used=CREATE_FONT_INFO_TEXT_USED_DEFAULT):
    face = font_face
    slot = face.glyph

    up_max = 0
    down_max = 0
    for c in text_used:
        face.load_char(c)
        bitmap = slot.bitmap
        up = max(0,slot.bitmap_top)
        down = max(0,bitmap.rows - slot.bitmap_top)
        up_max = max(up_max, up)
        down_max = max(down_max, down)
    
    return {
        'font_face':    font_face,
        'height':       up_max+down_max,
        'baseline':     down_max,
    }

def create_text(text, font_info, fill=True, stroke=False):

    face = font_info['font_face']
    height = font_info['height']
    baseline = font_info['baseline']

    slot = face.glyph

    # First pass to compute bbox
    width = 0
    previous = 0
    for c in text:
        face.load_char(c)
        bitmap = slot.bitmap
        kerning = face.get_kerning(previous, c)
        width += (slot.advance.x >> 6) + (kerning.x >> 6)
        previous = c

    Z = np.zeros((height,width), dtype=np.ubyte)

    # Second pass for actual rendering
    if fill:
        x, y = 0, 0
        previous = 0
        for c in text:
            face.load_char(c)
            bitmap = slot.bitmap
            top = slot.bitmap_top
            left = slot.bitmap_left
            w,h = bitmap.width, bitmap.rows
            y = height-baseline-top
            kerning = face.get_kerning(previous, c)
            x += (kerning.x >> 6)
            Z[y:y+h,x:x+w] += np.array(bitmap.buffer, dtype='ubyte').reshape(h,w)
            x += (slot.advance.x >> 6)
            previous = c
        
    return Z

if __name__ == '__main__':

    face = freetype.Face(os.path.join('font_set','Vera.ttf'))
    face.set_char_size( 48*64 )
    
    font_info = create_font_info(face,CREATE_FONT_INFO_TEXT_USED_DEFAULT+'!')
    Z = create_text('Hello World !', font_info)

    plt.figure(figsize=(10, 10*Z.shape[0]/float(Z.shape[1])))
    plt.imshow(Z, interpolation='nearest', origin='upper', cmap=plt.cm.gray)
    plt.xticks([]), plt.yticks([])
    plt.show()
