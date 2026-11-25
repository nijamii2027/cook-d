"""Bagel pinches herbs over a plated lunch; the seated café illustration stays fixed."""
from pathlib import Path
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import ink_actions as ink


SOURCE = ink.art('seated')
W,H = SOURCE.size
S = 3
NAVY = (25, 35, 75, 255)
WHITE = (255, 255, 255, 255)
SHOULDER = np.array([236.,273.])
CUFF = np.array([180.,280.])


def curve(start, *segments):
    pts=[start]
    for a,b,c in segments:
        p=np.array(pts[-1])
        for u in np.linspace(0,1,22)[1:]:
            pts.append(tuple(p*(1-u)**3+3*np.array(a)*u*(1-u)**2+3*np.array(b)*u**2*(1-u)+np.array(c)*u**3))
    return pts


def big():
    return Image.new('RGBA',(W*S,H*S))


def mark(canvas, pts, fill=None, edge=NAVY, width=2.6):
    coords=[(round(x*S),round(y*S)) for x,y in pts]
    pen=ImageDraw.Draw(canvas)
    if fill:
        pen.polygon(coords,fill=fill)
        coords.append(coords[0])
    if edge:
        pen.line(coords,fill=edge,width=round(width*S),joint='curve')
        rad=round(width*S/2)
        for x,y in (coords[0],coords[-1]):
            pen.ellipse((x-rad,y-rad,x+rad,y+rad),fill=edge)


def small(canvas):
    return canvas.resize((W,H), Image.Resampling.LANCZOS)


def cut(points):
    mask=Image.new('L',(W*S,H*S))
    ImageDraw.Draw(mask).polygon([(round(x*S),round(y*S)) for x,y in points],fill=255)
    source=SOURCE.copy()
    alpha=np.array(source.getchannel('A'),float)*np.array(mask.resize((W,H),Image.Resampling.LANCZOS))/255
    source.putalpha(Image.fromarray(np.rint(alpha).astype('uint8')))
    return source


def white_outline(layer, radius):
    distance=ndimage.distance_transform_edt(np.asarray(layer.getchannel('A'))<128)
    alpha=np.uint8(255*np.clip(radius+.5-distance,0,1))
    out=Image.new('RGBA',(W,H),WHITE);out.putalpha(Image.fromarray(alpha))
    return out


# Preserve the source's bone, ears, apron, sitting feet and long curled tail.
# The original fire and wooden spoon fall entirely outside this silhouette.
BODY=cut([(122,55),(435,55),(435,399),(171,399),(178,334),(191,315),(205,307),
          (217,301),(226,293),(232,290),(237,286),(238,263),(228,262),
          (224,265),(200,264),(182,265),(153,256),(126,244)])
# Keep the short contour beneath the shoulder when the chef stretches his sleeve.
under=big()
mark(under,curve((239,260),((240,271),(240,285),(236,294)),
                 ((230,293),(223,296),(216,301)),((221,289),(225,275),(230,261))),
     fill=WHITE,width=3)
under=small(under)
collar=white_outline(under,9)
collar.alpha_composite(under);collar.alpha_composite(BODY)
BODY=collar

SLEEVE=cut([(175,268),(193,267),(218,266),(228,262),(237,261),(240,262),
            (239,284),(228,289),(207,291),(190,295),(182,294),(177,290),
            (175,284),(178,281),(177,275),(173,274)])
HEAD=cut([(120,60),(428,60),(427,232),(369,260),(346,257),(310,257),
          (307,262),(285,269),(257,272),(243,263),(226,262),(214,265),
          (192,264),(181,264),(154,256),(125,240)])
# The original outer white sticker margin belongs behind the moving fingers.
# Restore just the chin's ink and fill in front of the shoulder.
hy,hx=np.indices((H,W))
chin=np.interp(hx,[125,146,160,172,177,181,185,191,196,202,210,224,235,245,264],
    [220,229,235,238,252,259,258,261,258,261,262,264,263,264,272])
ha=np.array(HEAD.getchannel('A'))
ha[(hx<264)&(hy>chin+1.3)]=0
HEAD.putalpha(Image.fromarray(ha))


def hand(opening):
    out=big()
    # Two softly joined fingertips unclasp a few leaves. The wrist joint sits
    # inside the original loose cuff throughout the gesture.
    top=curve((183,273), ((177,272),(169,264),(164,266)),
              ((159,267),(157,276),(153,280+opening*3)),
              ((151,284+opening*3),(154,287+opening*3),(158,284+opening*3)),
              ((163,279+opening*2),(165,277),(167,276)),
              ((165,281),(163,284),(160,285)),
              ((157,288),(161,292),(165,289)),
              ((169,286),(173,282),(177,286)),
              ((180,289),(184,285),(186,279)))
    mark(out,top,fill=WHITE,width=2.75)
    mark(out,curve((169,274),((172,272),(174,272),(176,274))),width=1.65)
    return small(out)


def plate():
    out=big()
    mark(out,curve((54,336),((58,327),(86,321),(119,319)),
            ((153,316),(181,319),(191,326)),((195,332),(184,341),(170,345)),
            ((143,355),(94,356),(70,351)),((60,348),(56,344),(54,336))),
         fill=WHITE,width=3.7)
    mark(out,curve((55,336),((79,346),(122,345),(148,340)),((169,337),(184,331),(191,326))),width=2.2)
    mark(out,curve((72,333),((81,327),(91,325),(99,323)),((102,319),(108,316),(113,317)),
           ((117,309),(127,308),(133,313)),((143,309),(151,311),(157,315)),
           ((164,313),(174,317),(176,322)),((179,324),(182,323),(185,326)),
           ((160,336),(115,343),(73,335))),fill=WHITE,width=2.35)
    for x,y,v in [(95,330,1),(111,324,-1),(128,320,1),(147,321,-1),(163,325,-1),(135,331,1)]:
        mark(out,curve((x-2,y+1),((x,y-2),(x+3,y-2),(x+5,y+v))),width=1.45)
    return small(out)


PLATE=plate()
PLATE_MATTE=white_outline(PLATE,6.2)
PLATE_MATTE.alpha_composite(PLATE)


def transform(piece,a,pivot,at):
    c,s=math.cos(a),math.sin(a)
    inv=np.array([[c,s],[-s,c]])
    off=pivot-inv@at
    return piece.transform((W,H),Image.Transform.AFFINE,
            (c,s,off[0],-s,c,off[1]),Image.Resampling.BICUBIC)


def rotated(vector,a):
    c,s=math.cos(a),math.sin(a)
    return np.array([vector[0]*c-vector[1]*s,vector[0]*s+vector[1]*c])


def gesture(t):
    t=t%1
    reach=ink.keyed(t,[(0,.04),(.10,0),(.29,.93),(.43,1),(.59,.91),(.69,.86),(.87,.08),(.94,.015),(1,.04)])
    shake=(math.sin((t-.32)*2*math.pi*9)*math.sin(math.pi*(t-.32)/.32)**2 if .32<t<.64 else 0)
    arm_angle=math.radians(-22+36*reach+2.1*shake)
    finger_angle=math.radians(44-61*reach+5.8*shake)
    cuff=SHOULDER+rotated(CUFF-SHOULDER,arm_angle)
    pinch=cuff+rotated(np.array([-25.,4.]),finger_angle)
    return arm_angle, finger_angle, cuff, pinch, reach


def leaf(canvas,x,y,theta,length):
    direction=np.array([math.cos(theta),math.sin(theta)])
    side=np.array([-direction[1],direction[0]])
    center=np.array([x,y])
    def pt(a,b):return tuple(center+direction*(a*length)+side*(b*length))
    mark(canvas,curve(pt(-.61,0), (pt(-.19,-.32),pt(.24,-.28),pt(.57,-.02)),
          (pt(.23,.26),pt(-.13,.27),pt(-.61,0))),fill=NAVY,edge=None)
    if length>8.8:
        mark(canvas,curve(pt(-.26,.015),(pt(-.13,0),pt(.01,-.025),pt(.15,-.035))),
             edge=WHITE,width=.95)


def garnish_action(t):
    a,b,cuff,pinch,reach=gesture(t)
    spread=ink.step(.23,.43,t)*(1-ink.step(.66,.81,t))
    fore=transform(hand(spread),b,CUFF,cuff)
    fore.alpha_composite(transform(SLEEVE,a,SHOULDER,SHOULDER))
    herbs=big()
    # Each leaf leaves the current fingertip position and disappears behind the
    # fixed rice mound, so the loop does not erase a pile of previously landed leaves.
    falling=[(.305,.235,141,-.72,13),(.36,.27,159,1.05,9.8),(.403,.238,128,.1,11.5),
             (.46,.26,151,-.84,12),(.516,.235,138,.63,9.5),(.568,.245,164,.2,10.8)]
    for i,(release,duration,land,angle,length) in enumerate(falling):
        age=(t-release)/duration
        if 0<=age<1:
            start=gesture(release)[3]
            arc=math.sin(math.pi*age)
            x=start[0]+(land-start[0])*age+6*arc*math.sin(i*1.73+age*2.7)
            y=start[1]+3+(322-start[1])*age**1.65-3*arc
            leaf(herbs,x,y,angle+age*(1.6 if i%2 else -2.15),length)
    if .04<t<.475:
        # The pinched sprig peeks out, then separates as the fingers unclasp.
        amount=ink.step(.04,.17,t)*(1-ink.step(.293,.475,t))
        for j in range(2):
            leaf(herbs,pinch[0]-1+j*3,pinch[1]+3+j,(-.78+j*1.75)+b,amount*(12-j))
    result=white_outline(fore,9)
    result.alpha_composite(BODY)
    result.alpha_composite(small(herbs))
    result.alpha_composite(PLATE_MATTE)
    result.alpha_composite(fore)
    result.alpha_composite(HEAD)
    return ink.finish(result,(30,60,424,387),.603,screen=(128,128))


if __name__=='__main__':
    frames=ink.save('garnish',garnish_action)
    frames[22].save(ink.DEST/'garnish-still.webp',lossless=True)
