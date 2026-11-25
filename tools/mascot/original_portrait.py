"""Lift, register and animate the café's original standing head for the running art."""
from PIL import Image, ImageDraw
import math
import numpy as np
from scipy import ndimage
NAVY = (26/255, 35/255, 77/255)

def prepared_ink(image):
    a = np.asarray(image.convert('RGBA')).astype(float)
    # A transparency-aware ink density also discards the sheet's white sticker edge.
    return np.clip((255-a[:,:,0])/(255-NAVY[0]*255), 0, 1)*a[:,:,3]/255


def cutout(ink):
    hard = ndimage.binary_fill_holes(ndimage.binary_closing(ink > .17, iterations=1))
    # Keep just the character. The source sheet includes stray specks outside its ink.
    components, _ = ndimage.label(hard)
    sizes = np.bincount(components.ravel())
    main = components == 1 + np.argmax(sizes[1:])
    alpha = np.maximum(main.astype(float), ink*ndimage.binary_dilation(main,iterations=2))
    rgb = np.stack([255-(255-255*v)*ink for v in NAVY], axis=-1)
    return Image.fromarray(np.uint8(np.dstack([rgb, 255*alpha]).clip(0,255)))


def extract_head(sheet):
    stand = sheet.crop((1200,260,1540,710))
    ink = prepared_ink(stand)
    ink[249:] = 0
    # Restore the short underside of the muzzle where the standing body met its head.
    chin = Image.new('L', stand.size)
    draw = ImageDraw.Draw(chin)
    draw.line([(129,247),(143,248),(156,250),(175,250),(192,248),(208,246)], fill=255,width=4)
    head = cutout(np.maximum(ink, np.asarray(chin)/255)).crop((50,45,296,263))
    return head


def lobe(x, y, cx, cy, rx, ry):
    return np.exp(-((x-cx)/rx)**2 - ((y-cy)/ry)**2)


def deform(image, dx, dy):
    arr = np.asarray(image)
    yy, xx = np.indices(arr.shape[:2], dtype=np.float32)
    coordinates = [yy-dy,xx-dx]
    # The RGBA layer is white and ink, exterior geometry lives in the alpha plane.
    channels = [ndimage.map_coordinates(arr[:,:,j],coordinates,order=1,mode='constant',
                                           cval=(0 if j == 3 else 255)) for j in range(4)]
    return Image.fromarray(np.stack(channels,axis=-1))


def swaying_head(base, t, energy, blink):
    yy,xx = np.indices((base.height,base.width), dtype=np.float32)
    ears = lobe(xx,yy,26,176,33,48) + lobe(xx,yy,216,175,36,47)
    hat = lobe(xx,yy,135,27,38,33)
    dx = ears*(2.7*math.cos(t))*energy + hat*(1.3*math.sin(t))*energy
    dy = ears*(4.2*math.sin(t-.9))*energy - hat*(1.2*math.cos(t))*energy
    out = deform(base, dx, dy)
    if blink > .04:
        for l,r,cy in ((81,106,118),(133,162,121)):
            eye = out.crop((l,cy-17,r,cy+17))
            # Erase the ink in the existing eyelid bounds before closing either eye.
            ImageDraw.Draw(out).rectangle((l,cy-17,r-1,cy+16), fill='white')
            h = max(3,round(34*(1-blink)))
            out.paste(eye.resize((r-l,h), Image.Resampling.LANCZOS),(l,cy-h//2))
    return out


