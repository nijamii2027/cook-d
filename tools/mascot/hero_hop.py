"""Register the café's two-eyed coffee runner to the five hero-letter landings.

The requested reference is the published sip.webp frame 7, unmirrored. Use
that coffee performance directly, with no new face, limbs, cup, or costume.
Only the small away-facing turn needs a rear drawing; it uses the same head,
apron, tail, foot and cup rig. Running this file updates only the hero assets.
"""
from functools import lru_cache
from io import BytesIO
import json
import math

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from scipy import ndimage
from scipy.interpolate import PchipInterpolator

import climbing as c
import coffee_run as run

SIZE,COUNT=c.SIZE,c.FRAMES
SOLE=c.v(172,216)
ZOOM=.74
R=Image.Resampling.BICUBIC
PHASE=PchipInterpolator([0,7,14,22,26,31,37,43,47],
                        [0,.055,.165,.265,7/24,.245,.125,.031,.00045])
CROUCH=PchipInterpolator([0,7,11,14,20,26,33,37,41,47],
                         [0,6.2,4.6,0,-3.,-5.,-2.5,0,5.6,0])


@lru_cache(maxsize=1)
def reference():
    """The single source drawing actually shown by the client."""
    with Image.open(c.DEST/'sip.webp') as atlas:
        return atlas.convert('RGBA').crop((7*256,0,8*256,256))


def active_sole(image,phase):
    # The supporting curved toe has a distinct navy bottom edge. Register that
    # actual ink, after rendering; the extra white sticker border is not a foot.
    x=run.gait(phase)[0]
    a=np.asarray(image)
    yy,xx=np.indices(a.shape[:2])
    ink=(a[:,:,0]<130)&(a[:,:,3]>170)&(yy>185)&(np.abs(xx-x)<16)
    y=int(yy[ink].max())
    edge=ink&(yy==y)
    return c.v(float(xx[edge].mean()),y-.8)


def place(im,source,dest,zoom=ZOOM):
    frame=im.transform((SIZE,SIZE),Image.Transform.AFFINE,
            (1/zoom,0,source[0]-dest[0]/zoom,
             0,1/zoom,source[1]-dest[1]/zoom),R)
    # Browser downsampling can leave the middle of the opaque white paper at
    # 254. Consolidate only those essentially opaque pixels, preserving edges.
    frame.putalpha(frame.getchannel('A').point(lambda v:255 if v>=253 else v))
    return frame


def compress(im,dy):
    if abs(dy)<.001:
        return im
    a=np.asarray(im)
    yy,xx=np.indices(a.shape[:2],dtype=np.float32)
    # The bottom of the sole stays on the support. The entire face, hat and cup
    # remain a single rigid drawing as the hip flexes through the landing.
    fade=np.clip((219-yy)/35,0,1)
    fade=fade*fade*(3-2*fade)
    y=yy-dy*fade
    rgba=[ndimage.map_coordinates(a[:,:,i],[y,xx],order=1,mode='constant',
              cval=0 if i==3 else 255) for i in range(4)]
    return Image.fromarray(np.stack(rgba,axis=-1))


def details(image,anchor,sole,grounded,eyes):
    normalize=lambda p:[round(float(n)/SIZE,7) for n in p]
    return {'anchor':normalize(anchor),'sole':normalize(sole),'center':c.center(image),
            'bounds':normalize(image.getbbox()),'grounded':bool(grounded),'visibleEyes':int(eyes)}


def hop(i):
    phase=float(PHASE(i))
    im=reference() if i==26 else run.runner(phase,'sip-run')
    # The literal matching drawing forms the centre of the flight, with no
    # optical squash, redrawn extremities or camera-facing reaction at the apex.
    dy=float(CROUCH(i))
    im=compress(im,max(0,dy))
    ground=i<=14 or i>=37
    foot=active_sole(im,phase)
    # In flight the rear heel tucks as the forward foot reaches for the next
    # ledge. The second half opens that same stagger into its landing stance,
    # so the supporting toe is continuous through the next push or pivot.
    dest=SOLE if ground else SOLE+c.v(0,min(0,dy))
    frame=place(im,foot,dest)
    return frame,details(frame,SOLE,dest,ground,2)



@lru_cache(maxsize=1)
def rear_head():
    """The original skull, crown and ears, behind the coffee runner's face."""
    src=np.asarray(run.head).copy()
    yy,xx=np.indices(src.shape[:2])
    face=((xx>82)&(xx<169)&(yy>102)&(yy<187))
    src[face,:3]=255
    return Image.fromarray(src)


def side_to_back(amount,side):
    """A single stroke stays attached to each ear, crown lobe and facial mark.

    Shift each horizontal scanline about its actual pigment centre as the head
    changes flanks. At the back the source contour is symmetric and can change
    handedness on the next frame without a duplicate hat or a translucent face.
    """
    if amount<.0001:
        return run.head if side>0 else ImageOps.mirror(run.head)
    base=np.asarray(rear_head())
    h,w=base.shape[:2]
    yy,xx=np.indices((h,w),dtype=np.float32)
    src=np.asarray(run.head)
    keep=(xx>82)&(xx<169)&(yy>102)&(yy<187)
    pigment=np.where(keep,255-src[:,:,0],0).astype(float)
    width=1-.39*amount
    source_x=(xx-124-79*amount)/width+124
    face=ndimage.map_coordinates(pigment,[yy,source_x],order=1,mode='constant',cval=0)
    # The cheek conceals the eyes, muzzle and mouth in succession as the nose
    # goes round the far side. The printed ears stay in front of those features.
    boundary=180-116*amount
    face*=np.clip((boundary-xx+2)/4.,0,1)
    imprint=base.copy()
    for j,ink in enumerate((26,35,77)):
        imprint[:,:,j]=np.minimum(imprint[:,:,j],np.uint8(np.clip(255-(255-ink)*face/230.,0,255)))
    edges=base[:,:,3]>130
    ymid=np.full(h,(w-1)/2)
    for y,row in enumerate(edges):
        if row.any():
            x=np.where(row)[0]
            ymid[y]=(x.min()+x.max())*.5
    center=(w-1)/2.
    shift=ndimage.gaussian_filter1d(center-ymid,.8)
    dx=xx-amount*shift[:,None]
    img=np.stack([ndimage.map_coordinates(imprint[:,:,j],[yy,dx],order=1,
                     mode='constant',cval=0 if j==3 else 255) for j in range(4)],axis=-1)
    symmetry=float(c.ease((amount-.40)/.59))
    if symmetry:
        # Align both halves on the actual contour centre. The front half of the
        # hat is its own stroke; it never appears twice as it rolls around.
        right=xx>center
        mirrored=img[:,::-1,:]
        selected=np.where(right[:,:,None],mirrored,img)
        # Follow the source's own irregular stroke under this interpolation.
        # Once the back is reached each side is pixel-identical to the other.
        img=np.uint8(img*(1-symmetry)+selected*symmetry)
    out=Image.fromarray(img)
    return out if side>0 else ImageOps.mirror(out)


def setup_source(i):
    """Use the same native gait, ankle, knee and leaning apron as frame zero."""
    phase=float(c.ease(i/47))
    yaw=math.cos(math.pi*phase)
    rear=1-abs(yaw)
    anchor=SOLE.copy()
    anchor[0]=c.mix(SOLE[0],SIZE-SOLE[0],phase)
    return phase,yaw,rear,anchor


@lru_cache(maxsize=1)
def standing_sole():
    return active_sole(run.runner(0,'sip-run'),0)


def turn_source(i):
    phase,yaw,rear,anchor=setup_source(i)
    side=1 if yaw>=0 else -1
    weight=abs(yaw)
    bend=math.sin(math.pi*phase)**2
    surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,512,512)
    ctx=cairo.Context(surf);ctx.scale(2,2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND);ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    # Work in runner coordinates centred on its right planted toe. The outer
    # placement translates this toe continuously between the registered ends.
    p=standing_sole().copy()
    ctx.translate(*p)
    def project(x,y,neutral):
        return ((x-p[0])*yaw+(1-weight)*neutral[0],(y-p[1])*weight+(1-weight)*neutral[1])
    torso=c.v(*project(119,172,(-4,-43)))+c.v(0,3.1*bend)
    def leg(name,hip,e,neutralhip,neutralend):
        root=c.v(*project(*hip,neutralhip))+c.v(0,3.1*bend)
        x,y,angle=run.gait(e)
        # Add the opposite-handed swing around the planted paw. A distinct
        # trailing toe lifts and plants after it passes the apron hem.
        pad=c.v(*project(x,y,neutralend))
        if name=='back': pad+=c.v(0,-6.4*bend)
        ctx.save();ctx.translate(*root);ctx.scale(side,1)
        target=(pad-root)*c.v(side,1)
        run.leg(ctx,(0,0),*target,angle*weight,name=='front',0)
        ctx.restore()
    ctx.save();ctx.translate(*torso);ctx.scale(side*(.18+.82*weight),1)
    ctx.translate(-119,-172)
    run.tail(ctx,0,0,1.9*bend)
    ctx.restore()
    leg('back',(112,180),.5,(-13,-36),(-12,-3))
    leg('front',(127,181),0,(6,-36),(0,-3))
    ctx.save();ctx.translate(*torso);ctx.scale(side*(.85+.15*weight),1)
    ctx.translate(-119,-172)
    run.body(ctx,0,0,.2*weight)
    if rear>0:
        # The turned back is the apron fabric; the front wordmark passes out
        # of sight. Draw only at its original bounds on the existing apron.
        ctx.save();ctx.translate(119,172);ctx.rotate(.2*weight);ctx.translate(-119,-172)
        ctx.rectangle(107,141,27,12);ctx.set_source_rgba(1,1,1,float(c.ease(rear/.48)));ctx.fill();ctx.restore()
    ctx.restore()
    arm0=math.sin(-.35)
    cupx=157+4*arm0;cupy=157-arm0
    end=c.v(*project(cupx,cupy,(16,-57)))+c.v(0,2*bend)
    def hand():
        ctx.save();ctx.translate(*end);ctx.scale(side*(1-.14*rear),1)
        run.cup(ctx,0,0,-.07*arm0*weight)
        ctx.restore()
    def arm():
        ex=124+6*arm0+(cupx-150)*.2
        ey=164
        path=[(115,140),(116,151),(ex,ey),((ex+cupx-6.7)*.5,(ey+cupy+5.1)*.5+1.6),
                 (cupx-6.7,cupy+5.1),(cupx-2.2,cupy+3.7)]
        targets=[(-11,-71),(-12,-62),(-8,-50),(1,-49),(10,-52),(14,-53)]
        pts=[c.v(*project(*pt,t))+c.v(0,3.1*bend) for pt,t in zip(path,targets)]
        run.silk(ctx,pts,[15.2,14.8,13.3,11.7,12,.5],1.85)
        hand()
        ctx.save();ctx.translate(*end);ctx.scale(side,1)
        run.path(ctx,[('M',-10.7,1.7),('C',-7.5,-.1,-4.9,-.7,-2.1,.6),
             ('C',-.7,1.8,-3.2,3.3,-2.1,4.5),('C',-.7,5.5,-2.7,7.4,-4.8,7.8),
             ('C',-6.6,9.3,-10.5,9.2,-11.7,7.2)],run.WHITE,1.15)
        ctx.restore()
    # Cup stays on the same side of the moving body. It goes behind the torso
    # as the runner pivots away, then becomes visible on the opposite flank.
    headpoint=c.v(*project(133.8,106,(-3,-112)))+c.v(0,3.1*bend)
    head=run.raster(side_to_back(rear,side))
    run.img(ctx,head,*headpoint,143*(1-.075*rear),128,.127*yaw,.5,.65)
    # As the body swings away the cup passes behind the actual apron edge.
    # A moving occlusion hides it while preserving solid white paint and nib.
    ctx.save()
    if rear>.35:
        ctx.scale(side,1)
        edge=c.mix(-200.,100.,float(c.ease((rear-.35)/.61)))
        ctx.rectangle(edge,-230,256,280)
        ctx.clip()
        ctx.scale(side,1)
    arm()
    ctx.restore()
    stream=BytesIO();surf.write_to_png(stream);stream.seek(0)
    im=Image.open(stream).convert('RGBA')
    sticker=Image.new('RGBA',im.size,'white');sticker.putalpha(im.getchannel('A').filter(ImageFilter.MaxFilter(15)))
    sticker.alpha_composite(im)
    return sticker.resize((256,256),Image.Resampling.LANCZOS),anchor,p


def turn(i,standing):
    _,yaw,rear,anchor=setup_source(i)
    if i==0 or i==47:
        out=standing if i==0 else ImageOps.mirror(standing)
    else:
        im,anchor,p=turn_source(i)
        # Measure the nontransparent dark supporting edge after ankle rotation.
        # The static p is the transition pin; the live support is the real toe.
        a=np.asarray(im);yy,xx=np.indices(a.shape[:2])
        m=(a[:,:,0]<150)&(a[:,:,3]>130)&(yy>208)&(np.abs(xx-p[0])<10)
        if m.any():
            y=int(yy[m].max());p=c.v(float(xx[m&(yy==y)].mean()),y-.8)
        out=place(im,p,anchor)
    return out,details(out,anchor,anchor,True,2 if rear<.45 else 1 if rear<.70 else 0)


def main():
    hops,data=zip(*(hop(i) for i in range(COUNT)))
    turns,turn_data=zip(*(turn(i,hops[0]) for i in range(COUNT)))
    packs={'hop':(hops,data,1.28),'hop-turn':(turns,turn_data,1.18)}
    metadata={'version':1,'frameSize':[SIZE,SIZE],'grid':[8,6],
              'takeoffFrame':14,'landingFrame':37,'actions':{}}
    for name,(frames,info,seconds) in packs.items():
        c.pack(name,frames)
        metadata['actions'][name]={'durationSeconds':seconds,'frames':info}
    assert turns[0].tobytes()==hops[0].tobytes()
    assert turns[-1].tobytes()==ImageOps.mirror(hops[0]).tobytes()
    (c.DEST/'hop.json').write_text(json.dumps(metadata,separators=(',',':'))+'\n')


if __name__=='__main__':
    main()
