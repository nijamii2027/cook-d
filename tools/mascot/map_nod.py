"""Bagel peeks over the map, using the café artist's sleepy, smiling sticker.

Head and paws come from the two small, neighbouring studies at the foot of the
original sheet. The off-centre chef-bone comes from the large central portrait.
The face and hat stay registered as one piece. Only the eye shapes close during a
slow blink. The two resting paws are composited in exactly the same place on
every frame. The live map edge sits at y=224 in each 288px cell.
"""
from functools import lru_cache
from pathlib import Path
from math import cos, pi, sin
from io import BytesIO
import sys
import cairo
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.interpolate import PchipInterpolator
from original_portrait import prepared_ink,cutout

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'dist/media/original/assets/customer/bagel-sticker-sheet.png'
DEST=ROOT/'dist/media/mascot'
FRAME,COUNT,LEDGE,SCALE=288,48,224,3
R=Image.Resampling.LANCZOS

with Image.open(SOURCE) as sheet:
    pair=sheet.convert('RGBA').crop((640,1470,1110,1910))
    crown_ink=prepared_ink(sheet.crop((590,840,1070,1250)))
source_ink=prepared_ink(pair)


def prepare_head():
    # Remove the neighbours and the cheek-pointing gesture from the lower study.
    # Restore the few covered pixels along the underside of its jaw.
    mask=Image.new('L',pair.size)
    ImageDraw.Draw(mask).polygon([(25,198),(156,197),(193,209),(220,229),(233,254),(244,269),
        (268,308),(268,368),(215,368),(208,343),(198,342),(184,348),(166,350),
        (138,351),(107,349),(87,346),(73,345),(68,353),(43,357),(26,344)],fill=255)
    ink=source_ink*(np.asarray(mask)/255)
    ink[336:354,104:185]=0
    repair=Image.new('L',pair.size);d=ImageDraw.Draw(repair)
    d.line([(102,346),(110,347),(116,347),(127,348),(136,348),(145,348),(156,347),
            (167,346),(175,345),(184,344),(189,344)],fill=245,width=4,joint='curve')
    return cutout(np.maximum(ink,np.asarray(repair)/255)).crop((30,200,265,365))


head=prepare_head()


def make_paw():
    # The upper-right study already has a soft paw resting on its neighbour.
    # Use its outline, removing only the neighbouring paw at the inside seam.
    field=Image.new('L',pair.size);d=ImageDraw.Draw(field)
    d.polygon([(237,235),(238,218),(244,203),(254,206),(270,209),(283,209),
               (296,211),(309,218),(318,227),(319,241),(312,247),(291,252),
               (252,250),(239,247)],fill=255)
    ink=source_ink*(np.asarray(field)/255)
    restore=Image.new('L',pair.size);d=ImageDraw.Draw(restore)
    d.line([(244,206),(250,207),(260,209),(269,210),(280,211),(288,212),
            (298,215),(305,218)],width=3,fill=250,joint='curve')
    return cutout(np.maximum(ink,np.asarray(restore)/255)).crop((233,200,322,253))


paw=make_paw()


def surface(image):
    b=BytesIO();image.save(b,format='PNG');b.seek(0)
    return cairo.ImageSurface.create_from_png(b)


@lru_cache(maxsize=1)
def chef_bone():
    # The small smiling study has a bare crown. Its larger sibling wears the
    # signature hand-inked two-lobed bone. Keep that original outline and the
    # little uneven turn where its base meets the forehead.
    mask=Image.new('L',(480,410))
    ImageDraw.Draw(mask).polygon([(314,121),(313,70),(330,45),(370,36),(398,47),
        (409,76),(408,111),(376,111),(364,141),(355,146),(341,137),(328,133)],fill=255)
    hat=cutout(crown_ink*np.asarray(mask)/255).crop((305,38,412,151))
    return surface(hat)


def canvas():
    output=cairo.ImageSurface(cairo.FORMAT_ARGB32,FRAME*SCALE,FRAME*SCALE)
    ctx=cairo.Context(output);ctx.scale(SCALE,SCALE)
    return output,ctx


def image_of(surf):
    b=BytesIO();surf.write_to_png(b);b.seek(0)
    return Image.open(b).convert('RGBA').resize((FRAME,FRAME),R)


def sticker(image,width):
    alpha=np.asarray(image.getchannel('A'))
    distance=ndimage.distance_transform_edt(alpha<128)
    white=Image.new('RGBA',image.size,'white')
    white.putalpha(Image.fromarray(np.uint8(np.clip(width+.5-distance,0,1)*255)))
    white.alpha_composite(image);return white


@lru_cache(maxsize=1)
def fixed_paws():
    surf,ctx=canvas();original=surface(paw)
    # Squat and rounded. Their upper halves tuck into the cheek, with only a
    # small cuff of each paw coming over the front of the paper.
    for x,y,scale,angle,mirror in [(99.5,224.7,.46,-4,False),(180.8,225.8,.425,4,True)]:
        ctx.save();ctx.translate(x,y);ctx.rotate(angle*pi/180)
        ctx.scale((-1 if mirror else 1)*scale,scale)
        ctx.set_source_surface(original,-44.5,-23.5);ctx.paint();ctx.restore()
    return sticker(image_of(surf),1.9)


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


# The head lifts slightly in anticipation, dips once on the downbeat, then
# follows with a shallower second acknowledgement and a longer settling pause.
beat=[0,.1,.21,.35,.43,.55,.61,.72,.81,.93,1]
depth=PchipInterpolator(beat,[0,-.4,-2.2,5.9,5.3,.5,-.36,2.4,1.1,0,0])
tilt=PchipInterpolator(beat,[-2,-2.2,-2.65,-.5,-.68,-2.2,-2.25,-1.36,-1.8,-2,-2])


def eyes(t):
    # The sleepy crescent highlights, nose and little smile are original pixels.
    blink=float(smooth((t-.285)/.064)*(1-smooth((t-.388)/.090)))
    if blink<.015:return head
    im=head.copy()
    for x,y,x2,y2 in [(74,61,102,87),(128,60,157,85)]:
        eye=head.crop((x,y,x2,y2));patch=Image.new('RGBA',eye.size,'white')
        h=max(3,round(eye.height*(1-.805*blink)))
        patch.alpha_composite(eye.resize((eye.width,h),R),(0,(eye.height-h)//2+round(1.5*blink)))
        im.paste(patch,(x,y))
    return im


def pose(t):
    t=t%1;dip=float(depth(t))
    surf,ctx=canvas()
    # The chin sits *behind* the upper edge. No exposed neck or upper arms.
    ctx.translate(144+.3*sin(2*pi*t),225.7+dip)
    ctx.rotate(float(tilt(t))*pi/180)
    ctx.scale(.92,.91)
    ctx.translate(-115.5,-140.5)
    ctx.set_source_surface(surface(eyes(t)),0,0);ctx.paint()
    # Keep the rim flush with the crown as the whole head dips. At the 84px
    # mobile display size, both lobes and the narrow shaft remain legible.
    ctx.translate(158,23.6)
    ctx.scale(.56,.56)
    ctx.set_source_surface(chef_bone(),-31,-99);ctx.paint()
    rear=sticker(image_of(surf),2.9)
    rear.paste((0,0,0,0),(0,LEDGE,FRAME,FRAME))
    paws=fixed_paws();rear.alpha_composite(paws)
    return rear


def make():
    frames=[pose(i/COUNT) for i in range(COUNT)]
    assert len({f.tobytes() for f in frames})==COUNT
    assert frames[0].tobytes()==pose(1).tobytes()
    arrays=np.asarray([np.asarray(f) for f in frames]);paws=np.asarray(Image.alpha_composite(Image.new('RGBA',(FRAME,FRAME)),fixed_paws()))
    # All visible paint below the ledge is a real paw. Each solid paw pixel,
    # including the portions overlapping the cheeks, remains fully stationary.
    assert np.all(arrays[:,LEDGE:]==paws[None,LEDGE:])
    fixed=paws[:,:,3]==255
    assert np.all(arrays[:,fixed]==paws[None,fixed])
    atlas=Image.new('RGBA',(FRAME*8,FRAME*6))
    for i,f in enumerate(frames):atlas.alpha_composite(f,((i%8)*FRAME,(i//8)*FRAME))
    atlas.save(DEST/'nod.webp',lossless=True,method=5)
    frames[0].save(DEST/'nod-still.webp',lossless=True,method=5)
    if len(sys.argv)>1:
        dest=Path(sys.argv[1]);dest.mkdir(exist_ok=True,parents=True)
        preview=Image.new('RGB',(FRAME*4,210),'#f4eddf')
        for k,i in enumerate([0,10,17,30]):
            tile=Image.new('RGB',(FRAME,FRAME),'#f4eddf');d=ImageDraw.Draw(tile)
            d.rectangle((0,LEDGE,FRAME,FRAME),fill='#ebe8d7');d.line((0,LEDGE,FRAME,LEDGE),fill='#817b6e');tile.paste(frames[i],(0,0),frames[i]);preview.paste(tile.crop((0,63,FRAME,273)),(FRAME*k,0))
        preview.save(dest/'new-peep.png')
    print(f'{len(frames)} distinct frames; {int(fixed.sum())} solid paw pixels fixed. Exact loop closure.')


if __name__=='__main__':make()
