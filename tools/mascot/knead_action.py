"""Animate the original artist's baking sticker in separate working layers.

Run this file to rebuild the 48-frame knead atlas. All coordinates are measured
on the source sticker. Only the forearms, the working dough and the eyelids
move. The bench and its props are composited from the same plate on every frame.
"""
from pathlib import Path
import math
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'dist/media/original/assets/customer/bagel-sticker-sheet.png'
OUT = ROOT / 'dist/media/mascot'
CROP = (1130, 1510, 1610, 1980)
FRAME = 256
N = 48
R = Image.Resampling.LANCZOS
original = Image.open(SOURCE).convert('RGBA').crop(CROP)
w, h = original.size
source = np.asarray(original)


def span_mask(rows):
    """Outline a scanned shape using (y, left edge, right edge) landmarks."""
    vertices = [(left, y) for y, left, _ in rows]
    vertices += [(right, y) for y, _, right in reversed(rows)]
    mask = Image.new('L', (w * 3, h * 3))
    ImageDraw.Draw(mask).polygon([(round(x*3),round(y*3)) for x,y in vertices],fill=255)
    return mask.resize((w,h),R)


def cut(mask):
    part = original.copy()
    part.putalpha(mask)
    return part

# Landmarks stop just past the ink on each side. Between the two wrists the
# table edge is continuous on its own layer, even when hidden by a forearm.
left_mask = span_mask([(271,168,182),(277,166,184),(284,162,185),(291,157,187),
    (302,149,183),(307,148,181),(313,147,180.9),(324,144,180.7),
    (329,144,179),(333,143,178.7),(337,144.3,177),(340,148,174),(342,150,172)])
right_mask = span_mask([(268,260,279),(278,259.5,282),(289,255,283),(299,254,283.5),
    (304,252.6,282),(308,251,280.7),(312,248.5,279.5),(315,246,277.8),
    (318,244,276),(322,241.5,274),(326,243,271.5),(328,245,269.3),
    (330,247,267.6),(332,254.5,265),(333.2,257,263.8)])
left = cut(left_mask)
right = cut(right_mask)

# The loaf fills its silhouette with cream-white, as in the original drawing.
# Reconstruct the short top outline formerly hidden underneath each paw.
loaf_mask = span_mask([(313,232,239),(316,225,247),(320,196,253),(323,177,255),
    (326,161,259),(331,141,264),(337,131,267.7),(345,125.5,269),
    (352,125.3,272.5),(358,126,273),(364,132,271),(369,146,266),
    (373,172,259),(376.5,214,249)])
loaf = cut(loaf_mask)
loaf_array=np.array(loaf)
for box in [(142,320,181,342),(241,314,269,333)]:
    x,y,x2,y2=box
    loaf_array[y:y2,x:x2,:3]=255
loaf=Image.fromarray(loaf_array)
# Fill the joins with lines traced in the direction of the adjoining contour.
loaf_draw=ImageDraw.Draw(loaf)
ink=(22,31,75,255)
loaf_draw.line([(139,335),(144,332),(151,331),(158,330),(165,328),(172,328),(179,326),(183,326)],fill=ink,width=4,joint='curve')
loaf_draw.line([(238,318),(244,320),(249,322),(254,326),(259,330),(262,334)],fill=ink,width=4,joint='curve')

plate_array=source.copy()
# Clear only the existing arms and loaf; retain the immutable white sticker
# border, the exact printed head, and every other feature of the original.
for mask in [left_mask,right_mask]:
    plate_array[np.asarray(mask)>0,:3]=255
plate_array[314:377,123:278,:3]=255
# Reconstruct the table underneath each wrist from neighbouring columns of its
# original pen stroke, preserving both its slope and the line's ink character.
for x1,x2 in [(139,184),(239,287)]:
    for x in range(x1,x2):
        sample_x=200+(x%33)
        sample_y=np.arange(304,316) + round((x-sample_x)*.019)
        plate_array[304:316,x,:3]=source[sample_y,sample_x,:3]
plate=Image.fromarray(plate_array)


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


def press(t):
    # Gather with the heel of one paw, transfer the load, then release.
    cues=[(0,.16),(.13,.02),(.23,.09),(.46,1),(.55,.97),(.70,.55),(.86,.11),(1,.16)]
    for (a,va),(b,vb) in zip(cues,cues[1:]):
        if t<=b:return float(va+(vb-va)*smooth((t-a)/(b-a)))
    return cues[-1][1]


def arm_layer(layer, region, shoulder, tip, travel_x, travel_y, elbow):
    """Move each wrist in an arc, blending displacement down from the shoulder."""
    x0,y0,x1,y1=region
    arm=np.asarray(layer.crop(region),np.float32)/255
    # Premultiply when sampling the cut edge to avoid a dark fringe.
    arm[:,:,:3]*=arm[:,:,3:4]
    yy,xx=np.indices(arm.shape[:2],dtype=float)
    ys=np.arange(y0-40,y1+40,dtype=float)
    weight=smooth((ys-shoulder)/(tip-shoulder))
    old_y=np.interp(yy[:,0]+y0,ys+weight*travel_y,ys)
    u=smooth((old_y-shoulder)/(tip-shoulder))
    shift=travel_x*u + elbow*4*u*(1-u)
    lookup_y=np.broadcast_to((old_y-y0)[:,None],xx.shape)
    lookup_x=xx-shift[:,None]
    pixels=np.stack([map_coordinates(arm[:,:,i],[lookup_y,lookup_x],order=1,mode='constant') for i in range(4)],axis=-1)
    pixels[:,:,:3]/=np.maximum(pixels[:,:,3:4],1/255)
    return Image.fromarray(np.rint(np.clip(pixels,0,1)*255).astype(np.uint8)),(x0,y0)


def output_canvas(scene):
    # Match the established sprite size, registration and safe transparent gutter.
    work=scene.crop((20,55,432,433)).resize((233,214),R)
    result=Image.new('RGBA',(FRAME,FRAME))
    result.alpha_composite(work,(12,21))
    return result


def assemble(phase):
    t=phase%1
    load=press(t)
    lead=math.sin(2*math.pi*t)
    sx=1+.155*load-.028*(1-load)
    sy=1-.305*load+.105*(1-load)
    pivot=(200,367)
    offset=3.1*math.sin(2*math.pi*(t-.06))
    x0,y0,x1,y1=(110,303,287,379)
    geom=loaf.transform((x1-x0,y1-y0),Image.Transform.AFFINE,
        (1/sx,0,(x0-pivot[0]-offset)/sx+pivot[0],0,1/sy,(y0-pivot[1])/sy+pivot[1]),
        Image.Resampling.BICUBIC)
    scene=plate.copy()
    scene.alpha_composite(geom,(x0,y0))
    # Each paw stays seated on the moving upper face of the loaf. Half-beat
    # lateral lead keeps the hands from moving in lockstep.
    for part,region,shoulder,tip,anchor,side in [
        (left,(121,267,202,362),279,338,158,-1),
        (right,(228,265,304,354),276,329,254,1),
    ]:
        shift_x=(anchor-pivot[0])*(sx-1)+offset+side*1.8*lead
        shift_y=(tip-pivot[1])*(sy-1)+1.2*load+side*.9*lead
        arm,point=arm_layer(part,region,shoulder,tip,shift_x,shift_y,-side*(3.2*load+lead))
        scene.alpha_composite(arm,point)
    # Reuse both shoulder seams above their hinges at full source coverage.
    # This preserves the artist's sparse apron neckline without a cutout seam.
    scene.paste(original.crop((133,263,302,279)),(133,263))
    # The eyes close briefly on the firm downward push. Change these two ink
    # shapes only. All head contours, hat lines and apron straps stay registered.
    blink=float(smooth((t-.405)/.076)*(1-smooth((t-.501)/.096)))
    if blink:
        for box in [(173,190,203,218),(235,185,264,213)]:
            x,y,x2,y2=box
            eye=original.crop(box); blank=Image.new('RGBA',eye.size,'white')
            height=round(eye.height*(1-.84*blink))
            blank.alpha_composite(eye.resize((eye.width,height),R),(0,(eye.height-height)//2+round(1.4*blink)))
            scene.alpha_composite(blank,(x,y))
    return scene


# Register the immobile props in final canvas coordinates. This last matte pass
# preserves the exact antialiased ink along the thin bench line after downsampling.
FIXED_PROPS = [(37,295,131,326),(195,306,229,314),(319,225,428,354),
               (253,378,324,429),(159,380,193,402),(285,340,308,363)]
def prop_rect(box):
    x,y,x2,y2=box
    return (math.ceil((x-20)*233/412)+12, math.ceil((y-55)*214/378)+21,
            math.floor((x2-20)*233/412)+12, math.floor((y2-55)*214/378)+21)
fixed_reference=output_canvas(original)
registered_patches=[(prop_rect(box),fixed_reference.crop(prop_rect(box))) for box in FIXED_PROPS]

def knead_action(t):
    frame=output_canvas(assemble(t))
    for box,content in registered_patches:frame.paste(content,box)
    return frame


def build():
    frames=[knead_action(i/N) for i in range(N)]
    atlas=Image.new('RGBA',(FRAME*8,FRAME*6))
    for i,frame in enumerate(frames):atlas.alpha_composite(frame,(FRAME*(i%8),FRAME*(i//8)))
    atlas.save(OUT/'knead.webp',lossless=True,method=5)
    frames[0].save(OUT/'knead-still.webp',lossless=True,method=5)
    return frames


def validate(frames):
    arrays=np.asarray([np.asarray(f) for f in frames]); base=arrays[0]
    assert len({a.tobytes() for a in arrays})==N
    # Mark the full possible swept area, with a margin for Lanczos filtering.
    # The rest (including both ends of the bench, the cup, steam and pastries)
    # must be pixel identical to the *original source* through the whole loop.
    valid=np.ones((FRAME,FRAME),bool)
    for source_box in [(168,182,272,222),(119,262,305,377)]:
        x,y,x2,y2=source_box
        valid[math.floor((y-55)*214/378)+18:math.ceil((y2-55)*214/378)+25,
              math.floor((x-20)*233/412)+9:math.ceil((x2-20)*233/412)+16]=False
    anchor=np.asarray(output_canvas(original)).copy()
    assert np.array_equal(base[valid],anchor[valid]),'A fixed feature departs from the original source'
    assert all(np.array_equal(a[valid],anchor[valid]) for a in arrays),'Moved protected geometry'
    # Protect the original cup / pastry silhouettes even inside the general
    # workspace bounding box, plus intact visible sections of the table edge.
    fixed=np.zeros((FRAME,FRAME),bool)
    for x,y,x2,y2 in FIXED_PROPS:
        fixed[math.ceil((y-55)*214/378)+21:math.floor((y2-55)*214/378)+21,
              math.ceil((x-20)*233/412)+12:math.floor((x2-20)*233/412)+12]=True
    assert all(np.array_equal(a[fixed],anchor[fixed]) for a in arrays),'Fixed prop changed'
    print(f'{N} distinct poses, {int((valid|fixed).sum())} fixed pixels verified against the original in every frame.')
    return arrays


if __name__=='__main__':
    frames=build();validate(frames)
    if len(sys.argv)>1:
        dest=Path(sys.argv[1]);dest.mkdir(exist_ok=True,parents=True)
        sheet=Image.new('RGB',(256*4,256*2),'#f4d7ad')
        for n,i in enumerate([0,6,12,18,24,30,36,42]):sheet.paste(frames[i],((n%4)*256,(n//4)*256),frames[i])
        sheet.save(dest/'knead-proof.jpg',quality=95)
        rgb=[]
        for frame in frames:
            bg=Image.new('RGB',frame.size,'#f4d7ad');bg.paste(frame,mask=frame.getchannel('A'));rgb.append(bg)
        rgb[0].save(dest/'knead-proof.gif',save_all=True,append_images=rgb[1:],duration=50,loop=0,disposal=2)
