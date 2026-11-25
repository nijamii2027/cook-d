"""Build the pan offer from the three rigid pieces of the original café drawing.

The two shoulder pivots, two paws and the pan form a four-bar linkage. No
deformation is applied to the pan, arms, printed face, apron, legs or tail.
Run this file with Pillow, NumPy and SciPy from any working directory.
"""
from pathlib import Path
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import ink_actions as ink


SOURCE = ink.art('stand')
W, H = SOURCE.size
SCALE = 3
NAVY = (25, 35, 75, 255)
WHITE = (255, 255, 255, 255)
LS = np.array([120., 248.])
RS = np.array([223., 248.])
LH = np.array([104., 298.])
RH = np.array([202., 295.])


def mask_for(rows):
    """Trace the source contour by horizontal edge coordinates."""
    left = [(x, y) for y, x, _ in rows]
    right = [(x, y) for y, _, x in rows[::-1]]
    m = Image.new('L', (W * SCALE, H * SCALE))
    ImageDraw.Draw(m).polygon([(round(x*SCALE), round(y*SCALE)) for x, y in left+right], fill=255)
    return m.resize((W,H), Image.Resampling.LANCZOS)


def clipped(image, mask):
    out = image.copy()
    a = np.array(image.getchannel('A'), dtype=float)*np.asarray(mask)/255
    out.putalpha(Image.fromarray(np.rint(a).astype('uint8')))
    return out


def layer(rows):
    return clipped(SOURCE, mask_for(rows))


# Coordinates are in the illustrator's high-resolution printed sticker, before
# the final 256px crop. Each piece carries its own original irregular pen edge.
BACK = layer([
    (246,119,123),(251,117,122),(258,111,123),(265,105,124),(272,100,125),
    (280,92,121),(288,88,118),(294,86,115),(298,86,112),(302,91,107)])
FRONT = layer([
    (244,221,236),(248,219,238),(254,216,243),(262,210,244),(270,205,244),
    (274,201,241),(278,196,235),(282,193,232),(286,192,228),(290,192,223),
    (294,193,221),(298,196,217),(301,200,207)])
PAN = layer([
    (286,145,161),(288,133,165),(289,126,196),(292,115,197),
    (295,108,199),(298,104,202),(301,101,198),(304,101,188),
    (307,101,183),(312,101,182),(316,102,177),(321,105,171),
    (324,107,163),(327,110,152),(328,113,141)])


def bezier(start, *segments):
    points = [start]
    for a, b, c in segments:
        p = np.array(points[-1])
        for u in np.linspace(0, 1, 18)[1:]:
            points.append(tuple(p*(1-u)**3 + 3*np.array(a)*u*(1-u)**2 +
                                3*np.array(b)*u*u*(1-u) + np.array(c)*u**3))
    return points


def drawing_points(path):
    return [(round(x*SCALE), round(y*SCALE)) for x,y in path]


def white_keyline(alpha, radius=14.0):
    # The original pasted sticker has a white keyline outside its ink silhouette.
    distance = ndimage.distance_transform_edt(np.asarray(alpha) < 128)
    cover = np.clip(radius + .5 - distance, 0, 1)
    result = Image.new('RGBA', (W,H), WHITE)
    result.putalpha(Image.fromarray(np.uint8(cover*255)))
    return result


def fixed_body():
    # This is the apron backing that was occluded by the frying pan. Restrict
    # reconstruction to the original prop/arm area. The torso surrounding it is
    # sampled directly from the source; every frame uses this same backing.
    body = Image.new('RGBA',(W*SCALE,H*SCALE))
    d = ImageDraw.Draw(body)
    path = bezier((120,245),
        ((119,257),(118,262),(117,269)), ((116,281),(111,291),(110,301)),
        ((109,310),(109,318),(111,327)), ((110,336),(110,342),(110,348)),
        ((129,350),(190,350),(217,350)), ((233,351),(239,339),(242,329)),
        ((244,318),(246,303),(238,292)), ((236,283),(242,272),(240,260)),
        ((240,248),(230,244),(220,245)))
    d.polygon(drawing_points(path), fill=WHITE)
    d.line(drawing_points(path), fill=NAVY, width=round(3.25*SCALE), joint='curve')
    body = body.resize((W,H),Image.Resampling.LANCZOS)
    backing = white_keyline(body.getchannel('A'))
    backing.alpha_composite(body)

    moving = np.maximum.reduce([np.asarray(obj.getchannel('A')) for obj in (BACK, FRONT, PAN)])
    y,x = np.indices((H,W))
    pad = ndimage.distance_transform_edt(moving < 128)
    # Only strip the wider sticker halo at Bagel's outside edge. Inside, the
    # untouched collar and apron should stay in the artist's own pen.
    radius = np.where((x < 116) | ((x > 234) & (y < 290)), 21.5, 1.25)
    erase = np.clip(radius+.5-pad,0,1)
    erase[(y < 249) | (y >= 345)] = 0
    # The existing outside torso and waistband lines continue behind the paw.
    erase[(x >= 219) & (y >= 288)] = 0
    return Image.composite(backing,SOURCE,Image.fromarray(np.uint8(erase*255)))


BODY = fixed_body()


def rotation(a):
    return np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])


def angle(v):
    return math.atan2(v[1],v[0])


def place(piece, a, pivot, moved):
    # PIL maps target pixels back into the source. This matrix is a pure rigid
    # rotation plus translation, maintaining line weight and pan dimensions.
    inv = rotation(-a)
    offset = pivot - inv @ moved
    transform = (inv[0,0],inv[0,1],offset[0],inv[1,0],inv[1,1],offset[1])
    return piece.transform((W,H),Image.Transform.AFFINE,transform,Image.Resampling.BICUBIC)


def positions(a):
    left = LS + rotation(a) @ (LH-LS)
    axis = RS-left
    d = np.linalg.norm(axis)
    axis /= d
    pan_len = np.linalg.norm(RH-LH)
    fore_len = np.linalg.norm(RH-RS)
    adjacent = (pan_len**2 - fore_len**2 + d**2)/(2*d)
    opposite = math.sqrt(max(0.,pan_len**2-adjacent**2))
    right = left + adjacent*axis + opposite*np.array([-axis[1],axis[0]])
    return left,right


def pan_action(t):
    # A small preparatory dip, smooth lift and gently settling offering pose.
    gesture = ink.keyed(t % 1, [(0,0),(.103,-3.3),(.392,33.5),(.481,31.1),
                                (.61,30.7),(.72,26.5),(.936,.95),(1,0)])
    a = math.radians(gesture)
    left,right = positions(a)
    front_angle = angle(right-RS) - angle(RH-RS)
    pan_angle = angle(right-left) - angle(RH-LH)
    arms = place(BACK, a, LS, LS)
    arms.alpha_composite(place(PAN, pan_angle, LH, left))
    arms.alpha_composite(place(FRONT, front_angle, RS, RS))
    result = white_keyline(arms.getchannel('A'))
    result.alpha_composite(BODY)
    result.alpha_composite(arms)
    # The chin overlaps the arm roots, exactly as in the original illustration.
    # Restore the original chin pixels only where an arm could rise through it.
    restore = Image.new('L',(W,H))
    ImageDraw.Draw(restore).polygon([(106,226),(248,226),(249,245),(241,247),
        (231,248),(212,248),(205,245),(138,242),(135,249),(120,249),(110,247)],fill=255)
    ImageDraw.Draw(restore).polygon([(248,263),(W,263),(W,H),(238,H),(238,333),
        (244,310),(245,287)],fill=255)
    result = Image.composite(SOURCE,result,restore)
    # At the neutral resting pose the exact untouched print forms the endpoint.
    # Blend the subpixel contour handoff during the first two degrees of travel.
    if abs(gesture) < 2:
        result = Image.blend(SOURCE, result, ink.step(0,2,abs(gesture)))
    return ink.finish(result,(4,26,327,418),.531,screen=(128,122))


if __name__=='__main__':
    ink.save('pan',pan_action)
