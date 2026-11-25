"""Grounded Bagel run and coffee break, using source head and seated apron lettering."""
from pathlib import Path
from io import BytesIO
import math, sys
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import cairo
from scipy.interpolate import CubicSpline
import ink_actions as a
from original_portrait import extract_head, swaying_head

SIZE=a.SIZE; N=a.N
C=(24/255,35/255,75/255)
WHITE=(1,1,1)
head=extract_head(Image.open(a.SHEET))
head_source=head
head=head.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
# 'COOK'D' appears in the seated apron itself, small and hand-drawn.
label=a.art('seated').crop((244,278,300,295)).convert('RGBA')
arr=np.array(label); arr[:,:,3]=255-np.minimum(255,np.maximum(0,arr[:,:,0].astype(float)-32)*1.15).astype('uint8')
arr[:,:,:3]=[26,36,76];LABEL=Image.fromarray(arr)

def raster(im):
    buf=BytesIO();im.save(buf,format='PNG');buf.seek(0)
    return cairo.ImageSurface.create_from_png(buf)
HEAD=raster(head); LOGO=raster(LABEL)
def img(ctx,layer,x,y,w,h,angle=0,ax=.5,ay=.5):
    ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.scale(w/layer.get_width(),h/layer.get_height())
    ctx.set_source_surface(layer,-ax*layer.get_width(),-ay*layer.get_height());ctx.paint();ctx.restore()
def path(ctx,instructions,fill=WHITE,lw=1.95):
    ctx.new_path()
    for cmd,*val in instructions:
        if cmd=='M':ctx.move_to(*val)
        elif cmd=='C':ctx.curve_to(*val)
        elif cmd=='L':ctx.line_to(*val)
        elif cmd=='Z':ctx.close_path()
    if fill is not None:
        ctx.set_source_rgb(*fill);ctx.fill_preserve()
    ctx.set_line_width(lw);ctx.set_source_rgb(*C);ctx.stroke()
def silk(ctx,points,widths,line=1.95):
    """Ink anatomy follows an individually profiled thigh, shin, elbow and toe."""
    points=np.array(points,float); axis=np.arange(len(points))
    f=CubicSpline(axis,points,bc_type='natural')
    t=np.linspace(0,len(points)-1,45)
    spine=f(t)
    radii=np.interp(t,axis,widths)*.5
    # Paint one continuous ink outline, even when the heel folds up against the shin.
    # The width profile changes along each limb to retain shoulder, knee, heel and toes.
    for colour,extra in [(C,line*.5),(WHITE,0)]:
        ctx.new_path()
        for (x,y),r in zip(spine,radii):
            ctx.new_sub_path();ctx.arc(x,y,max(.48,r+extra),0,a.TAU)
        ctx.set_source_rgb(*colour);ctx.fill()
def gait(p):
    p=p%1
    if p<.54:
        # heel catches, sole rolls level, then the toe stays on the floor as heel rises.
        v=p/.54
        return 155-60*v,218-1.4*math.sin(math.pi*v), -7*(1-a.step(0,.22,v))+15*a.step(.66,1,v)
    v=(p-.54)/.46
    return 95+60*a.ease(v),218-21*math.sin(math.pi*v)**.9, 15*(1-v)-10*v-26*math.sin(math.pi*v)
def leg(ctx,hip,x,y,angle,front,drive):
    hx,hy=hip
    heel=np.array([x-3,y-3]);dx,dy=heel-[hx,hy]
    # The knee leads both the planted and returning paw; the rear heel folds under the apron.
    knee=np.array([(hx+x)*.5+7+13*drive,(hy+y)*.5-1-5*drive])
    thigh_mid=(np.array([hx,hy])+knee)/2+[.5,0]
    calf=(knee+heel)/2+[-1.8,-.5]
    rad=math.radians(angle)
    e=np.array([math.cos(rad),math.sin(rad)])
    toe=heel+e*10+np.array([0,2])
    silk(ctx,[(hx,hy),thigh_mid,knee,calf,heel,heel+e*5+[-.1,2],toe],[16,15.8,14,12.3,10.2,9.1,.5],1.9)
def tail(ctx,xx,yy,beat):
    ctx.save();ctx.translate(xx,yy)
    # Bagel's long, tapered tail, curled exactly like the right edge of the source.
    path(ctx,[('M',103,176),('C',92,183,81,184,74,177),('C',70,173,67,168,63,168+beat),
              ('C',59,169+beat,57,166+beat,59,162+beat),('C',61,156+beat,67,155+beat,73,160+beat),
              ('C',81,171,87,170,99,162),('Z',)],lw=2)
    ctx.restore()
def body(ctx,shift,drop,lean):
    ctx.save();ctx.translate(shift,drop);ctx.translate(119,172);ctx.rotate(lean);ctx.translate(-119,-172)
    path(ctx,[('M',108,119),('C',117,116,127,119,137,126),
              ('C',144,133,147,148,143,168),('C',140,182,133,192,118,192),
              ('C',107,192,99,189,94,183),('C',90,173,93,159,96,145),('C',99,132,102,121,108,119),('Z',)])
    # The apron flares and wrinkles at the forward hip. Its upper edge is the drawn bib.
    path(ctx,[('M',108,124),('C',108,133,118,137,133,130),('C',134,127,135,125,136,123),
              ('C',141,123,142,132,143,136),('C',144,147,143,163,144,177),
              ('C',138,181,126,182,117,183),('C',105,183,99,181,91,181),
              ('L',96,156),('C',98,148,101,136,104,126),('Z',)],lw=1.95)
    path(ctx,[('M',96,178),('C',104,179,110,179,113,179)],None,.63)
    img(ctx,LOGO,120,147,23,7,-.05)
    ctx.restore()
def cup(ctx,x,y,theta):
    ctx.save();ctx.translate(x,y);ctx.rotate(theta)
    # A small takeaway cup scaled to Bagel's paw, with the double lip from its café illustration.
    path(ctx,[('M',-10.8,-8),('L',-8,10.2),('C',-4,12.9,5,13.2,8,10),('L',10.5,-8),
              ('C',7,-5,-6,-4,-10.8,-8),('Z',)],lw=1.65)
    path(ctx,[('M',-10.7,-8.5),('C',-10,-12,8,-12,10.6,-8.7),
              ('C',12,-5.4,-7,-4,-10.6,-7.4),('Z',)],lw=1.55)
    path(ctx,[('M',-8,2.4),('C',-3,4.3,5.5,4.8,8.5,1.7)],None,.9)
    ctx.restore()
def map_item(ctx,x,y,theta):
    ctx.save();ctx.translate(x,y);ctx.rotate(theta)
    path(ctx,[('M',-13,-8),('L',-5,-5),('L',2,-10),('L',12,-6),('L',11,8),
              ('L',3,5),('L',-5,10),('L',-14,6),('Z',)],lw=1.4)
    path(ctx,[('M',-5,-4),('L',-5,7),('M',2,-8),('L',3,3)],None,.8)
    path(ctx,[('M',-10,3),('C',-8,-4,-3,6,-1,1),('C',1,-5,5,0,8,-2)],None,.9)
    ctx.restore()

def runner(t,mode):
    drinking=(mode=='sip')
    if drinking:
        # Jog, gather the rear foot, tip the cup, pause for a sip, then push off.
        if t<.5:
            phase=t*2
            still=1-a.step(0,.095,t)
        else:
            phase=0
            still=a.step(.50,.63,t)
        raise_cup=a.keyed(t,[(0,.045),(.12,.025),(.49,.025),(.56,.16),(.65,.88),(.705,1),(.79,1),(.855,.91),(.92,.31),(1,.045)])
    else:
        phase=t;still=0;raise_cup=0
    p=phase%1; b=math.sin(2*math.pi*p); bounce=-4.6*math.sin(2*math.pi*p)**2
    breath=(1.2*math.sin(2*math.pi*t) if drinking else 0)
    dy=(1-still)*bounce+still*2+breath
    dx=(1-still)*2*math.sin(a.TAU*p)
    lean=(1-still)*.2+still*(-.015-.025*raise_cup)
    # As Bagel settles, the back heel returns underneath its own hip; at rest both feet are grounded.
    def foot(k):
        x,y,ang=gait(p+k*.5)
        targetx=138 if k==0 else 110
        return x*(1-still)+targetx*still,y*(1-still)+219*still,ang*(1-still),max(0,math.sin(a.TAU*(p+k*.5-.52)))*(1-still)
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,SIZE*2,SIZE*2);ctx=cairo.Context(surface);ctx.scale(2,2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND);ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    tail(ctx,dx,dy,5*b*(1-still)+1.5*math.sin(a.TAU*t))
    far=foot(1);near=foot(0)
    leg(ctx,(112+dx,180+dy),*far[:3],False,far[3])
    leg(ctx,(127+dx,181+dy),*near[:3],True,near[3])
    arm_swing=math.sin(a.TAU*p-.35)*(1-still)
    # Far wrist swings in opposition to the lead leg, largely behind the apron and head.
    silk(ctx,[(128+dx,137+dy),(123+dx-5*arm_swing,148+dy),
              (118+dx-12*arm_swing,156+dy),(109+dx-13*arm_swing,151+dy),
              (104+dx-14*arm_swing,147+dy)], [14.8,13.6,11,9.6,1],1.75)
    body(ctx,dx,dy,lean)
    headx=129+dx+lean*24; heady=106+dy
    headangle=.037+.09*(1-still)+.035*b*(1-still)-.055*raise_cup
    iw,ih=143,128
    # Track the actual source mouth in the mirrored raster. This is the exact point
    # that the top rim of the cup must meet during a sip.
    u=(246-138)/246*iw - iw*.5;v=172/218*ih-ih*.65
    mouthx=headx+u*math.cos(headangle)-v*math.sin(headangle)
    mouthy=heady+u*math.sin(headangle)+v*math.cos(headangle)
    if mode in ('sip','sip-run'):
        cx=(157+dx+4*arm_swing)*(1-raise_cup)+(mouthx+1.5)*raise_cup
        cy=(157+dy-1*arm_swing)*(1-raise_cup)+(mouthy+8.5)*raise_cup
    elif mode=='route':
        cx=150+dx+5*arm_swing;cy=148+dy+3*arm_swing
    # Ears share the same original contour as the café's character portrait.
    if drinking:
        # Bagel blinks once as the coffee reaches the muzzle, with its ears settling
        # from the last step while both legs remain planted.
        blink=max(0, 1-abs(t-.751)/.055) * .93
        portrait=swaying_head(head_source,a.TAU*t,.38,blink).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        img(ctx,raster(portrait),headx,heady,iw,ih,headangle,.5,.65)
    else:
        img(ctx,HEAD,headx,heady,iw,ih,headangle,.5,.65)
    if mode in ('sip','sip-run','route'):
        ex=124+dx+6*arm_swing+(cx-150)*.2
        ey=164+dy-raise_cup*14
        wx,wy=cx-6.7,cy+5.1
        silk(ctx,[(115+dx,140+dy),(116+dx,151+dy),(ex,ey),
                  ((ex+wx)*.50,(ey+wy)*.5+1.6),(wx,wy),(wx+4.5,wy-1.4)],
             [15.2,14.8,13.3,11.7,12,.5],1.85)
        if mode in ('sip','sip-run'): cup(ctx,cx,cy,-.07*arm_swing-.29*raise_cup)
        else: map_item(ctx,cx,cy,-.09-.10*arm_swing)
        # Paw wraps across the near wall of the held object, fingers following its rim.
        path(ctx,[('M',wx-4,wy-3.4),('C',wx-.8,wy-5.2,wx+1.8,wy-5.8,wx+4.6,wy-4.5),
                 ('C',wx+6,wy-3.3,wx+3.5,wy-1.8,wx+4.6,wy-.6),
                 ('C',wx+6,wy+.4,wx+4,wy+2.3,wx+1.9,wy+2.7),
                 ('C',wx+.1,wy+4.2,wx-3.8,wy+4.1,wx-5,wy+2.1)],WHITE,1.15)
    else:
        ex=120+dx+9*arm_swing;ey=160+dy
        wx=133+dx+14*arm_swing;wy=150+dy-4*arm_swing
        silk(ctx,[(113+dx,139+dy),(114+dx,149+dy),(ex,ey),((ex+wx)*.5,(ey+wy)*.5+1),
                  (wx,wy),(wx+3,wy-4),(wx+5,wy-4.5)], [15,15.4,13.5,11.3,10.5,8,.6],1.85)
    buf=BytesIO();surface.write_to_png(buf);buf.seek(0);im=Image.open(buf).convert('RGBA')
    matte=im.getchannel('A').filter(ImageFilter.MaxFilter(15))
    out=Image.new('RGBA',im.size,'white');out.putalpha(matte);out.alpha_composite(im)
    return out.resize((SIZE,SIZE),a.R)
if __name__=='__main__':
    actions={name:(lambda t,n=name: runner(t,n)) for name in ('run','route','sip','sip-run')}
    if '--proof' in sys.argv:
        a.proof(list(actions.items()),a.QA/'coffee-run-proof.jpg')
    else:
        for action,fn in actions.items():
            if len(sys.argv)==1 or action in sys.argv:a.save(action,fn)
