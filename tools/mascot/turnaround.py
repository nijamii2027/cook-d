"""Turn Bagel on the final mantle's planted heel without flattening the portrait.

The cheek and eye correspondences come from the café's actual sticker. Its bone
hat is an independent cutout turning about the skull, preserving its white body
and navy contour even when it passes directly over the crown.
"""
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage
from scipy.spatial import Delaunay

import climbing as c
from original_portrait import cutout, prepared_ink

SIZE, COUNT = c.SIZE, c.FRAMES
PIVOT = c.v(*c.END_PAW)
WIDTH, HEIGHT = 497, 410
SAMPLE = 2


def head_layers():
    portrait=c.atlas_head()
    original=Image.new('RGBA',(WIDTH,HEIGHT),(255,255,255,0))
    original.alpha_composite(portrait)
    density=prepared_ink(original)
    # Reconnect the small section of forehead hidden by the base of the bone.
    bridge=[(300,118),(311,121),(321,125),(331,131),(340,136),(350,143),(358,149)]
    bone_mask=Image.new('L',original.size)
    pen=ImageDraw.Draw(bone_mask)
    pen.polygon([(313,121),(310,72),(331,44),(373,31),(400,45),(413,77),(410,113),
                 (378,112),(365,139),(356,148),(349,146),(337,139),(326,132)],fill=255)
    matte=np.asarray(bone_mask,dtype=float)/255
    skull=density*(1-matte)
    seam=Image.new('L',original.size)
    ImageDraw.Draw(seam).line(bridge,fill=250,width=6,joint='curve')
    face=cutout(np.maximum(skull,np.asarray(seam)/255))
    hat=cutout(density*matte)
    return original,face,hat


def image_planes(im):
    """Premultiplied ink and paper coverage at twice the final display density."""
    im=im.resize((249,205),Image.Resampling.LANCZOS)
    rgba=np.asarray(im,float)/255
    return np.stack([prepared_ink(im),rgba[:,:,3]],axis=0)


def rgba(planes):
    ink,alpha=np.clip(planes,0,1)
    data=np.stack([*(255*(1-(1-z)*ink/np.maximum(alpha,1e-6)) for z in c.NAVY),255*alpha],axis=-1)
    return Image.fromarray(np.uint8(data.clip(0,255)))


def correspondence():
    # Each pair follows the same feature on opposite cheeks. This lets a new
    # three-quarter position retain one set of eyes and one uninterrupted jaw.
    pairs=[
        ((42,321),(445,342)),((48,333),(439,350)),((62,325),(429,348)),
        ((67,345),(420,362)),((84,353),(401,368)),((99,345),(387,360)),
        ((105,326),(401,341)),((113,330),(389,341)),((127,327),(378,339)),
        ((130,344),(376,359)),((144,345),(365,351)),((150,356),(354,345)),
        ((170,363),(344,362)),((198,368),(322,365)),((222,369),(284,371)),
        ((51,291),(441,305)),((61,260),(435,267)),((77,229),(425,229)),
        ((97,205),(413,204)),((118,182),(393,181)),((142,166),(372,168)),
        ((149,149),(359,149)),((168,132),(341,135)),((192,121),(322,125)),
        ((220,112),(292,114)),
        ((170,224),(348,235)),((175,220),(343,226)),((182,213),(338,220)),
        ((193,207),(325,215)),((202,207),(314,217)),((212,216),(303,227)),
        ((217,230),(297,238)),((210,239),(303,247)),((196,244),(317,252)),
        ((181,239),(334,250)),((174,232),(344,245)),
        ((156,242),(353,255)),((134,258),(373,269)),((118,279),(389,293)),
        ((109,306),(398,316)),((235,273),(266,277)),((240,285),(260,288)),
        ((238,315),(261,315)),((245,324),(257,325)),
        ((0,0),(496,0)),((0,150),(496,150)),((0,270),(496,270)),((0,409),(496,409))]
    single=[(248,0),(251,109),(250,192),(250,265),(250,277),(250,288),
            (250,315),(250,326),(251,371),(248,409)]
    a,b=[],[]
    mirror=lambda p:(496-p[0],p[1])
    for left,right in pairs:
        a.extend((left,right))
        b.extend((mirror(right),mirror(left)))
    for p in single:
        a.append(p)
        b.append(mirror(p))
    return np.array(a,float)/SAMPLE,np.array(b,float)/SAMPLE


class TurningHead:
    def __init__(self):
        original,face,hat=head_layers()
        self.original=image_planes(original)
        self.face=image_planes(face)
        self.hat=image_planes(hat)
        self.a,self.b=correspondence()
        self.y,self.x=np.indices((205,249),dtype=float)
        self.points=np.stack([self.x.ravel(),self.y.ravel()],axis=1)

    @staticmethod
    def sample(layer,x,y):
        return np.stack([ndimage.map_coordinates(p,[y,x],order=1,mode='constant',cval=0)
                         for p in layer])

    def face_at(self,t):
        destination=c.mix(self.a,self.b,t)
        triangles=Delaunay(destination)
        idx=triangles.find_simplex(self.points)
        idx[idx<0]=0
        transform=triangles.transform[idx]
        uv=np.einsum('nij,nj->ni',transform[:,:2],self.points-transform[:,2])
        weights=np.column_stack([uv,1-uv.sum(axis=1)])
        labels=triangles.simplices[idx]
        def coords(src):
            pts=np.einsum('nk,nkd->nd',weights,src[labels])
            return (p.reshape(self.x.shape) for p in pts.T)
        xa,ya=coords(self.a)
        xb,yb=coords(self.b)
        right=self.sample(self.face,xa,ya)
        left=self.sample(self.face,248-xb,yb)
        return c.mix(right,left,c.ease((t-.23)/.54))

    def hat_at(self,t):
        base=c.v(c.mix(335.,161.,t),135.-24.7*math.sin(math.pi*t))/SAMPLE
        x,y=self.x-base[0],self.y-base[1]
        def rotated(src_x,ang,mirror=False):
            cs,sn=math.cos(ang),math.sin(ang)
            xx=src_x/SAMPLE+cs*x+sn*y
            yy=135/SAMPLE-sn*x+cs*y
            return self.sample(self.hat,248-xx if mirror else xx,yy)
        a=rotated(335,-1.13*t)
        b=rotated(161,1.13*(1-t),True)
        return c.mix(a,b,c.ease((t-.30)/.40))

    def image(self,t):
        skull=self.face_at(t)
        hat=self.hat_at(t)
        ink=hat[0]+skull[0]*(1-hat[1])
        alpha=hat[1]+skull[1]*(1-hat[1])
        complete=np.stack([ink,alpha])
        near=min(t,1-t)
        if near<.016:
            print_layer=self.original if t<.5 else self.original[:,:,::-1]
            complete=c.mix(print_layer,complete,c.ease(near/.016))
        return rgba(complete).resize((WIDTH,HEIGHT),Image.Resampling.BICUBIC)


def facing_point(side,neutral,yaw):
    return c.v(side[0]*yaw,side[1]*abs(yaw))+(1-abs(yaw))*np.array(neutral)


def one(i,last,head):
    if i==0:
        return last,PIVOT
    if i==COUNT-1:
        return ImageOps.mirror(last),c.v(SIZE-PIVOT[0],PIVOT[1])
    t=i/(COUNT-1)
    side_time=float(c.ease(t))
    yaw=math.cos(math.pi*side_time)
    front=1-abs(yaw)
    side=1 if yaw>=0 else -1
    scoop=math.sin(math.pi*t)**2
    anchor=c.v(c.mix(PIVOT[0],SIZE-PIVOT[0],side_time),PIVOT[1])
    body,side_angle,ends,grip,_=c.pose('crest',1.)
    r=c.roots(body,side_angle)
    body_offset=body-PIVOT
    body_shift=c.v(body_offset[0]*yaw,body_offset[1]+2.3*scoop)
    neutral_roots=[(-14,-13),(14,-13),(-6,13),(7,13)]
    roots={n:body_shift+facing_point(r[n]-body,o,yaw) for n,o in zip(c.NAMES,neutral_roots)}
    hands={n:facing_point(ends[n]-PIVOT,p,yaw)+c.v(0,1.6*scoop)
           for n,p in [('handFront',(-15,-14)),('handBack',(15,-14))]}
    paws={**hands,'footFront':c.v(0,0),'footBack':c.v(17*yaw+8.5*scoop,-5.2*scoop)}
    target,ctx=c.canvas()
    ctx.translate(*anchor)
    def limb(name):
        near=name.endswith('Front')
        hand=name.startswith('hand')
        stance=c.paw_direction('crest',name,grip,1)
        middle=c.v(-.30 if near else .31,1.)
        direction=facing_point(stance,middle,yaw)
        fold=((1 if near else -.62) if hand else -.86)*yaw
        c.leg(ctx,roots[name],paws[name],direction,fold,hand,near)
    limb('footBack')
    limb('handBack')
    limb('footFront')
    ctx.save()
    ctx.translate(*body_shift)
    ctx.scale(side,1)
    c.torso(ctx,c.v(0,0),side_angle*abs(yaw),3.2*math.sin(-.5)+2.5*scoop,1,front)
    ctx.restore()
    limb('handFront')
    end_head,end_pitch=c.head_position('crest',body,side_angle,1.)
    relative=end_head-PIVOT
    lead=float(c.ease(t+.035*math.sin(math.pi*t)))
    point=c.v(relative[0]*yaw,relative[1]+2.7*scoop)
    pitch=end_pitch*yaw+.018*math.sin(2*math.pi*t)
    c.paint_head(ctx,c.surface(head.image(lead)),point,pitch)
    return c.finish(target),anchor


def main():
    size=SIZE
    with Image.open(c.DEST/'crest.webp') as atlas:
        last=atlas.convert('RGBA').crop((7*size,5*size,8*size,6*size))
    head=TurningHead()
    frames,metadata=[],[]
    for i in range(COUNT):
        image,paw=one(i,last,head)
        frames.append(image)
        metadata.append({'anchor':[round(float(z)/SIZE,6) for z in paw],
                         'center':c.center(image)})
    c.pack('turnaround',frames)
    with Image.open(c.DEST/'turnaround.webp') as atlas:
        atlas=atlas.convert('RGBA')
        for i,src in [(0,last),(47,ImageOps.mirror(last))]:
            box=(i%8*size,i//8*size,(i%8+1)*size,(i//8+1)*size)
            assert np.array_equal(np.asarray(atlas.crop(box)),np.asarray(src))
    (c.DEST/'turnaround.json').write_text(json.dumps({'grid':[8,6],'cell':[SIZE,SIZE],
        'durationSeconds':.95,'frames':metadata},separators=(',',':'))+'\n')


if __name__=='__main__':
    main()
