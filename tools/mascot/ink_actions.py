"""Shared framing and atlas helpers for the Cook’d illustrator’s sticker artwork."""
from pathlib import Path
import sys, math
from PIL import Image, ImageDraw

BASE=Path(__file__).resolve().parents[2]
DEST=BASE/'dist/media/mascot'
SHEET=BASE/'dist/media/original/assets/customer/bagel-sticker-sheet.png'
SIZE=256
COLS=8
N=48
TAU=2*math.pi
INK='#19244c'
R=Image.Resampling.LANCZOS
QA=Path.cwd()
POSES={'stand':(1200,260,1540,710),'pour':(1200,825,1590,1240),'bake':(1130,1510,1610,1980),'seated':(70,270,525,690),'whisk':(590,270,1150,680)}
def ease(t): return t*t*(3-2*t)
def step(a,b,t): return ease(min(1,max(0,(t-a)/(b-a))))
def keyed(t,keys):
    for (a,v),(b,w) in zip(keys,keys[1:]):
        if t<=b: return v+(w-v)*step(a,b,t)
    return keys[-1][1]
def art(which): return Image.open(SHEET).convert('RGBA').crop(POSES[which])

def finish(im, box, scale, anchor=(.5,.5), screen=(128,128)):
    im=im.crop(box)
    im=im.resize((round(im.width*scale),round(im.height*scale)),R)
    target=Image.new('RGBA',(SIZE,SIZE))
    target.alpha_composite(im,(round(screen[0]-im.width*anchor[0]),round(screen[1]-im.height*anchor[1])))
    return target

def save(action,fn):
    frames=[fn(i/N) for i in range(N)]
    assert len({x.tobytes() for x in frames})==N,action
    atlas=Image.new('RGBA',(SIZE*8,SIZE*6))
    for i,f in enumerate(frames): atlas.alpha_composite(f,(i%8*SIZE,i//8*SIZE))
    atlas.save(DEST/(action+'.webp'),lossless=True,method=3)
    frames[0].save(DEST/(action+'-still.webp'),lossless=True)
    return frames
def proof(actions,filename):
    sheet=Image.new('RGB',(256*5,256*len(actions)),'#ead8b9')
    for j,(action,fn) in enumerate(actions):
        for k,i in enumerate((0,9,18,26,37)):
            f=fn(i/N); sheet.paste(f,(k*256,j*256),f)
            ImageDraw.Draw(sheet).text((k*256+3,j*256+3),f'{action} {i}',fill=INK)
    sheet.save(filename)
if __name__=='__main__':
    from pan_offer import pan_action
    from knead_action import knead_action
    from portrait_peek import portrait
    actions={'pan':pan_action,'knead':knead_action,'hello':portrait}
    if '--proof' in sys.argv:
        proof(list(actions.items()),QA/'ink-action-proof.jpg')
    else:
        for key,fn in actions.items():
            if len(sys.argv)==1 or key in sys.argv:
                save(key,fn)
