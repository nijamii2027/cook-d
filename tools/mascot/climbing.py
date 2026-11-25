"""Animate the café's original round Bagel portrait and four short climbing limbs.

Each exported support point belongs to an actual drawn toe. The 48-frame reaches
use the same travel as the planting track: 34 px up a wall, 38 px across a lip.
Run with Debian Python, Pillow, NumPy, SciPy and Pycairo.
"""
from io import BytesIO
from pathlib import Path
import json
import math

import cairo
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from scipy.interpolate import PchipInterpolator

from original_portrait import NAVY, cutout, prepared_ink

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'dist/media/mascot'
SOURCE = ROOT / 'dist/media/original/assets/customer/bagel-sticker-sheet.png'
SIZE, FRAMES = 288, 48
INK = (24/255,33/255,76/255)
WHITE = (1.,1.,1.)
TAU = math.tau
NAMES = ('handFront','handBack','footFront','footBack')
TRAVEL = {'climb':34.,'traverse':38.}
END_PAW = (197.,151.)


def v(x,y):
    return np.array((x,y),float)


def mix(a,b,t):
    return (1-t)*a + t*b


def ease(t):
    t = np.clip(t,0,1)
    return t*t*(3-2*t)


def unit(a):
    return a/max(np.linalg.norm(a),.0001)


def perp(a):
    return v(-a[1],a[0])


def at_body(body,angle,offset):
    x,y=offset
    cs,sn=math.cos(angle),math.sin(angle)
    return body+v(cs*x-sn*y,sn*x+cs*y)


def atlas_head():
    with Image.open(SOURCE) as sheet:
        return cutout(prepared_ink(sheet.crop((590,840,1070,1250))))


def surface(image):
    out=BytesIO()
    image.save(out,format='PNG')
    out.seek(0)
    return cairo.ImageSurface.create_from_png(out)


def outline(ctx,points,weight=2.8,fill=WHITE,loop=True,tension=.75,*,stroke=INK):
    points=np.asarray(points,float)
    n=len(points)
    ctx.new_path()
    ctx.move_to(*points[0])
    for i in range(n if loop else n-1):
        p,q=points[i],points[(i+1)%n]
        before=points[i-1] if i or loop else p
        after=points[(i+2)%n] if i+2<n or loop else q
        ctx.curve_to(*(p+(q-before)*tension/6),*(q-(after-p)*tension/6),*q)
    if loop:
        ctx.close_path()
    if fill is not None:
        ctx.set_source_rgb(*fill)
        ctx.fill_preserve()
    ctx.set_source_rgb(*stroke)
    ctx.set_line_width(weight)
    ctx.stroke()


def shape(ctx,points,width=2.4,fill=WHITE,closed=True):
    outline(ctx,points,width,fill,closed,.834,stroke=NAVY)


def canvas():
    target=cairo.ImageSurface(cairo.FORMAT_ARGB32,SIZE*2,SIZE*2)
    ctx=cairo.Context(target)
    ctx.scale(2,2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    return target,ctx


def finish(target):
    data=BytesIO()
    target.write_to_png(data)
    data.seek(0)
    art=Image.open(data).convert('RGBA')
    sticker=Image.new('RGBA',art.size,'white')
    sticker.putalpha(art.getchannel('A').filter(ImageFilter.MaxFilter(13)))
    sticker.alpha_composite(art)
    return sticker.resize((SIZE,SIZE),Image.Resampling.LANCZOS)


def center(image):
    alpha=np.asarray(image.getchannel('A'),float)
    y,x=np.indices(alpha.shape)+.5
    return [round(float((alpha*q).sum()/alpha.sum()/SIZE),7) for q in (x,y)]


def leg(ctx,root,end,tip,fold,hand,near,hooked=False):
    """One short bent limb with a broad teardrop paw and two unequal toe lobes."""
    direction=unit(tip)
    perp_tip=perp(direction)
    wrist=end-direction*(12 if hooked else 9 if hand else 10)
    span=wrist-root
    length=np.linalg.norm(span)
    axis=unit(span)
    elbow=mix(root,wrist,.47)+perp(axis)*fold*min(8.,3.6+.13*length)
    width=1 if near else .92
    # Draw all the overlapping pads in a mask before inking. Even at the tightest
    # bend the ankle remains one furry contour with no internal black rings.
    samples=[]
    for t in np.linspace(0,1,45):
        pt=(1-t)**2*root+2*(1-t)*t*elbow+t*t*wrist
        radius=((1-t)*(8.1 if hand else 9.3)+t*5.8)*width
        samples.append((pt,radius))
    for t in np.linspace(0,1,16):
        samples.append((mix(wrist,end-direction*4.8,t),mix(5.65,6.,t)*width))
    samples.extend([(end-direction*3.55+perp_tip*.72,3.95*width),
                    (end-direction*4.5-perp_tip*2.32,3.43*width)])
    if hooked:
        samples.extend([(wrist+perp_tip*1.2,6.35*width),
                        (end-direction*3.3+perp_tip*2.65,3.9*width),
                        (end-direction*4.7-perp_tip*2.40,3.65*width)])
    low=np.floor(np.min([p-r-2 for p,r in samples],axis=0))
    hi=np.ceil(np.max([p+r+2 for p,r in samples],axis=0))
    scale=3
    w,h=np.int32((hi-low)*scale)
    yy,xx=np.indices((h,w),dtype=float)
    xx=xx/scale+low[0]
    yy=yy/scale+low[1]
    mask=np.zeros((h,w),bool)
    for point,radius in samples:
        mask|=(xx-point[0])**2+(yy-point[1])**2<=radius**2
    dist=ndimage.distance_transform_edt(mask)/scale
    inside=np.clip((dist-(2.15 if near else 1.95))*scale+.5,0,1)
    rgba=np.uint8(np.stack([*(255*(q+(1-q)*inside) for q in NAVY),255*mask],axis=-1))
    ctx.save()
    ctx.translate(*low)
    ctx.scale(1/scale,1/scale)
    ctx.set_source_surface(surface(Image.fromarray(rgba)))
    ctx.paint()
    ctx.restore()
    if near:
        p=end-direction*2.9-perp_tip*1.35
        if hooked:
            shape(ctx,[end-direction*1.6-perp_tip*.5,end-direction*2.8-perp_tip*.36,
                       end-direction*4.65-perp_tip*.88],1.26,None,False)
        else:
            shape(ctx,[p,p-direction*.85+perp_tip*.5,p-direction*2.05+perp_tip*.55],1.03,None,False)


def torso(ctx,body,angle,wag,lift,front=0):
    """The apron wraps a pear-shaped body; its hem ends above the ankle."""
    ctx.save()
    ctx.translate(*body)
    ctx.rotate(angle)
    ctx.save()
    ctx.scale(max(.06,1-front),1)
    ctx.translate(0,6.2)
    tail=[(-16,7),(-23,10),(-32,8+wag*.38),(-38,3+wag*.7),
          (-40,-1+wag),(-39,-4+wag),(-36,-4+wag),(-33,0+wag*.83),
          (-28,3+wag*.5),(-22,3+wag*.17),(-18,-1)]
    shape(ctx,tail,2.22)
    ctx.restore()
    side_body=[(-16,-15),(-6,-21),(9,-21),(20,-15),(25,-6),(24,5),
               (20,13),(12,19),(-1,22),(-14,20),(-21,15),(-25,6),(-24,-4)]
    front_body=[(-16,-16),(-6,-21),(6,-21),(16,-16),(23,-7),(24,4),
                (20,13),(12,19),(0,21),(-12,19),(-20,13),(-24,4),(-23,-7)]
    shape(ctx,mix(np.array(side_body),np.array(front_body),front),2.45)
    side=[(-16,-15),(-13,-8),(-7,-4),(2,-4),(10,-10),(13,-16),(19,-14),
          (20,-9),(16,-2),(17,8),(21,15),(11,18),(0,19),(-13,17-lift),(-23,12-lift),
          (-21,6),(-20,-1),(-21,-12)]
    fore=[(-17,-15),(-14,-9),(-9,-5),(1,-3),(10,-6),(14,-15),(19,-14),
          (19,-8),(16,-2),(18,7),(20,15),(11,17),(0,18),(-12,17),(-20,15),
          (-17,7),(-17,-1),(-20,-12)]
    shape(ctx,mix(np.array(side),np.array(fore),front),2.22)
    shape(ctx,[(-3,3),(2,3.5),(7,2.7),(7,6),(6,9),(3,10),(-1,9),(-2,6)],1.2,None,False)
    if front < .93:
        ctx.save()
        ctx.translate(-19,0)
        ctx.scale(1-front,1)
        shape(ctx,[(-1,1),(-6,4),(-10,4),(-8,1),(-3,-1)],1.55)
        ctx.restore()
    ctx.restore()


def path(keys):
    time,values=zip(*keys)
    return PchipInterpolator(time,np.array(values),axis=0)


# The mantle moves the head first. A heel draws up under the hem as its forepaw
# stays on the shelf, then the chest rolls forward over the planted heel.
CREST_PATHS = {
    'body':path([(0,(165,179)),(.13,(166,180)),(.37,(171,162)),(.54,(181,150)),
                 (.68,(190,144)),(.83,(197,134)),(1,(203,122))]),
    'angle':path([(0,.11),(.13,.14),(.46,.30),(.65,.37),(.84,.18),(1,.025)]),
    'handFront':path([(0,END_PAW),(.74,END_PAW),(.86,(202,137)),(1,(219,131))]),
    'handBack':path([(0,(193,158)),(.11,(196,148)),(.25,(207,151)),
                     (.80,(207,151)),(.94,(219,132)),(1,(222,130))]),
    'footFront':path([(0,(192,205)),(.20,(192,205)),(.40,(182,187)),
                      (.54,(187,163)),(.65,END_PAW),(1,END_PAW)]),
    'footBack':path([(0,(193,214)),(.28,(193,214)),(.46,(182,190)),
                     (.65,(181,174)),(.82,(195,161)),(.93,(214,151)),(1,(214,151))])
}


def reach(t,offset,base,mode,foot):
    phase=(t+offset)%1
    support=.64 if foot else .65
    swing=max(0,(phase-support)/(1-support))
    displacement=TRAVEL[mode]*(phase-support/2-ease(swing))
    curl=math.sin(math.pi*swing)**2
    if mode=='climb':
        return base+v(-curl*(9 if foot else 6),displacement-curl*1.4),phase<=support
    return base+v(-displacement,curl*7.5),phase<=support


def pose(mode,t):
    wave=t*TAU
    if mode=='crest':
        channels={name:fn(t) for name,fn in CREST_PATHS.items()}
        grip=(['handFront'] if t<=.74 else [])+(['handBack'] if .25<=t<=.80 else [])
        grip+=(['footFront'] if t<=.20 or t>=.65 else [])+(['footBack'] if t<=.28 or t>=.93 else [])
        return channels['body'],float(channels['angle']),{k:channels[k] for k in NAMES},grip,'handFront' if t<=.74 else 'footFront'
    if mode=='climb':
        body=v(165+1.55*math.sin(2*wave-.48),169+2.1*math.cos(2*wave-.48))
        tilt=.115+.048*math.sin(wave-.3)
        bases=[(198,145),(198,145),(197,190),(197,190)]
    else:
        body=v(163+2.85*math.sin(wave-.37),161+1.65*math.cos(wave*2))
        tilt=-.08+.061*math.sin(wave-.3)
        bases=[(191.5,127),(191.5,127),(173,190),(153,189)]
        if mode=='hang':
            bases[:2]=[(198,127),(184,127)]
    paws,grip={},[]
    for i,name in enumerate(NAMES):
        if mode=='hang' or (mode=='traverse' and i>=2):
            p=v(*bases[i])
            grounded=i<2
            if not grounded:
                p+=v((5.0 if i==2 else -4.6)*math.sin(wave-.32),
                     (2.6 if i==2 else -2.3)*math.cos(wave-.24))
        else:
            p,grounded=reach(t,[0,.5,.54,.04][i],v(*bases[i]),mode,i>=2)
        paws[name]=p
        if grounded:
            grip.append(name)
    return body,tilt,paws,grip,'handFront' if 'handFront' in grip else 'handBack'


def roots(body,angle,front=0):
    side=[(13,-14),(18,-13),(0,13),(-9,14)]
    facing=[(-16,-12),(16,-12),(-10,13),(10,13)]
    return {n:at_body(body,angle,mix(np.array(a),np.array(b),front)) for n,a,b in zip(NAMES,side,facing)}


def paw_direction(mode,name,grip,t):
    if name.startswith('foot'):
        if name not in grip:
            return v(.55,.84)
        if mode=='climb' or (mode=='crest' and t<(.65 if name=='footFront' else .93)):
            return v(.94,-.13)
        return v(.36,.94)
    if name not in grip:
        return v(.58,.81) if mode=='crest' and t>.68 else v(.78,-.50)
    if mode=='climb':
        return v(.86,-.51)
    return v(.14,.99)


def head_position(mode,body,angle,t):
    if mode=='crest':
        offset=mix(v(-21,-23),v(-5,-23),ease(t))
        pitch=-.12+.11*ease(t)+.17*math.sin(math.pi*t)
    elif mode=='climb':
        offset=v(-22,-24)
        pitch=-.13+.041*math.sin(TAU*t-.32)
    else:
        offset=v(-23,-20)
        pitch=-.09+.043*math.sin(TAU*t-.45)
    return at_body(body,angle,offset),pitch


def paint_head(ctx,head,point,pitch,scale=.237):
    ctx.save()
    ctx.translate(*point)
    ctx.rotate(pitch)
    ctx.scale(scale,scale)
    ctx.set_source_surface(head,-248,-322)
    ctx.paint()
    ctx.restore()


def actor(ctx,mode,t,head,body,angle,paws,grip,front=0):
    r=roots(body,angle,front)
    def limb(name):
        hand=name.startswith('hand')
        near=name.endswith('Front')
        leg(ctx,r[name],paws[name],paw_direction(mode,name,grip,t),
            (1 if near else -.62) if hand else -.86,hand,near,
            hooked=hand and name in grip and mode!='climb')
    limb('footBack')
    limb('handBack')
    limb('footFront')
    torso(ctx,body,angle,3.2*math.sin(TAU*t-.5),1*math.cos(TAU*t),front)
    limb('handFront')
    point,pitch=head_position(mode,body,angle,t)
    paint_head(ctx,head,point,pitch)


def render(mode,i,head):
    t=i/(FRAMES-1 if mode=='crest' else FRAMES)
    body,angle,paws,grip,primary=pose(mode,t)
    target,ctx=canvas()
    actor(ctx,mode,t,head,body,angle,paws,grip)
    image=finish(target)
    contacts={k:[round(float(z)/SIZE,6) for z in p] for k,p in paws.items()}
    contacts.update(primary=primary,anchor=contacts[primary],grip=grip,center=center(image))
    return image,contacts


def pack(name,frames):
    grid=Image.new('RGBA',(8*SIZE,6*SIZE))
    assert len({frame.tobytes() for frame in frames})==FRAMES
    for i,im in enumerate(frames):
        bounds=im.getbbox()
        assert min(bounds[:2])>=3 and max(bounds[2:])<=SIZE-3,(name,i,bounds)
        grid.paste(im,(i%8*SIZE,i//8*SIZE))
    grid.save(DEST/(name+'.webp'),lossless=True,exact=True,method=4)
    frames[0].save(DEST/(name+'-still.webp'),lossless=True,exact=True,method=4)


def main():
    head=surface(atlas_head())
    data={'version':1,'frameSize':[SIZE,SIZE],'grid':[8,6],'actions':{}}
    for mode in ('climb','hang','traverse','crest'):
        frames,metadata=zip(*(render(mode,i,head) for i in range(FRAMES)))
        pack(mode,frames)
        data['actions'][mode]={'frames':metadata,'loop':mode!='crest','nominalTravel':round(TRAVEL.get(mode,0)/SIZE,6)}
    (DEST/'contacts.json').write_text(json.dumps(data,separators=(',',':'))+'\n')


if __name__=='__main__':
    main()
