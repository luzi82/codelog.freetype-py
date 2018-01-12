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

def create_text(text, font_face):

    #face = Face(os.path.join('font_set','Vera.ttf'))
    #face.set_char_size( 48*64 )
    face = font_face
    #text = 'Hello World !'
    slot = face.glyph

    # First pass to compute bbox
    width, height, baseline = 0, 0, 0
    previous = 0
    for i,c in enumerate(text):
        face.load_char(c)
        bitmap = slot.bitmap
        height = max(height,
                     bitmap.rows + max(0,-(slot.bitmap_top-bitmap.rows)))
        baseline = max(baseline, max(0,-(slot.bitmap_top-bitmap.rows)))
        kerning = face.get_kerning(previous, c)
        width += (slot.advance.x >> 6) + (kerning.x >> 6)
        previous = c

    Z = np.zeros((height,width), dtype=np.ubyte)

    # Second pass for actual rendering
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
    
    Z = create_text('Hello World !', face)

    plt.figure(figsize=(10, 10*Z.shape[0]/float(Z.shape[1])))
    plt.imshow(Z, interpolation='nearest', origin='upper', cmap=plt.cm.gray)
    plt.xticks([]), plt.yticks([])
    plt.show()
