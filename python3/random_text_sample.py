import freetype
import os
import numpy as np
import matplotlib.pyplot as plt
import string

CREATE_FONT_INFO_TEXT_USED_DEFAULT = string.ascii_lowercase + string.ascii_uppercase + string.digits

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

def create_text(text, font_info, fill=True, stroke=False, stroke_radius=0):

    face = font_info['font_face']
    height = font_info['height']
    baseline = font_info['baseline']
    height += stroke_radius*2

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

    width  += stroke_radius*2
    Z = np.zeros((height,width), dtype=np.int)

    # Second pass for actual rendering
    if fill:
        x, y = stroke_radius, 0
        previous = 0
        for c in text:
            face.load_char(c)
            bitmap = slot.bitmap
            top = slot.bitmap_top
            #left = slot.bitmap_left
            w,h = bitmap.width, bitmap.rows
            y = height-baseline-top-stroke_radius
            kerning = face.get_kerning(previous, c)
            x += (kerning.x >> 6)
            #print((c,x,y,w,h))
            Z[y:y+h,x:x+w] += np.array(bitmap.buffer, dtype='ubyte').reshape(h,w)
            x += (slot.advance.x >> 6)
            previous = c
    
    if stroke:

        x, y = 0, 0
        previous = 0
        for c in text:
            face.load_char(c, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
            slot = face.glyph
            glyph = slot.get_glyph()
            stroker = freetype.Stroker( )
            stroker.set(64*stroke_radius, freetype.FT_STROKER_LINECAP_ROUND, freetype.FT_STROKER_LINEJOIN_ROUND, 0 )
            glyph.stroke( stroker , True )
            blyph = glyph.to_bitmap(freetype.FT_RENDER_MODE_NORMAL, freetype.Vector(0,0), True )
            bitmap = blyph.bitmap

            #top = slot.bitmap_top
            #left = slot.bitmap_left
            #print(blyph.top)
            top = blyph.top
            w,h = bitmap.width, bitmap.rows
            y = height-baseline-top-stroke_radius
            kerning = face.get_kerning(previous, c)
            x += (kerning.x >> 6)
            #print((c,x,y,w,h))
            Z[y:y+h,x:x+w] += np.array(bitmap.buffer, dtype='ubyte').reshape(h,w)
            x += (slot.advance.x >> 6)
            previous = c
    
    Z = np.minimum(Z,255)
    
    return Z

if __name__ == '__main__':

    char_set = CREATE_FONT_INFO_TEXT_USED_DEFAULT

    face = freetype.Face(os.path.join('font_set','Vera.ttf'))
    face.set_char_size( 48*64 )
    font_info = create_font_info(face)
    height_max = font_info['height']

    for _ in range(100):
        text_len = random.randint(1,20)
        text = ''.join(random.choice(char_set) for _ in range(text_len))
        font_size = random.randint(36*64,48*64)
        draw_type = random.choice(['FILL', 'STROKE_DOWN', 'STROKE_UP'])
        if draw_type=='FILL':
            stroke_radius = 0
        else:
            stroke_radius = random.randint(1,4)
        if draw_type=='FILL':
            bg_color = np.random.rand(3)
            while True:
                fill_color = np.random.rand(3)
                diff = np.sum(np.absolute(fill_color-bg_color))
                if diff > 0.25:
                    break
        else:
            bg_color = np.random.rand(3)
            stroke_color = np.random.rand(3)
            while True:
                fill_color = np.random.rand(3)
                diff = np.sum(np.absolute(fill_color-stroke_color))
                if diff > 0.25:
                    break

        font_info = create_font_info(face)
        fill_z = create_text(text, font_info, fill=True, stroke=False, stroke_radius=stroke_radius)
        if draw_type!='FILL':
            stroke_z = create_text(text, font_info, fill=False, stroke=True, stroke_radius=stroke_radius)

        // blah...
