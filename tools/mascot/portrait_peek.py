"""Bagel peeks out of the folded edge of his own illustrated proof card."""
from math import cos, sin, pi
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.interpolate import PchipInterpolator

from ink_actions import SHEET, save
from original_portrait import extract_head, swaying_head

S = 3
SIZE = 256
NAVY = (26, 35, 77, 255)
WHITE = (255, 255, 255, 255)
RESAMPLE = Image.Resampling.LANCZOS
FACE = extract_head(Image.open(SHEET).convert('RGBA'))
# The paws find the paper before the face appears. Hold high long enough to see
# the dog's original expression, then duck behind the same edge for a perfect loop.
beats = [0, .10, .21, .33, .42, .58, .68, .78, .90, 1]
head_height = PchipInterpolator(beats, [0, 2, 30, 85, 105, 106, 103, 95, 17, 0])
tilt = PchipInterpolator(beats, [0, -.5, -2, -6, -7, 3, 7, 5, 2, 0])
hand_height = PchipInterpolator(beats, [3, 11, 16, 15, 17, 16, 17, 19, 11, 3])


def cubic(draw, start, *sections, width=2.4):
    pts = [start]
    for a, b, e in sections:
        last = np.array(pts[-1])
        for t in np.linspace(0, 1, 26)[1:]:
            pts.append((1-t)**3*last + 3*(1-t)**2*t*np.array(a) + 3*(1-t)*t*t*np.array(b) + t**3*np.array(e))
    draw.line([(round(x*S), round(y*S)) for x,y in pts], fill=NAVY, width=round(width*S), joint='curve')


def paw(draw, x, y, side):
    # A loose mitten and two short inner toe marks curve over the paper edge.
    raw = [(0,13),(-4,10),(-5,1),(-2,-7),(5,-11),(15,-10),(21,-4),(22,5),(19,12),(15,13),(11,10),(9,14),(5,14)]
    points=[(x+dx*side,y+dy) for dx,dy in raw]
    draw.polygon([(round(px*S), round(py*S)) for px,py in points], fill=WHITE)
    for start,end in zip(points,points[1:]+points[:1]):
        draw.line([(round(a*S),round(b*S)) for a,b in (start,end)], fill=NAVY, width=round(2.2*S))
    for dx,dy in [(11,8),(17,7)]:
        cubic(draw,(x+side*dx,y+dy),((x+side*(dx+.5),y+dy-1),(x+side*(dx+1.4),y+dy-3),(x+side*(dx+1.5),y+dy-5)),width=1.1)


def portrait(t):
    w=SIZE*S
    img=Image.new('RGBA',(w,w))
    edge=198
    lift=float(head_height(t))
    blink=max(0,1-abs(t-.615)/.05)**1.7
    face=swaying_head(FACE,t*2*pi,.22,blink).resize((round(167*S),round(148*S)),RESAMPLE)
    face=face.rotate(float(tilt(t)),Image.Resampling.BICUBIC,expand=True)
    center=(128 + 5*sin(2*pi*t),edge+20-lift)
    draw=ImageDraw.Draw(img)
    shoulders=[(82,center[1]+60),(100,center[1]+46),(156,center[1]+47),(177,center[1]+63),
               (184,edge+17),(73,edge+17)]
    outline=[(round(x*S),round(y*S)) for x,y in shoulders]
    draw.polygon(outline,fill=WHITE)
    draw.line(outline+[outline[0]],fill=NAVY,width=round(2.3*S),joint='curve')
    img.alpha_composite(face,(round(center[0]*S-face.width/2),round(center[1]*S-face.height/2)))
    draw=ImageDraw.Draw(img)
    draw.rectangle((0,edge*S,w,w),fill=(255,255,255,0))
    for x,side,delay in [(65,1,0),(190,-1,.035)]:
        amount=float(hand_height((t-delay)%1))
        paw(draw,x,edge+11-amount,side)
    # Two interrupted ink strokes leave the knuckles in front of the crease.
    cubic(draw,(22,edge+1),((32,edge-2),(47,edge+2),(60,edge)),width=2)
    cubic(draw,(89,edge+1),((111,edge-1),(143,edge+2),(165,edge)),width=2)
    cubic(draw,(198,edge),((210,edge-1),(223,edge),(232,edge-2)),width=2)
    img=img.resize((SIZE,SIZE),RESAMPLE)
    white=Image.new('RGBA',img.size,'white');white.putalpha(img.getchannel('A').filter(ImageFilter.MaxFilter(7)))
    white.alpha_composite(img)
    return white


if __name__=='__main__':
    save('hello',portrait)
