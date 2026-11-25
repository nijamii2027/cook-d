"""Bagel smells a freshly baked salt roll, then offers it on a wooden baker's peel.

Rebuild the artwork with /usr/bin/python3 tools/mascot/baker_peel.py.
Head and chef hat are preserved from the café's original bakery sticker.
"""
from io import BytesIO
from math import cos, radians, sin, tau
from pathlib import Path

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage

from climbing import INK, WHITE, outline, surface
from original_portrait import prepared_ink, cutout

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "dist/media/mascot"
SOURCE = ROOT / "dist/media/original/assets/customer/bagel-sticker-sheet.png"
SIZE = 320
COUNT = 48
SCALE = 2


def smooth(a, b, u):
    v = max(0., min(1., (u - a) / (b - a)))
    return v * v * (3 - 2 * v)


def cue(u, points):
    """Ease into holds as the arms take and release the weight."""
    for (a, v), (b, w) in zip(points, points[1:]):
        if u <= b:
            return v + (w - v) * smooth(a, b, u)
    return points[-1][1]


def chef_face():
    sheet = Image.open(SOURCE).convert("RGBA")
    bakery = sheet.crop((1130, 1510, 1610, 1980))
    mask = Image.new("L", bakery.size)
    draw = ImageDraw.Draw(mask)
    # The contour passes inside the shoulder/arms and around the original chin.
    draw.polygon([(120,67),(334,67),(334,273),(291,269),(277,270),(263,272),
                  (260,283),(237,287),(187,289),(180,285),(178,276),(165,277),
                  (158,278),(130,279),(119,271)], fill=255)
    density = prepared_ink(bakery) * np.asarray(mask) / 255
    head = cutout(density).crop((124,72,331,291))
    return ImageOps.mirror(head)


def sniff_face(base, amount):
    if amount < .025:
        return surface(base)
    image = base.copy()
    # Compress only the two original eye marks while the nose takes in the aroma.
    for box in ((67,116,97,142),(126,121,157,147)):
        l,t,r,b = box
        eye = base.crop(box)
        height = max(3,round(eye.height * (1 - .88*amount)))
        ImageDraw.Draw(image).rectangle((l,t,r-1,b-1),fill="white")
        image.paste(eye.resize((r-l,height),Image.Resampling.LANCZOS),(l, (t+b-height)//2))
    return surface(image)


def closed(ctx, pts, weight=2.7):
    outline(ctx, pts, weight, WHITE, True, .81)


def pen(ctx, pts, weight=1.8):
    outline(ctx, pts, weight, None, False, .83)


def body(ctx, lift, offer, tail):
    # Stance stays planted throughout the lift. The hips transfer the load
    # between feet while the hem and tied apron follow with a smaller motion.
    dx = 2.2 * offer - .9 * lift
    dy = -2.1 * lift + 1.1 * offer
    closed(ctx, [(89,200),(67,212),(52,213),(42,207),(37,199+tail),(31,200+tail),
                 (28,206+tail),(31,216+tail),(39,224+tail*.7),(48,228+tail*.3),
                 (61,230),(74,225),(91,220)], 2.7)
    closed(ctx, [(80+dx,229+dy),(98+dx,232+dy),(98,243),(96,256),(92,263),
                 (83,264),(79,261),(81,252),(80,241)], 2.8)
    closed(ctx, [(119+dx,229+dy),(138+dx,229+dy),(138,245),(140,257),(139,263),
                 (131,265),(124,263),(123,254),(120,250)], 2.8)
    ctx.save()
    ctx.translate(dx, dy)
    closed(ctx, [(74,177),(81,159),(95,146),(116,149),(133,155),(142,172),
                 (145,201),(142,225),(138,240),(118,241),(97,242),(75,236),
                 (70,221),(69,198)], 3.1)
    closed(ctx, [(78,155),(85,158),(87,173),(99,180),(114,178),(125,169),
                 (133,153),(141,159),(139,172),(144,191),(142,207),(143,232),
                 (134,237),(114,237),(92,238),(72,234),(73,213),(69,193),(72,175)], 2.9)
    pen(ctx, [(79,225),(85,228),(93,229)], 1.6)
    closed(ctx, [(74,187),(65,188),(61,194),(64,196),(70,191),(73,191)], 1.65)
    ctx.restore()
    return dx, dy


def foreleg(ctx, shoulder, palm, side):
    sx, sy = shoulder
    px, py = palm
    ex = min(sx, px) - (6 if side < 0 else 1)
    ey = max(sy+13, py+3)
    # One continuous outline joins the small elbow, wrist and mitten.
    closed(ctx, [(sx-5,sy-3),(sx+5,sy),(sx+7,sy+10),(ex+5,ey-5),(px-4,py-4),
                 (px+1,py-6),(px+5,py-5),(px+7,py-2),(px+6,py+3),(px+1,py+5),
                 (px-4,py+4),(ex-2,ey+4),(ex-7,ey+1),(ex-8,ey-5),(sx-8,sy+9)], 2.65)
    pen(ctx, [(px+1,py+1),(px+2,py+3),(px+3,py+3)], 1.26)


def peel_board(ctx, root, angle):
    ctx.save()
    ctx.translate(*root)
    ctx.rotate(angle)
    # The narrow handle broadens gradually into a round-end wooden paddle.
    closed(ctx, [(-32,-3),(-14,-3.5),(37,-3.4),(63,-4.2),(79,-8.2),
                 (91,-12.3),(114,-14.6),(137,-13.7),(155,-9.8),(166,-4.6),
                 (168,0),(166,4),(153,9.4),(133,13.7),(112,14.3),(93,11.7),
                 (78,7.6),(62,3.6),(37,3.3),(-13,3.4),(-31,3),(-34,.9),(-34,-1.1)], 2.85)
    pen(ctx, [(81,6.8),(99,10.8),(119,11.7),(140,9.9),(153,6.1)], 1.35)
    pen(ctx, [(-25,-.1),(-16,.2),(-8,-.2)], 1.38)
    # A single shio-pan with its curled tip, rolled seam and a few coarse salt grains.
    ctx.translate(118, -2)
    closed(ctx, [(-37,1),(-40,-4),(-38,-10),(-30,-16),(-23,-23),(-12,-28),
                 (-4,-30),(9,-31),(20,-28),(29,-22),(35,-15),(41,-12),(43,-7),
                 (39,-3),(30,-2),(19,2),(8,5),(-6,6),(-21,5),(-31,3)], 2.85)
    pen(ctx, [(-22,-21),(-18,-17),(-18,-10),(-21,-4),(-25,1)], 1.85)
    pen(ctx, [(-4,-29),(2,-25),(7,-19),(10,-12),(11,-5),(10,1)], 2.1)
    pen(ctx, [(19,-27),(22,-23),(26,-17),(28,-11),(27,-7)], 1.75)
    pen(ctx, [(32,-11),(37,-10),(39,-8),(37,-6)], 1.45)
    for x,y in ((-8,-19),(-1,-13),(8,-24),(16,-16),(-12,-8)):
        pen(ctx, [(x-1.15,y+.7),(x+.5,y-.8),(x+1.4,y-.5)], 1.18)
    ctx.restore()


def steaming(ctx, origin, u, sniff):
    # The wisps curl toward the nose during the sniff and rise upright on presentation.
    for j, (offset, height) in enumerate(((-8,24),(7,30))):
        pts = []
        phase = tau * (u + j*.32)
        for k in range(12):
            v = k / 11
            x = origin[0]+offset + (2.1 + 1.8*v) * sin(phase + v*6.4) - (4+11*sniff)*v*v
            y = origin[1] - v * (height + 2.7*cos(phase))
            pts.append((x, y))
        pen(ctx, pts, 1.45 if j else 1.65)


def picture(ctx, image, x, y, zoom, tilt):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(tilt)
    ctx.scale(zoom,zoom)
    ctx.set_source_surface(image, -image.get_width()*.52, -image.get_height()*.83)
    ctx.paint()
    ctx.restore()


def make_frame(head, u):
    # Beat 1: accept the weight. Beat 2: draw it in, sniff twice.
    # Beat 3: offer it out. Hold long enough to read the finished loaf.
    lift = cue(u, [(0,0),(.095,0),(.31,1),(.53,1),(.7,.65),(.82,.64),(.98,0),(1,0)])
    offer = cue(u, [(0,0),(.14,0),(.32,-.45),(.49,-.45),(.68,1),(.81,1),(.98,0),(1,0)])
    sniff = cue(u, [(0,0),(.28,0),(.37,1),(.413,.29),(.465,.91),(.545,.08),(.62,0),(1,0)])
    breath = sin(tau*u)
    ctx_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE*SCALE,SIZE*SCALE)
    ctx = cairo.Context(ctx_surface)
    ctx.scale(SCALE,SCALE)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    dx,dy = body(ctx, lift, offer, 3.2*sin(tau*u+.2)+2.5*sniff)
    root = (88 + 10*offer - 5*lift, 208 - 22*lift + .8*breath)
    angle = radians(-4 - 5.6*lift + 3*offer)
    tangent = np.array([cos(angle), sin(angle)])
    normal = np.array([-sin(angle), cos(angle)])
    back = np.array(root) + tangent*4 - normal*.75
    front = np.array(root) + tangent*46 - normal*.7
    # Both shoulders tuck under the fur at the chin. Their small gripping pads
    # close over the handle only after the peel has been placed.
    foreleg(ctx, (82+dx,164+dy), tuple(back), -1)
    foreleg(ctx, (125+dx,152+dy), tuple(front), 1)
    steam_base = np.array(root) + tangent * 119 - normal * 36
    steaming(ctx, steam_base, u, sniff)
    head_tilt = radians(-3.5 + 7.5*sniff - 3.8*offer + 1.1*breath)
    picture(ctx, sniff_face(head,sniff), 111+3*lift+7.2*sniff+2.4*offer, 152+dy+2*sniff-2*offer+.5*breath, .68, head_tilt)
    peel_board(ctx, root, angle)
    fx,fy = front
    closed(ctx,[(fx-5.2,fy-3.1),(fx-4.6,fy-6),(fx-.8,fy-6.4),(fx+2.7,fy-5.1),
                (fx+5.5,fy-2.7),(fx+5.7,fy+.4),(fx+4,fy+2.6),(fx+1.8,fy+2.1),
                (fx+.2,fy+3.2),(fx-2.7,fy+1.5),(fx-5,fy+.7)],2.15)
    pen(ctx,[(fx+1.3,fy-.7),(fx+2.1,fy+.5),(fx+2.2,fy+1.6)],1.02)
    # A small white paw tip laps around the rear grip, leaving a visible handle
    # between the paws and a short lever to the left.
    closed(ctx, [(back[0]-5,back[1]-3),(back[0]-4,back[1]-6),(back[0],back[1]-6),
                 (back[0]+3.8,back[1]-4),(back[0]+4.6,back[1]-1),(back[0]+3.8,back[1]+1.6),
                 (back[0]+.2,back[1]+1.3),(back[0]-3,back[1])], 1.9)
    stream=BytesIO()
    ctx_surface.write_to_png(stream)
    stream.seek(0)
    art=Image.open(stream).convert("RGBA")
    # One continuous white cut edge follows all of the moving pen shapes.
    alpha=np.asarray(art.getchannel("A"), dtype=float)/255
    dist=ndimage.distance_transform_edt(alpha<.375)
    edge=np.uint8(np.clip(4.2*SCALE+.5-dist,0,1)*255)
    backing=Image.new("RGBA",art.size,"white")
    backing.putalpha(Image.fromarray(edge))
    backing.alpha_composite(art)
    return backing.crop((4*SCALE, 9*SCALE, 287*SCALE, 292*SCALE)).resize((SIZE,SIZE), Image.Resampling.LANCZOS)


def build():
    face = chef_face()
    frames = [make_frame(face, n / COUNT) for n in range(COUNT)]
    assert len({f.tobytes() for f in frames}) == COUNT
    assert frames[0].tobytes() == make_frame(face, 1.).tobytes()
    atlas = Image.new("RGBA", (SIZE*8,SIZE*6))
    for n,frame in enumerate(frames):
        atlas.alpha_composite(frame,(n%8*SIZE,n//8*SIZE))
    atlas.save(DEST/"peel.webp", lossless=True,method=4)
    frames[0].save(DEST/"peel-still.webp",lossless=True,method=5)
    return frames


if __name__ == "__main__":
    build()
