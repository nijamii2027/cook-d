"""Two 48-pose sticker performances: sift the rolls, and unfurl the arrival pennant.

Run with the system Python with Pillow, NumPy, Pycairo and SciPy. Reuses the
illustrator's original bone hat, face, ears and scored pastry. The props and
articulated paws are inked around those cutouts at two-times export size.
"""
from io import BytesIO
from math import sin, cos, tau, pi, radians
from pathlib import Path
import sys
import cairo
import numpy as np
from PIL import Image
from scipy import ndimage
from menu_chop import INK, PAPER, SOURCE, DEST, HEAD, path, oval, arm, key, ease
from original_portrait import extract_head, prepared_ink, cutout

COUNT=48
CELL=256
R=Image.Resampling.LANCZOS
original=Image.open(SOURCE).convert('RGBA')


def to_surface(image):
    stream=BytesIO();image.save(stream,format='PNG');stream.seek(0)
    return cairo.ImageSurface.create_from_png(stream)


stand=to_surface(extract_head(original))
# Scored bread from the bottom-right pastry on the café artist's prep sticker.
roll_crop=original.crop((1130+253,1510+376,1130+327,1510+419))
roll=to_surface(cutout(prepared_ink(roll_crop)))


def put(ctx,img,x,y,scale,angle=0):
    ctx.save();ctx.translate(x,y);ctx.rotate(radians(angle));ctx.scale(scale,scale)
    ctx.set_source_surface(img,-img.get_width()/2,-img.get_height());ctx.paint();ctx.restore()


def chef_body(ctx,x,y,lift=0):
    ctx.save();ctx.translate(x,y+lift)
    path(ctx,[('M',-25,-29),('C',-31,-15,-38,3,-36,24),('C',-18,32,18,29,34,23),('C',34,1,29,-19,22,-29),('Z',)],width=2.8)
    path(ctx,[('M',-22,-28),('C',-14,-14,6,-13,20,-27),('M',-25,6),('C',-14,9,4,10,23,6),('M',-8,12),('C',-7,20,6,21,9,12)],None,1.65)
    ctx.restore()


def paw(ctx,x,y,angle=0):
    ctx.save();ctx.translate(x,y);ctx.rotate(angle)
    path(ctx,[('M',-6,-3),('C',-6,-7,-2,-8,2,-6),('C',4,-4,7,-4,7,-.3),('C',8,3,5,5,3,5),('C',1,8,-4,6,-5,4),('C',-8,3,-8,-1,-6,-3),('Z',)],width=1.9)
    path(ctx,[('M',.4,4.5),('C',2,4.6,3.5,3.4,3.9,1.8)],None,1.15);ctx.restore()


def bakeware(ctx):
    # Low oval tray and a paper sack. Rolls remain registered to the tray.
    path(ctx,[('M',31,199),('C',36,205,52,207,70,209),('L',213,222),('C',225,222,234,218,236,213),('L',226,206),('C',183,195,105,187,47,188),('Z',)],width=2.0)
    path(ctx,[('M',32,197),('C',49,191,115,197,173,203),('C',201,206,229,207,235,212),('C',228,218,219,219,208,218),('L',61,206),('C',45,204,33,202,32,197),('Z',)],width=1.65)
    # A little mixing bowl catches the sieve on each return stroke. Its flour
    # mound sits at the same height as the mesh at the bottom of the scoop.
    path(ctx,[('M',69,179),('C',72,188,78,195,91,195),('C',103,196,113,191,116,177),('C',101,173,84,173,69,179),('Z',)],width=1.9)
    oval(ctx,92,178.5,23.5,5,-.02,width=1.65)
    path(ctx,[('M',72,179),('C',75,177,79,176,83,176),('C',87,172,91,171,95,173),('C',100,170,107,175,111,178)],None,1.2)
    for x,y,sc,angle in [(123,202,.55,-6),(164,207,.75,-5),(210,212,.72,9)]:
        put(ctx,roll,x,y,sc,angle)


def sieve(ctx,x,y,angle):
    ctx.save();ctx.translate(x,y);ctx.rotate(radians(angle))
    path(ctx,[('M',-53,-4),('C',-47,-5,-31,-3,-20,-2),('L',-17,3),('C',-29,3,-45,1,-52,1),('C',-55,1,-56,-3,-53,-4),('Z',)],width=1.85)
    path(ctx,[('M',-23,-4),('C',-21,9,-14,15,-3,16),('C',9,18,18,11,22,-3),('C',10,1,-11,3,-23,-4),('Z',)],width=2.0)
    for pos in [-16,-9,-2,5,12]:
        path(ctx,[('M',pos,1),('C',pos+.5,5,pos+1.5,9,pos+4,12)],None,.9)
    for off in [4.5,8.5]:path(ctx,[('M',-16,off),('C',-8,off+4,6,off+4,15,off-.5)],None,.85)
    oval(ctx,0,-3.8,23,5.4,-.018,width=2.15)
    path(ctx,[('M',-16,-3.4),('C',-12,-7,-7,-9,-4,-7),('C',3,-13,10,-8,16,-4)],None,1.35)
    ctx.restore()


def sift_pose(t):
    carry=key(t,[(0,0),(.12,-.15),(.28,.41),(.37,1),(.75,1),(.87,.67),(1,0)])
    shake=key(t,[(0,0),(.31,0),(.40,1),(.69,1),(.78,0),(1,0)])
    sweep=sin(2*pi*(t-.38)/.36)
    jitter=sin(2*pi*(t-.37)/.091)
    return (104+79*carry+shake*(9*sweep+3.1*jitter),164-33*carry+1.8*jitter*shake,
            -13+15*carry+5*shake*jitter,carry,shake)


def flour(ctx,t):
    # Each fleck starts from the sieve as it shakes at the *emission* time and
    # follows a ballistic arc toward the stationary bread. No random frame noise.
    for i in range(49):
        born=.355+i*.0075
        flight=.153+(i%5)*.012
        u=(t-born)/flight
        if not 0<u<1:continue
        bx,by,_,_,_=sift_pose(born)
        spread=sin(i*5.041)*12.5
        x=bx+spread*.9+u*(6.2+spread*.65)+1.8*sin(pi*u)
        y=by+14.5+51*u*u-2.2*sin(pi*u)+.62*spread*u
        r=(.75+.60*((i*29)%11)/10)*min(1,5.5*u,6.5*(1-u))
        if r<=.10:continue
        oval(ctx,x,y,r,r*(1.07+.25*sin(i)),.35,fill=INK if i%4==0 else PAPER,width=.7)


def dust(ctx,t):
    x,y,angle,carry,shake=sift_pose(t)
    a=radians(angle);br=sin(t*tau)
    grip=(x-43*cos(a),y-43*sin(a)-1.5)
    tap=(x-19-4*(1-shake),y-4.5-(4+4*cos(2*pi*(t-.37)/.091))*shake)
    chef_body(ctx,87,163,1.1*br)
    arm(ctx,(104,139),(133,148-10*carry),tap,6.0)
    bakeware(ctx)
    put(ctx,HEAD,83+2*carry,138+3*br,.49,-3.5+7*carry+1.0*br)
    arm(ctx,(65,143),(50,168+2*br),grip,6.2)
    flour(ctx,t);sieve(ctx,x,y,angle);paw(ctx,*grip,-.13);paw(ctx,*tap,-.85)
    if shake>.4:
        v=abs(sin(2*pi*(t-.37)/.091))
        if v>.32:
            path(ctx,[('M',x+26,y-6),('L',x+28+2*v,y-8),('M',x+26,y-.5),('L',x+29+v,y+.3)],None,1.2)


def arrive(ctx,t):
    up=key(t,[(0,0),(.11,.03),(.29,.41),(.51,1),(.68,.98),(.80,1),(1,.993)])
    unfurl=key(t,[(0,0),(.38,.02),(.53,.32),(.72,1),(.83,.97),(1,1)])
    read=key(t,[(0,0),(.16,1),(.32,.94),(.55,0),(1,0)])
    breath=sin(t*tau);xc=101+2*read
    # Sturdy feet take the weight once the runner has reached the pin.
    path(ctx,[('M',76,181),('C',71,187,70,196,71,205),('C',64,212,64,217,72,218),('C',81,219,91,216,92,208),('L',98,187),('Z',)],width=2.6)
    path(ctx,[('M',108,184),('C',110,194,115,203,117,209),('C',115,214,117,220,125,219),('C',131,220,140,215,136,207),('L',126,182),('Z',)],width=2.45)
    ctx.save();ctx.translate(123,174);ctx.rotate(radians(-6+7*up+2.8*breath))
    path(ctx,[('M',0,3),('C',13,8,17,0,19,-10),('C',21,-17,27,-18,29,-12),('C',31,1,20,15,1,14),('Z',)],width=2.3);ctx.restore()
    chef_body(ctx,xc,160,breath*.9)
    put(ctx,stand,xc-2+1.5*up,143+3.1*read, .52, 5.5*read-4.5*up+1.1*breath)
    # The far paw holds a little address slip. Its map pin folds toward Bagel.
    px=70+11*read;py=166-18*read+1.1*breath
    arm(ctx,(76,140),(52,153), (px+4,py+2),6.3)
    ctx.save();ctx.translate(px,py);ctx.rotate(radians(-8-15*read));
    path(ctx,[('M',-13,-14),('L',10,-13),('L',12,7),('L',4,7.5),('L',-6,8.5),('L',-13,11),('Z',)],width=1.85)
    path(ctx,[('M',-8,-7),('L',4,-7),('M',-7,-3),('L',1,-3),('M',-6,1),('L',4,1)],None,1.15);ctx.restore();paw(ctx,px+6,py+6,-.45)
    # Stitched pennant with the café's cup pictogram, tied to one rigid shaft.
    grip=np.array((126+19*up,161-30*up+1.2*breath));ang=radians(1+20*up)
    arm(ctx,(123,138),(152+13*up,159-23*up),grip,7)
    ctx.save();ctx.translate(*grip);ctx.rotate(ang)
    path(ctx,[('M',-.8,12),('L',-.8,-61),('C',-.8,-64,2.5,-64,2.5,-61),('L',2.2,11),('Z',)],width=1.9)
    wide=8+54*unfurl
    ripple=(1.1+2.1*unfurl)*sin(t*2*tau-.5)
    path(ctx,[('M',2,-58),('C',wide*.33,-62-ripple,wide*.70,-53+ripple,wide,-53-ripple),('C',wide*.71,-39+ripple,wide*.49,-38-ripple,wide*.25,-36+ripple),('C',wide*.14,-34,6,-32,2,-32),('Z',)],width=2.2)
    if unfurl>.23:
        ctx.save();ctx.translate(6+11*unfurl,-49);ctx.scale(min(1,(unfurl-.23)/.6),1)
        path(ctx,[('M',-6,0),('L',-4,7),('C',-2,10,3,10,6,7),('L',8,0),('Z',)],width=1.5)
        path(ctx,[('M',8,.7),('C',15,-1,13,6,7,6),('M',-7,11),('C',-2,12,4,12,9,10),('M',-1,-2),('C',-2,-5,2,-5,0,-8)],None,1.35);ctx.restore()
    ctx.restore();paw(ctx,*grip,.18)


def render(fn,t):
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,CELL*2,CELL*2);ctx=cairo.Context(surface);ctx.scale(2,2)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND);ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    fn(ctx,t)
    b=BytesIO();surface.write_to_png(b);b.seek(0)
    im=Image.open(b).convert('RGBA').resize((CELL,CELL),R)
    alpha=np.asarray(im.getchannel('A'))
    components,_=ndimage.label(alpha>=128)
    sizes=np.bincount(components.ravel());sizes[0]=0
    known_shape=sizes[components]>42
    d=ndimage.distance_transform_edt(~known_shape)
    thin=ndimage.distance_transform_edt(alpha<128)
    contour=np.uint8(np.clip(np.maximum(4.7-d,2-thin),0,1)*255)
    base=Image.new('RGBA',im.size,'white');base.putalpha(Image.fromarray(contour));base.alpha_composite(im)
    return base


def save(name,fn):
    frames=[render(fn,i/COUNT) for i in range(COUNT)]
    assert len({im.tobytes() for im in frames})==COUNT
    atlas=Image.new('RGBA',(CELL*8,CELL*6))
    for i,f in enumerate(frames):
        x,y,x2,y2=f.getbbox();assert x>0 and y>0 and x2<CELL and y2<CELL, (name,i,(x,y,x2,y2))
        atlas.alpha_composite(f,(i%8*CELL,i//8*CELL))
    atlas.save(DEST/(name+'.webp'),lossless=True,method=4);frames[0].save(DEST/(name+'-still.webp'),lossless=True,method=4)
    return frames


if __name__=='__main__':
    all_frames=[save('dust',dust),save('arrive',arrive)]
    if len(sys.argv)>1:
        dst=Path(sys.argv[1]);dst.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(256*5,256*2),'#f1d6ad')
        for j,fr in enumerate(all_frames):
            for n,i in enumerate([0,12,22,32,45]):board.paste(fr[i],(n*256,j*256),fr[i]);
        board.save(dst/'chef-finishers.jpg',quality=95)
