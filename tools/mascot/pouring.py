"""Prepare a rigidly separated pour animation from Bagel sticker number six.

The face, the held cup and the pitcher are three independent plates. Original
pen marks stay rigid on each. Only the strokes underneath the overlapping metal
spout and the beginning of the coffee stream need to be completed.
"""
from io import BytesIO
import math
from pathlib import Path
import sys

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'dist/media/mascot'
SIZE=256; N=48
INK=(.094,.126,.295)
WHITE=(1,1,1)
SHEET=ROOT/'dist/media/original/assets/customer/bagel-sticker-sheet.png'
CROP=(1200,825,1590,1240)
source=Image.open(SHEET).convert('RGBA').crop(CROP)
pixels=np.asarray(source,dtype=float)
density=np.clip((255-pixels[:,:,0])/231,0,1)*pixels[:,:,3]/255


def region(points):
    m=Image.new('L',source.size)
    ImageDraw.Draw(m).polygon(points,fill=255)
    return np.array(m)/255


def image_surface(img):
    b=BytesIO(); img.save(b,format='PNG'); b.seek(0)
    return cairo.ImageSurface.create_from_png(b)


def plate(ink,alpha):
    rgb=[255-(255-255*v)*ink for v in INK]
    return image_surface(Image.fromarray(np.uint8(np.clip(np.dstack(rgb+[255*alpha]),0,255))))


def path(ctx,geometry,fill=None,stroke=INK,width=3.9):
    ctx.new_path()
    for item in geometry:
        cmd,*pts=item
        if cmd=='M':ctx.move_to(*pts)
        elif cmd=='L':ctx.line_to(*pts)
        elif cmd=='C':ctx.curve_to(*pts)
        else:ctx.close_path()
    if fill:
        ctx.set_source_rgb(*fill);ctx.fill_preserve()
    if stroke:
        ctx.set_source_rgb(*stroke);ctx.set_line_width(width);ctx.stroke()
    else:
        ctx.new_path()


def art():
    # Keep every visible facial mark while setting aside the near paw and pitcher.
    bound=region([(65,69),(355,69),(355,278),(320,280),(298,273),(291,281),
                  (282,291),(258,293),(248,294),(234,296),(224,295),(214,296),
                  (202,294),(188,294),(176,290),(164,288),(152,281),(143,272),
                  (136,265),(132,265),(127,269),(104,273),(80,272)])
    ink_limit=region([(65,68),(355,68),(355,278),(320,281),(298,274),
                      (289,286),(281,291),(261,292),(246,293),(236,291),(232,280),
                      (224,277),(205,267),(179,257),(151,252),(145,254),(139,260),
                      (134,262),(127,269),(104,273),(80,272)])
    inks=density*ink_limit
    alpha=np.maximum(ndimage.distance_transform_edt(pixels[:,:,3]>128)>9,ink_limit*density)*bound
    head=plate(inks,alpha)

    # Nearly all of the visible foreground paw, handle and pitcher is original
    # ink. Only the rightmost few pixels of spout were hidden by the liquid.
    pitcher_curve=[('M',112,279),('C',127,265,136,255,151,259),
                    ('C',163,262,173,270,182,276),('L',211,293),
                    ('C',216,295,220,298,224,301),('L',209,305),
                    ('C',205,310,196,323,189,331),('L',153,312),
                    ('L',145,317),('C',133,324,119,320,116,308),
                    ('C',113,300,110,290,112,279),('Z',)]
    pitcher_limit=region([(105,282),(126,259),(140,254),(151,254),(164,260),
                          (182,272),(201,283),(212,291),(214,295),(210,298),
                          (209,302),(213,305),(190,335),(153,315),(149,319),
                          (139,324),(119,323),(110,309),(107,299)])
    pi=density*pitcher_limit
    # Cut off the original printed river before adding the two inked spout edges.
    pi[289:309,207:]=0
    # At print size the eyebrow-side ear touches the wrist above it. Discard
    # its two isolated nib marks; also trim the garment line below the paw.
    pi[259:270,118:128]=0
    pi[:257,133:142]=0
    pi[320:,140:147]=0
    pitcher=plate(pi,pi.clip(0,1))
    return head,pitcher,pitcher_curve


HEAD,PITCHER,PITCHER_SHAPE=art()
# Trace the torso against the actual garment edge, then replace its blank bib
# with the original garment hem and the complete opposite arm / held cup.
body_select=region([(129,371),(134,341),(140,323),(146,318),(153,319),
                    (150,325),(147,340),(147,363),(221,363),
                    (219,341),(222,320),(226,316),(230,327),(248,333),
                    (260,327),(265,319),(264,309),(258,300),(254,286),(271,284),
                    (286,276),(295,292),(299,311),(300,320),(308,347),
                    (311,381),(127,382)])
body_sel_ink=density*body_select
# The actual cup rim and surface are separate from the printed liquid.
rim_remove=region([(221,308),(261,305),(265,314),(261,323),(242,330),(224,335),(220,327)])
body_sel_ink*=1-rim_remove
BODY_INK=plate(body_sel_ink,body_sel_ink)


def cup_body(ctx):
    path(ctx,[('M',153,277),('C',151,293,148,308,143,323),
              ('C',137,342,132,360,134,374),
              ('C',178,374,267,374,302,373),
              ('C',305,353,302,329,297,314),
              ('C',297,296,288,280,273,274),
              ('C',254,276,238,284,226,287),('C',200,281,174,276,153,277),('Z',)],
         WHITE,None)
    path(ctx,[('M',152,290),('C',151,309,143,326,138,347),('C',135,358,134,369,134,373)],
         None,INK,4)
    # Underneath the chin the cotton neckline closes on the original right cuff.
    path(ctx,[('M',174,277),('C',188,290,207,303,221,303),
              ('C',239,304,248,299,251,286)],None,INK,4)
    ctx.set_source_surface(BODY_INK);ctx.paint()
    path(ctx,[('M',225.5,328),('C',225.5,333,229.2,337,232.5,341)],None,INK,3.5)
    # The oval is tilted in the same hand that holds the actual source cup.
    path(ctx,[('M',225,326),('C',228,319,245,312,255,312),
              ('C',266,311,266,317,260,321),('C',253,326,238,331,229,331),
              ('C',225,331,224,330,225,326),('Z',)],WHITE,INK,3.4)
    path(ctx,[('M',229,327),('C',236,322,251,317,259,317),
              ('C',258,320,247,324,239,326),('C',235,328,232,328,229,327),('Z',)],INK,None)


def keyed(t, keys):
    for (a,v),(b,w) in zip(keys,keys[1:]):
        if t<=b:
            q=(t-a)/(b-a); q=min(1,max(0,q));q=q*q*(3-2*q)
            return v+(w-v)*q
    return keys[-1][1]


def scene(t):
    # The forepaw travels with the pitcher: angular movement at this wrist is
    # substantially different from distorting the face or enlarging the spout.
    s=cairo.ImageSurface(cairo.FORMAT_ARGB32,SIZE*2,SIZE*2);ctx=cairo.Context(s)
    ctx.scale(2,2);ctx.translate(128,130);ctx.scale(.635,.635);ctx.translate(-217.5,-239)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND);ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    cup_body(ctx)
    tip=keyed(t,[(0,.03),(.09,0),(.23,.35),(.38,.91),(.49,1),(.65,.94),
                 (.72,.83),(.83,.27),(.94,.06),(1,.03)])
    look=keyed(t,[(0,.13),(.2,.25),(.44,.95),(.65,1),(.86,.28),(1,.13)])
    breath=math.sin(t*math.tau)
    ctx.save()
    ctx.translate(223,285);ctx.rotate(math.radians(1.8*look-.7));ctx.translate(0,1.55*look+.4*breath)
    ctx.translate(-223,-285)
    ctx.set_source_surface(HEAD);ctx.paint()
    # The source paw obscures this tiny arc of fur. Its irregular underside is
    # completed behind the moving hand while eyes, mouth and cheeks stay intact.
    path(ctx,[('M',138.5,259),('C',137,264,139,266,143,268),
              ('C',144,273,147,275,151,276),('C',152,280,154,281,157,280),
              ('C',160,285,165,287,170,286),('C',178,292,184,291,191,292),
              ('C',201,294,210,294,217,291)],None,INK,3.9)
    ctx.restore()

    center=(141,298);theta=math.radians(-29+34*tip)
    dx=-5+11*tip;dy=1-16*tip
    ca,sa=math.cos(theta),math.sin(theta)
    sp=(224,301)
    fx=center[0]+dx+(sp[0]-center[0])*ca-(sp[1]-center[1])*sa
    fy=center[1]+dy+(sp[0]-center[0])*sa+(sp[1]-center[1])*ca
    # A curved taper grows until it meets the centre of the cup. On release the
    # top detaches first and the last short drop drains into the held cup.
    emission=keyed(t,[(0,0),(.245,0),(.33,1),(.70,1),(.775,0),(1,0)])
    reach=keyed(t,[(0,0),(.245,0),(.315,1),(.775,1),(.82,0),(1,0)])
    start=keyed(t,[(0,0),(.745,0),(.81,1),(1,1)])
    if reach>0 and start<reach:
        xs=[];ys=[]
        for u in np.linspace(start,reach,35):
            xs.append(fx+(244-fx)*(1-(1-u)**2))
            ys.append(fy+(323.5-fy)*u)
        left=[];right=[]
        for k,(x,y) in enumerate(zip(xs,ys)):
            u=k/(len(xs)-1); width=(.68+1.65*emission)*(1-.48*u)
            left.append((x-width,y));right.append((x+width,y))
        ctx.move_to(*left[0])
        for p in left[1:]+list(reversed(right)):ctx.line_to(*p)
        ctx.close_path();ctx.set_source_rgb(*INK);ctx.fill()
    ctx.save();ctx.translate(center[0]+dx,center[1]+dy);ctx.rotate(theta);ctx.translate(-center[0],-center[1])
    path(ctx,PITCHER_SHAPE,WHITE,None)
    ctx.set_source_surface(PITCHER);ctx.paint()
    path(ctx,[('M',199.7,285.9),('C',208,290,219,297,224,300),
              ('C',221,302,215,303,208.8,304.3)],None,INK,4.05)
    ctx.restore()
    b=BytesIO();s.write_to_png(b);b.seek(0);im=Image.open(b).convert('RGBA')
    bg=Image.new('RGBA',im.size,'white');bg.putalpha(im.getchannel('A').filter(ImageFilter.MaxFilter(17)))
    bg.alpha_composite(im);return bg.resize((SIZE,SIZE),Image.Resampling.LANCZOS)


def main():
    frames=[scene(i/N) for i in range(N)]
    assert len({f.tobytes() for f in frames})==N
    atlas=Image.new('RGBA',(8*SIZE,6*SIZE))
    for i,f in enumerate(frames):atlas.alpha_composite(f,((i%8)*SIZE,(i//8)*SIZE))
    atlas.save(DEST/'pour.webp',lossless=True,method=4)
    frames[0].save(DEST/'pour-still.webp',lossless=True,method=4)
    if len(sys.argv)>1:
        p=Path(sys.argv[1])
        proof=Image.new('RGB',(256*7,256),'#eee0c4')
        for j,i in enumerate([0,8,13,19,27,35,43]):proof.paste(frames[i],(j*256,0),frames[i])
        proof.save(p/'coffee-rigid-proof.jpg')
        rendered=[]
        for f in frames:
            bg=Image.new('RGB',f.size,'#f1e4be');bg.paste(f,(0,0),f);rendered.append(bg)
        rendered[0].save(p/'coffee-rigid-pour.gif',save_all=True,append_images=rendered[1:],duration=65,loop=0,disposal=2)


if __name__=='__main__':
    main()
