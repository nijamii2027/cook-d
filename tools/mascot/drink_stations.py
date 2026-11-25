"""Draw the espresso tamp and the two-handed shaker station from original Bagel art.

The espresso performance reuses the exact serious head plate and completed muzzle
from pouring.py. The menu performance uses the other, standing artist portrait.
Both tools and both grips are positioned by a shared coordinate transform, so
pressing the tamper or removing the shaker lid keeps each paw on its held object.
"""
from io import BytesIO
import math

import cairo
import numpy as np
from PIL import Image, ImageFilter

import climbing as ink
import pouring
from original_portrait import extract_head

N = 48
SIZE = 256
DEST = ink.DEST
WHITE = (1,1,1)
NAVY = ink.INK
TAU = math.tau
FRONT = ink.surface(extract_head(Image.open(ink.SOURCE)))
V = ink.v


def key(t, points):
    return pouring.keyed(t,points)


def curve(ctx, geometry, fill=WHITE, width=2.65):
    pouring.path(ctx,geometry,fill,NAVY,width)


def stroke(ctx,points,width=1.65):
    ink.outline(ctx,points,width,None,False)


def oval(ctx,x,y,rx,ry,fill=WHITE,width=2.3):
    # Make the path on a scaled circle, but stroke it with a circular nib.
    ctx.save();ctx.translate(x,y);ctx.scale(rx,ry);ctx.new_path();ctx.arc(0,0,1,0,TAU);ctx.restore()
    if fill:
        ctx.set_source_rgb(*fill);ctx.fill_preserve()
    ctx.set_line_width(width);ctx.set_source_rgb(*NAVY);ctx.stroke()


def sprite():
    s=cairo.ImageSurface(cairo.FORMAT_ARGB32,SIZE*2,SIZE*2);ctx=cairo.Context(s)
    ctx.scale(2,2);ctx.set_line_join(cairo.LINE_JOIN_ROUND);ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    return s,ctx


def finish(s):
    data=BytesIO();s.write_to_png(data);data.seek(0);im=Image.open(data).convert('RGBA')
    sticker=Image.new('RGBA',im.size,'white')
    sticker.putalpha(im.getchannel('A').filter(ImageFilter.MaxFilter(15)));sticker.alpha_composite(im)
    return sticker.resize((SIZE,SIZE),Image.Resampling.LANCZOS)


def apron(ctx,center,drop,lean):
    ctx.save();ctx.translate(center,drop);ctx.rotate(lean)
    curve(ctx,[('M',-32,144),('C',-28,135,-18,130,-7,133),
               ('C',6,139,23,134,29,139),('C',37,149,47,183,48,208),
               ('C',40,211,-20,212,-45,211),('C',-45,191,-41,161,-32,144),('Z',)])
    curve(ctx,[('M',-25,146),('C',-20,155,-8,157,-2,157),
               ('C',8,159,19,155,22,146),('L',27,141),('C',33,148,33,156,32,164),
               ('C',35,177,40,199,40,208),('C',23,209,-21,208,-41,209),
               ('C',-44,201,-39,175,-36,163),('C',-34,155,-31,148,-30,143),('Z',)],WHITE,2.4)
    stroke(ctx,[(-34,201),(-27,203),(-19,202)],1.2)
    ctx.restore()


def arm(ctx,shoulder,elbow,wrist,near=True):
    """Follow the elbow with a tapered limb and leave room for the gripping paw."""
    a,b,c=[np.array(x,float) for x in (shoulder,elbow,wrist)]
    points=[]
    for t in np.linspace(0,1,55):
        q=(1-t)**2*a+2*(1-t)*t*b+t*t*c
        rad=(9.5 if near else 8.5)*(1-t)+6.6*t+1.8*math.sin(math.pi*t)
        points.append((*q,rad))
    for colour,extra in [(NAVY,1.4),(WHITE,-.8)]:
        ctx.new_path()
        for x,y,r in points:
            ctx.new_sub_path();ctx.arc(x,y,r+extra,0,TAU)
        ctx.set_source_rgb(*colour);ctx.fill()


def mitten(ctx,x,y,rotation,scale=1):
    """An irregular little hooked paw with a thumb and a shallow pad crease."""
    ctx.save();ctx.translate(x,y);ctx.rotate(rotation);ctx.scale(scale,scale)
    curve(ctx,[('M',-8,-4),('C',-6,-8,-1,-9,3,-8),
               ('C',7,-8,10,-5,9,-3),('C',10,-1,11,1,9,3),
               ('C',10,6,7,8,4,7),('C',1,9,-4,8,-6,6),
               ('C',-9,5,-10,0,-8,-4),('Z',)],WHITE,2.5)
    stroke(ctx,[(3,-4),(6,-3),(7,-1)],1.35);ctx.restore()


def serious_head(ctx,pressure,breath):
    # Identical proportions, registration and character ink to the original
    # approved coffee capsule, including the underside formerly hidden by a jug.
    ctx.save();ctx.translate(128+1.8*pressure,130+3.1*pressure+.55*breath)
    ctx.scale(.635,.635);ctx.translate(-217.5,-239)
    ctx.translate(223,285);ctx.rotate(math.radians(1.5*pressure-.7));ctx.translate(-223,-285)
    ctx.set_source_surface(pouring.HEAD);ctx.paint()
    pouring.path(ctx,[('M',138.5,259),('C',137,264,139,266,143,268),
        ('C',144,273,147,275,151,276),('C',152,280,154,281,157,280),
        ('C',160,285,165,287,170,286),('C',178,292,184,291,191,292),
        ('C',201,294,210,294,217,291)],None,pouring.INK,3.9)
    ctx.restore()


def portafilter(ctx,x,y):
    ctx.save();ctx.translate(x,y)
    # Rubber bar mat and the basket's flat little restaurant spouts.
    ink.outline(ctx,[(-22,17),(19,17),(24,20),(24,23),(-20,23),(-25,21)],2,WHITE)
    ink.outline(ctx,[(-8,11),(-6,17),(-1,18),(2,13),(6,18),(10,17),(11,10)],1.9,WHITE)
    # A kitchen portafilter's rubber-ended handle runs behind the basket rim.
    curve(ctx,[('M',-14,-4),('L',-49,-9),('C',-59,-11,-68,-10,-70,-6),
               ('C',-72,-3,-68,1,-61,1),('L',-15,3),('Z',)],WHITE,2.7)
    stroke(ctx,[(-62,-7),(-50,-7),(-41,-6)],1.1)
    curve(ctx,[('M',-20,-2),('C',-17,9,-13,14,-3,15),
               ('C',7,17,14,13,18,8),('L',22,-2),('Z',)],WHITE,2.55)
    oval(ctx,1,-2,21.4,6.1,WHITE,2.35);oval(ctx,1,-2,17.7,3.6,NAVY,1)
    stroke(ctx,[(-12,5),(-10,8),(-6,10)],1.35)
    ctx.restore()


def tamper(ctx,x,base,twist):
    ctx.save();ctx.translate(x,base)
    # Flat steel base with the weight of a squat, rounded wooden handle.
    curve(ctx,[('M',-16,-5),('C',-9,-7,11,-7,16,-4),('L',16,0),
               ('C',11,3,-9,4,-16,1),('Z',)],WHITE,2.2)
    oval(ctx,0,-5,15.8,3.4,WHITE,1.9)
    curve(ctx,[('M',-6,-7),('C',-4,-14,-5,-17,-8,-21),
               ('C',-15,-28,-9,-36,0,-37),('C',10,-37,14,-30,10,-24),
               ('C',5,-20,4,-14,6,-7),('C',3,-5,-3,-5,-6,-7),('Z',)],WHITE,2.4)
    stroke(ctx,[(3+2*twist,-33),(6+1.8*twist,-30),(5+twist,-28)],1.55)
    ctx.restore()


def tamp(t):
    s,ctx=sprite();breath=math.sin(TAU*t)
    down=key(t,[(0,.18),(.10,0),(.19,.02),(.315,.95),(.365,1),(.47,1),
                (.51,.86),(.558,1),(.72,1),(.79,.91),(.89,.23),(.96,.16),(1,.18)])
    twist=key(t,[(0,0),(.49,0),(.58,-1),(.67,1),(.73,-.7),(.78,.25),(.86,0),(1,0)])
    weight=key(t,[(0,.12),(.16,0),(.35,1),(.46,1),(.53,.76),(.68,1),(.85,.27),(1,.12)])
    tx=193+(.8*twist*down);base=152+36*down
    sx=123+weight*1.8
    apron(ctx,sx,2.3*weight,0)
    arm(ctx,(97,149+weight*2),(82,182),(129,187),False)
    # Forearm folds on the pickup, then straightens as the body puts weight
    # through the palm. The wrist polishes around a vertical axis at the base.
    grip=V(tx-2.2+twist*2.4,base-30.5)
    arm(ctx,(146,146+weight*3),(164-3*(1-down),167-27*(1-down)),grip+V(-5,1))
    serious_head(ctx,weight,breath)
    portafilter(ctx,192,193)
    mitten(ctx,130,187,-.25,.91)
    tamper(ctx,tx,base,twist)
    mitten(ctx,*grip,-.63+.29*twist,.94)
    if .56<t<.75:
        amp=math.sin((t-.56)/.19*math.pi)
        stroke(ctx,[(211,172),(215+2*amp,174),(217+3*amp,178)],.9+amp*.7)
    return finish(s)


def front_head(ctx,center,lift,roll):
    ctx.save();ctx.translate(center,113+lift);ctx.rotate(roll)
    ctx.scale(.586,.586);ctx.set_source_surface(FRONT,-123,-137);ctx.paint();ctx.restore()


def tin_body(ctx,present):
    # The two-piece ridged mixing tin becomes the serving tumbler; the ink
    # drink surface and ice are revealed physically when its lid lifts.
    curve(ctx,[('M',-17,1),('C',-17,13,-15,28,-12,39),
               ('C',-6,43,8,43,13,39),('C',15,28,17,13,18,1),('Z',)],WHITE,2.5)
    oval(ctx,.5,1,17.3,5.1,WHITE,2.0)
    oval(ctx,.5,1,14.1,3.5,NAVY,1.05)
    if present>.24:
        for x,y,theta in [(-4,-1.2,-.35),(5,.3,.32)]:
            ctx.save();ctx.translate(x,y);ctx.rotate(theta)
            ink.outline(ctx,[(-3,-1.2),(-1,-2.6),(2,-2.1),(3,.3),(1.3,1.7),(-2,1)],.7,WHITE)
            ctx.restore()
    for y,r in [(7,15.7),(10.5,15.5),(14,15.2)]:
        stroke(ctx,[(-r,y),(-7,y+2.4),(5,y+3),(r,y+.4)],1.2)
    stroke(ctx,[(-11,19),(-10,27),(-8.6,32)],1.3)
    stroke(ctx,[(7.8,35),(10.7,34)],1.25)


def tin_lid(ctx):
    # Shouldered cap with two rolled steel seams and a flat lid.
    curve(ctx,[('M',-17.3,0),('L',-16,-11),('C',-16,-14,-10,-18,-8,-20),
               ('L',-8,-28),('C',-6,-31,6,-31,8,-28),('L',8,-21),
               ('C',12,-18,16,-15,16,-11),('L',17.5,0),
               ('C',11,5,-10,5,-17.3,0),('Z',)],WHITE,2.45)
    oval(ctx,0,-28,8,2.8,WHITE,1.6)
    stroke(ctx,[(-14,-8),(-6,-5.5),(5,-5),(14.7,-7.4)],1.5)
    stroke(ctx,[(-7,-19),(-2,-18),(4,-18.4)],1.15)


def positioned(ctx,center,theta,shape,*params):
    ctx.save();ctx.translate(*center);ctx.rotate(theta);shape(ctx,*params);ctx.restore()


def grip_at(center,theta,offset):
    x,y=offset
    return np.array(center)+V(x*math.cos(theta)-y*math.sin(theta),x*math.sin(theta)+y*math.cos(theta))


def shake(t):
    s,ctx=sprite()
    # Three shoulder-to-hip strokes precede a pause, pop, and open-tin service.
    sealed=key(t,[(0,0),(.10,0),(.195,1),(.70,1),(.795,0),(1,0)])
    gather=key(t,[(0,0),(.13,0),(.23,1),(.625,1),(.72,.82),(.80,.08),(.9,0),(1,0)])
    drive_phase=min(1,max(0,(t-.225)/.415))
    drive=math.sin(TAU*3*drive_phase)*math.sin(math.pi*drive_phase)**.55
    breath=math.sin(TAU*t)
    # The head counterbalances every change in direction, away from the tin.
    head_x=102-3.1*gather-3.9*drive
    head_lift=1.8*gather-.85*drive+.55*breath
    apron(ctx,99-.9*drive,3*gather,.015*gather+.015*drive)
    front_head(ctx,head_x,head_lift,-.07*gather-.056*drive+.01*breath)
    origin=V(182-13*gather+18.6*drive,172-41*gather-20*drive+1.1*breath)
    theta=.11*(1-gather)-.60*gather-.31*drive
    # The detached cap travels back to the other hand as the tumbler extends.
    cap_origin=origin+V(-48*(1-sealed),-9*(1-sealed))
    cap_theta=theta+.43*(1-sealed)
    lower=grip_at(origin,theta,(-9,22));upper=grip_at(cap_origin,cap_theta,(-6,-15))
    arm(ctx,(124,143+head_lift),(139+8*drive,161-16*gather),lower+V(-4,2),False)
    arm(ctx,(81,148+head_lift),(87+9*drive,189-40*gather),upper+V(-4,1),True)
    positioned(ctx,origin,theta,tin_body,1-sealed);positioned(ctx,cap_origin,cap_theta,tin_lid)
    mitten(ctx,*lower,.25+theta,.88);mitten(ctx,*upper,-.65+cap_theta,.9)
    speed=math.cos(TAU*3*drive_phase)*math.sin(math.pi*drive_phase)
    if abs(speed)>.55:
        for y,length in [(-13,9),(0,6.3)]:
            p=grip_at(origin,theta,(25,y)); direction=1 if speed>0 else -1
            stroke(ctx,[p,p+V(3.3,-2.4)*direction,p+V(length,-length*.55)*direction],1.15)
    return finish(s)


def main():
    for name,fn in [('tamp',tamp),('shake',shake)]:
        atlas=Image.new('RGBA',(8*SIZE,6*SIZE));frames=[fn(i/N) for i in range(N)]
        assert len({f.tobytes() for f in frames})==N
        for i,f in enumerate(frames):
            box=f.getchannel('A').getbbox()
            assert min(box[0],box[1],SIZE-box[2],SIZE-box[3])>3
            atlas.paste(f,(i%8*SIZE,i//8*SIZE))
        atlas.save(DEST/(name+'.webp'),lossless=True,exact=True,method=4)
        frames[0].save(DEST/(name+'-still.webp'),lossless=True,exact=True,method=4)
        print(name,flush=True)


if __name__=='__main__':
    main()
