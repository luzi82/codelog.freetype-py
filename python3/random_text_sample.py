import freetype
import os
import numpy as np
#import matplotlib.pyplot as plt
import string
import shutil
import random
import cv2

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
    width2 = 0
    previous = 0
    for c in text:
        face.load_char(c)
        bitmap = slot.bitmap
        kerning = face.get_kerning(previous, c)
        width2 = width + bitmap.width + (kerning.x >> 6)
        width += (slot.advance.x >> 6) + (kerning.x >> 6)
        previous = c

    width = max(width,width2)
    width += 1

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

def get_width(text, font_info, fill=True, stroke=False, stroke_radius=0):

    face = font_info['font_face']
    height = font_info['height']
    baseline = font_info['baseline']

    slot = face.glyph

    width = 0
    previous = 0
    for c in text:
        face.load_char(c)
        bitmap = slot.bitmap
        kerning = face.get_kerning(previous, c)
        width += (slot.advance.x >> 6) + (kerning.x >> 6)
        previous = c

    width  += stroke_radius*2
    
    return width

def draw(dest_hwc, src_c, z_hw):
    assert(dest_hwc.shape[0] == z_hw.shape[0])
    assert(dest_hwc.shape[1] == z_hw.shape[1])
    assert(dest_hwc.shape[2] == 3)
    assert(src_c.shape[0] == 3)
    
    h = dest_hwc.shape[0]
    w = dest_hwc.shape[1]
    c = 3

    z_chw = np.reshape(z_hw,(1,h,w))
    z_chw = np.repeat(z_chw,c,axis=0)
    z_hwc = np.transpose(z_chw,(1,2,0))

    dz255_hwc = dest_hwc * (255-z_hwc)
    
    src_hwc = np.reshape(src_c,(1,1,c))
    src_hwc = np.repeat(src_hwc,w,axis=1)
    src_hwc = np.repeat(src_hwc,h,axis=0)
    
    sz255_hwc = src_hwc * z_hwc
    
    dest_hwc[:,:,:] = (dz255_hwc+sz255_hwc)/255

def reset_dir(out_dir):
    shutil.rmtree(out_dir,ignore_errors=True)
    os.makedirs(out_dir)

if __name__ == '__main__':

    CHAR_SET = CREATE_FONT_INFO_TEXT_USED_DEFAULT
    CHAR_COUNT_MAX = 10
    OUT_PATH = 'output'
    STROKE_RADIUS_MIN = 1
    STROKE_RADIUS_MAX = 4

    reset_dir(OUT_PATH)

    face = freetype.Face(os.path.join('font_set','Vera.ttf'))
    face.set_char_size( 48*64 )
    font_info = create_font_info(face,text_used=CHAR_SET)
    inner_height_max = font_info['height']
    print('inner_height_max = {}'.format(inner_height_max))

    #inner_width_max = max([get_width(c*CHAR_COUNT_MAX,font_info) for c in CHAR_SET])

    for _ in range(100):
        text_len = random.randint(1,CHAR_COUNT_MAX)
        text = ''.join(random.choice(CHAR_SET) for _ in range(text_len))
        font_size = random.randint(24*64,48*64)
        draw_type = random.choice(['FILL', 'STROKE_DOWN', 'STROKE_UP'])
        noise = random.random()
        if draw_type=='FILL':
            stroke_radius = 0
        else:
            stroke_radius = random.randint(STROKE_RADIUS_MIN,STROKE_RADIUS_MAX)
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

        print('text={}, font_size={}, stroke_radius={}',text,font_size,stroke_radius)

        face.set_char_size( font_size )
        font_info = create_font_info(face,text_used=CHAR_SET)
        fill_z = create_text(text, font_info, fill=True, stroke=False, stroke_radius=stroke_radius)
        if draw_type!='FILL':
            stroke_z = create_text(text, font_info, fill=False, stroke=True, stroke_radius=stroke_radius)

        height = inner_height_max + stroke_radius*2
        width  = fill_z.shape[1]
        zh = fill_z.shape[0]
        y_freedom = height-zh
        assert(y_freedom>=0)
        y_offset = random.randint(0,y_freedom)
        
        img_hwc = bg_color.reshape((1,1,3))
        img_hwc = np.repeat(img_hwc,width,axis=1)
        img_hwc = np.repeat(img_hwc,height,axis=0)
        
        img_hwc = img_hwc + (np.random.rand(height,width,3)*noise)
        
        if draw_type == 'STROKE_DOWN':
            draw(img_hwc[y_offset:y_offset+zh,:,:], stroke_color, stroke_z)
        draw(img_hwc[y_offset:y_offset+zh,:,:], fill_color, fill_z)
        if draw_type == 'STROKE_UP':
            draw(img_hwc[y_offset:y_offset+zh,:,:], stroke_color, stroke_z)
        
        img_hwc = img_hwc*255
        img_hwc = np.floor(img_hwc)
        img_hwc = np.minimum(img_hwc,255)
        img_hwc = np.maximum(img_hwc,0)
        print(np.max(img_hwc))
        
        output_fn = os.path.join(OUT_PATH,'{}.png'.format(text))
        cv2.imwrite(output_fn,img_hwc)
        