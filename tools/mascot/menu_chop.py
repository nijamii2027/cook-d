"""Bake Bagel's three-chop, scoop and serve loop from the café's original prep drawing.

Run with system Python (Pillow, NumPy, SciPy, Pycairo). The artist's facial ink is
kept as one rigid cutout. The guide paw holds spring onions across the board.
The working paw grips the bolster as the curved edge rocks against the board.
"""
from io import BytesIO
from pathlib import Path
from math import cos, sin, tan, radians, tau, pi, sqrt

import cairo
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from original_portrait import prepared_ink, cutout

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'dist/media/mascot'
SOURCE = ROOT / 'dist/media/original/assets/customer/bagel-sticker-sheet.png'
CELL = 256
COUNT = 48
INK = (26 / 255, 34 / 255, 75 / 255)
PAPER = (1, 1, 1)
BLADE_SHADE = (.88, .90, .95)
TAU = tau
BOARD_ANGLE = radians(7)
CONTACT_FRAMES = (5, 14, 23)
GRIP = (-61.5, -15.3)


def ease(a):
    a = max(0., min(1., a))
    return a*a*(3.-2.*a)


def key(t, sequence):
    for (a,x),(b,y) in zip(sequence,sequence[1:]):
        if t <= b:
            return x + (y-x)*ease((t-a)/(b-a))
    return sequence[-1][1]


def blend(a, b, t):
    return a + (b-a)*t


def edge_y(u):
    return -.0085 * max(u + 32., 0.)**2


def pose(t):
    f = t * COUNT
    lift = radians(key(f, [(0, 22), (5, 0), (5.6, 0), (9.5, 25),
                           (14, 0), (14.6, 0), (18.5, 23), (23, 0),
                           (25, 0), (31, 0), (36, 3), (39, 3), (42, 0),
                           (44, 3), (48, 22)]))
    # Basing the pose on the tangent to the curved edge keeps it on the board
    # throughout the stroke. The contact rolls from the belly towards the heel.
    tangent_u = max(-32., min(0., tan(lift) / .017 - 32.))
    edge_height = tangent_u * sin(lift) + edge_y(tangent_u) * cos(lift)
    x = key(f, [(0,179), (24,179), (26,170), (30.5,182), (36,205),
                (38,207), (41,202), (45,179), (48,179)])
    y = key(f, [(0,193), (24,193), (27,199), (30.5,199), (36,157),
                (38,155), (41,165), (45,193), (48,193)])
    # Roll the knife onto its side to gather the rings, then tip them out.
    flat = key(f, [(0,0), (23.5,0), (27,1), (36,1), (38.5,1),
                   (41,.12), (44,0), (48,0)])
    return (x + edge_height * sin(BOARD_ANGLE), y - edge_height * cos(BOARD_ANGLE),
            BOARD_ANGLE + lift, flat)


def local_point(pose, u, v):
    x, y, angle, flat = pose
    u += .32 * flat * v
    v *= 1. - .38 * flat
    return np.array([x + u*cos(angle)-v*sin(angle), y+u*sin(angle)+v*cos(angle)])


def path(ctx, commands, fill=PAPER, width=2.35, outline=INK):
    ctx.new_path()
    for code, *v in commands:
        if code == 'M': ctx.move_to(*v)
        elif code == 'C': ctx.curve_to(*v)
        elif code == 'L': ctx.line_to(*v)
        elif code == 'Z': ctx.close_path()
    if fill is not None:
        ctx.set_source_rgb(*fill)
        ctx.fill_preserve()
    if width:
        ctx.set_line_width(width);ctx.set_source_rgb(*outline);ctx.stroke()
    else:
        ctx.new_path()


def oval(ctx, x, y, rx, ry, angle=0, fill=PAPER, width=1.8):
    ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.scale(rx,ry)
    ctx.new_path();ctx.arc(0,0,1,0,TAU);ctx.restore()
    if fill is not None:
        ctx.set_source_rgb(*fill);ctx.fill_preserve()
    ctx.set_source_rgb(*INK);ctx.set_line_width(width);ctx.stroke()


def artist_head():
    # Bottom-right sticker: preserve the bone, eyes, ear tufts and face verbatim.
    prep = Image.open(SOURCE).convert('RGBA').crop((1130,1510,1610,1980))
    field = Image.new('L',prep.size); d=ImageDraw.Draw(field)
    d.polygon([(104,62),(333,62),(335,266),(313,273),(297,269),(292,267),
               (285,270),(269,272),(259,271),(257,280),(249,285),(227,288),
               (183,286),(183,277),(168,277),(160,281),(135,281),(117,274),(104,251)],fill=255)
    ink = prepared_ink(prep)*np.asarray(field)/255
    chin = Image.new('L',prep.size); d=ImageDraw.Draw(chin)
    d.line([(169,273),(175,276),(182,278),(190,282)],fill=255,width=3)
    ink[278:287,162:181]=0
    head = cutout(np.maximum(ink,np.asarray(chin)/255)).crop((120,72,334,294))
    buf=BytesIO();head.save(buf,format='PNG');buf.seek(0)
    return cairo.ImageSurface.create_from_png(buf)


HEAD = artist_head()


def arm(ctx, shoulder, elbow, wrist, radius):
    # Ink the outline of one gently tapered arm in a continuous brush stroke.
    p0,p1,p2 = map(np.asarray,(shoulder,elbow,wrist))
    for colour,extra in ((INK,1.12),(PAPER,0)):
        ctx.new_path()
        for t in np.linspace(0.,1.,58):
            pt=(1-t)**2*p0+2*t*(1-t)*p1+t*t*p2
            r=blend(radius*1.14,radius,t)+extra
            ctx.new_sub_path();ctx.arc(*pt,r,0,TAU)
        ctx.set_source_rgb(*colour);ctx.fill()


def blade(ctx, p):
    ctx.save();ctx.translate(p[0],p[1]);ctx.rotate(p[2])
    ctx.transform(cairo.Matrix(1,0,.32*p[3],1-.38*p[3],0,0))
    # The rounded handle butt and its rivet remain visible behind the paw.
    path(ctx,[('M',-89,-19),('C',-88,-21,-86,-21,-82,-20.2),
              ('C',-72,-18.9,-65,-20,-55,-20),('L',-53.5,-12),
              ('C',-63,-12.8,-71,-13,-80,-10.5),('C',-84,-9,-88,-9.3,-89,-12),
              ('C',-90,-14,-90,-16,-89,-19),('Z',)],fill=INK,width=1.2)
    oval(ctx,-82,-15.3,1.45,1.45,fill=PAPER,width=.6)
    # Broad heel, nearly straight spine and a gently rising belly. This lower
    # cubic is the same quadratic as edge_y(), traced from tip to heel.
    path(ctx,[('M',-54.5,-21),('C',-44,-21.7,-31,-21,-23,-20),
              ('C',-13,-18.8,-4.3,-14.5,0,edge_y(0)),
              ('C',-10.667,-2.9013,-21.333,0,-32,0),('L',-53.1,0),
              ('C',-54.6,0,-55.4,-.3,-55.4,-1.3),('L',-55.4,-10.3),
              ('C',-55.5,-12.2,-57.5,-12.4,-58.5,-12.8),
              ('L',-58.5,-19.6),('L',-54.5,-21),('Z',)],fill=BLADE_SHADE,width=2.25)
    path(ctx,[('M',-52,-3),('C',-37,-2.1,-21,-2.3,-11,-6.3)],fill=None,width=.9)
    ctx.restore()


def stalks(ctx, t):
    # The stalk axes recede across the blade's path. Their freshly sliced
    # mouths appear at the heel, where the cutting edge meets the board last.
    f = t * COUNT
    feed = sum(ease((f-i)/3) for i in CONTACT_FRAMES) * (1 - ease((f-41)/7))
    withdraw = key(f, [(0,0), (24,0), (28,1), (41,1), (48,0)])
    for i, (x, y) in enumerate([(146,189), (151,190), (155,191)]):
        x += withdraw*3
        y -= withdraw*3
        end_x = [167,178,189][i] - feed + withdraw*3*(i+1)
        end_y = [156,153,158][i] + feed - withdraw*2
        path(ctx,[('M',x-2,y-1),('C',x+3,y-10,end_x-8,end_y+5,end_x,end_y),
                  ('C',end_x-2,end_y+8,x+8,y-8,x+2,y+1),('Z',)],width=1.5)
        oval(ctx,x,y,2.25,1.55,.4,width=1.25)


def scallion(ctx, x, y, angle=0., scale=1.):
    ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.scale(scale,scale)
    # Each round has a deliberately irregular ring and a visible hollow centre.
    path(ctx,[('M',-4,0),('C',-4.4,-2.2,-2,-3.5,0,-3.2),
              ('C',3.6,-3.4,5,-.7,3.7,1.8),('C',2,3.5,-.5,3.6,-2.7,2.1),
              ('C',-3.7,1.5,-4,.8,-4,0),('Z',)],width=1.35)
    oval(ctx,.0,-.1,1.55,1.0,-.22,width=.85)
    ctx.restore()


def bowl(ctx):
    path(ctx,[('M',191,199),('C',193,204,196,212,202,214),
              ('C',210,218,222,214,225,211),('C',229,206,230,201,231,196),
              ('C',222,190,202,191,191,199),('Z',)],width=2.15)
    oval(ctx,211,197,20,5.2,-.07,width=2.0)
    path(ctx,[('M',199,205),('C',200,207,202,208,203,209)],None,1.15)


def frame(t):
    super_size=2
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,CELL*super_size,CELL*super_size)
    ctx=cairo.Context(surface);ctx.scale(super_size,super_size)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND);ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    p=pose(t)
    presentation = key(t,[(0,0),(.60,0),(.77,1),(.84,1),(.96,0),(1,0)])
    f = t * COUNT
    impact = sum(max(0.,1-abs(f-v)/2.5)**2 for v in CONTACT_FRAMES)
    breath = sin(TAU*t)
    sway = (-1.3*breath + 3.7*presentation)
    # Apron, neck opening and seam, based on the shape of the café's prep pose.
    path(ctx,[('M',82+sway,123),('C',93,116,120,116,133+sway,122),
              ('C',142,131,143,153,148,181),('C',131,188,86,190,66,186),
              ('C',68,162,71,136,82+sway,123),('Z',)],width=2.5)
    path(ctx,[('M',83,126),('C',87,142,108,146,124,132),('M',75,159),
              ('C',83,161,89,161,94,160)],None,1.7)

    # Slight asymmetry in the cutting board matches the uneven printed outlines.
    path(ctx,[('M',22,182),('C',64,180,162,171,196,169),('C',200,168,203,169,206,171),
              ('L',235,195),('C',237,197,237,201,234,203),('L',55,223),
              ('C',52,223,49,223,47,221),('L',21,190),('C',18,186,18,183,22,182),('Z',)],width=2.6)
    path(ctx,[('M',22,184),('C',31,194,43,207,53,219),('C',100,214,188,204,235,198)],None,1.35)
    for x,y,length in ((43,189,15),(56,192,8),(76,211,17),(177,176,8),(121,207,10)):
        path(ctx,[('M',x,y),('L',x+length,y-1.1)],None,.8)

    # Small nods follow the blade; the head remains the original illustration.
    ctx.save();ctx.translate(106+sway,137+breath*.9+impact*1.8-presentation*2.5)
    ctx.rotate(radians(1.2+1.5*breath+3*impact-7.3*presentation))
    ctx.scale(.586,.586);ctx.set_source_surface(HEAD,-HEAD.get_width()*.5,-HEAD.get_height()+4)
    ctx.paint();ctx.restore()
    stalks(ctx,t)

    guide=np.array([172+3*presentation,164.5-12*presentation])
    arm(ctx,(135+sway,134),(160+4*presentation,138-2*presentation),guide,6.0)
    ctx.save();ctx.translate(*guide);ctx.rotate(.15)
    path(ctx,[('M',-7,-2),('C',-6,-6,-3,-8,0,-7.8),
              ('C',4,-8,7,-6,8,-3),('C',10,-1.5,10,1.6,8.5,3),
              ('C',8.4,5.1,6.1,6.1,4,5.1),('C',2.5,6.4,.6,6.5,-1,5.1),
              ('C',-3.9,6,-6,4.6,-6.1,2.5),('C',-7.8,1,-8,0,-7,-2),('Z',)],width=1.8)
    path(ctx,[('M',5.8,1.7),('C',5.9,3.1,5.2,4.2,4,5.1),
              ('M',.5,2.2),('C',.7,3.4,-.2,4.4,-1,5.1)],None,1.05)
    ctx.restore()

    grip=local_point(p,*GRIP)
    wrist=local_point(p,GRIP[0]-6,GRIP[1]-4)
    shoulder=np.array((77+sway,135.))
    # Solve for a folded elbow: the upper arm and the forearm keep their
    # lengths as the paw moves from the board to the serving position.
    distance=np.linalg.norm(wrist-shoulder)
    direction=(wrist-shoulder)/distance
    along=(31**2-37**2+distance**2)/(2*distance)
    bend=sqrt(max(0.,31**2-along**2))
    elbow=shoulder+along*direction+bend*np.array((-direction[1],direction[0]))
    arm(ctx,shoulder,elbow,wrist,6.9)
    blade(ctx,p)
    # A pinching paw over the near face of the bolster: the thumb reaches
    # forward and the other little pads curl beneath the dark handle.
    ctx.save();ctx.translate(*grip);ctx.rotate(p[2])
    path(ctx,[('M',-9.3,-.5),('C',-10.3,-4.7,-8.6,-8.3,-5.9,-9.2),
              ('C',-3.2,-10.2,-.3,-9.2,1.2,-7.6),('C',3.4,-7.8,5.6,-6.3,6.5,-4.4),
              ('C',8.7,-3.1,10,-1,9.5,.6),('C',9.1,2.8,6.8,3.4,4.2,2.3),
              ('C',4.7,4.3,4,6.1,2.2,6.7),('C',.9,7.3,-.7,7,-1.7,6.3),
              ('C',-3.8,8,-6.4,6.9,-6.9,4.6),('C',-9.1,4,-9.8,2.1,-9.3,-.5),('Z',)],width=1.85)
    path(ctx,[('M',1.6,-.4),('C',2.4,.6,3.2,1.7,4.2,2.3),
              ('M',-1.1,3.2),('C',-.9,4.2,-1,5.3,-1.7,6.3)],None,1.15)
    ctx.restore()

    bowl(ctx)
    for x,y in [(206,198),(214,196.5),(218,198.4)]:
        scallion(ctx,x,y,.22,.65)
    # Three groups appear at each board contact, slide onto the passing blade,
    # travel with it in a rigid arrangement, then fall into the serving bowl.
    rings=[(5,(-41,-8),(145,194)),(5,(-43,-14),(143,198)),(14,(-30,-9),(151,195)),
           (14,(-34,-14),(151,200)),(23,(-20,-9),(158,195)),(23,(-22,-14),(158,200))]
    for i,(born,local,floor) in enumerate(rings):
        if f < born or f > 46: continue
        gather=ease((f-25.5)/5)
        slide=ease((f-36.7-i*.11)/3.3)
        target=local_point(p,blend(local[0],-3.,slide),blend(local[1],-8.5,slide))
        start=ease((f-born)/2.5)
        floor=np.asarray(floor,float)
        floor[0]=blend(150.,floor[0],start)
        floor[1]=blend(188.,floor[1],start) - 5*sin(pi*start)
        pos=floor*(1-gather)+target*gather
        fall=ease((f-38-i*.13)/5.5)
        if fall:
            pos=pos*(1-fall)+np.array([202+(i%3)*6,197+(i//3)*1.5])*fall
            pos[1]-=4.2*sin(pi*fall)
        fade=1-ease((t-.905)/.05)
        scallion(ctx,*pos,angle=.33*sin(i*2.4)+gather*p[2]+fall*.6,scale=(.70+.23*start)*fade+.01)

    buf=BytesIO();surface.write_to_png(buf);buf.seek(0)
    im=Image.open(buf).convert('RGBA').resize((CELL,CELL),Image.Resampling.LANCZOS)
    alpha=np.asarray(im.getchannel('A'))
    distance=ndimage.distance_transform_edt(alpha<120)
    edge=np.clip(5.15-distance,0,1)
    sticker=Image.new('RGBA',im.size,'white')
    sticker.putalpha(Image.fromarray(np.uint8(edge*255)))
    sticker.alpha_composite(im)
    return sticker


def build():
    frames=[frame(i/COUNT) for i in range(COUNT)]
    assert len({im.tobytes() for im in frames}) == COUNT
    atlas=Image.new('RGBA',(CELL*8,CELL*6))
    for i,im in enumerate(frames):
        bounds=im.getbbox()
        assert bounds and min(bounds[:2])>2 and max(bounds[2:])<CELL-2
        atlas.alpha_composite(im,(CELL*(i%8),CELL*(i//8)))
    atlas.save(DEST/'chop.webp',lossless=True,method=4)
    frames[0].save(DEST/'chop-still.webp',lossless=True,method=4)
    return frames


if __name__=='__main__':
    build()
