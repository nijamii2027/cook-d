"""Render the small, north-up card map. No network access is needed to build it.

Run `python tools/neighbourhood-map.py` from any directory. Refresh the frozen
OSM geometry by passing a public OSM XML extract covering 153.039,-27.581,
153.056,-27.568. Generate exactly the same SVG from the compact JSON snapshot.
"""
import json
import math
from pathlib import Path
import sys
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = ROOT / 'tools' / 'neighbourhood-streets.json'
SVG = ROOT / 'src' / 'neighbourhood-map.svg'
W, H = 500, 300
WEST, NORTH, SCALE = 153.0403, -27.56965, .35
OSM = 'https://www.openstreetmap.org/'
# Destination of the public directions link on the café's original site.
CAFE = (-27.5722183,153.0478762)


def project(point):
    lat,lon=point
    return ((lon-WEST)*111195*math.cos(math.radians(NORTH))*SCALE, (NORTH-lat)*111195*SCALE)


def simplify(points,tolerance=.62):
    """Douglas-Peucker in display coordinates: keep real bends at small scale."""
    if len(points)<3:return points
    (ax,ay),(bx,by)=points[0],points[-1]
    dx,dy=bx-ax,by-ay
    def distance(p):
        u=max(0,min(1,((p[0]-ax)*dx+(p[1]-ay)*dy)/(dx*dx+dy*dy or 1)))
        return math.hypot(p[0]-ax-u*dx,p[1]-ay-u*dy)
    i=max(range(1,len(points)-1),key=lambda j:distance(points[j]))
    if distance(points[i])<=tolerance:return [points[0],points[-1]]
    return simplify(points[:i+1],tolerance)[:-1]+simplify(points[i:],tolerance)


def extract(file):
    root=ElementTree.parse(file).getroot()
    nodes={n.get('id'):(float(n.get('lat')),float(n.get('lon'))) for n in root.findall('node')}
    ways={w.get('id'):w for w in root.findall('way')}
    parks={m.get('ref') for m in root.find("relation[@id='18000728']").findall('member') if m.get('role')=='outer'}
    def pts(i):return [nodes[n.get('ref')] for n in ways[str(i)].findall('nd')]
    data={k:[] for k in ['main','local','park','maughan','school','rail']}
    for wid,way in ways.items():
        tags={t.get('k'):t.get('v') for t in way.findall('tag')}
        highway=tags.get('highway');rail=tags.get('railway');name=tags.get('name','')
        category=None
        if wid in parks:category='maughan'
        elif tags.get('leisure')=='park':category='park'
        elif tags.get('amenity')=='school':category='school'
        elif rail=='rail' and not tags.get('service'):category='rail'
        elif highway in ('primary','tertiary','secondary') and name in ('Troughton Road','Boundary Road','McCullough Street','Turton Street','Breton Street'):category='main'
        elif highway in ('primary','tertiary','secondary','residential','unclassified'):category='local'
        if not category:continue
        xy=[project(p) for p in pts(wid)]
        xs,ys=zip(*xy)
        if min(xs)>W+4 or min(ys)>H+4 or max(xs)<-4 or max(ys)<-4:continue
        # Parallel Queensland Rail tracks collapse into one symbolic rail corridor.
        if category=='rail' and name!='Gold Coast Line Up':continue
        data[category].append([[round(x,1),round(y,1)] for x,y in simplify(xy)])
    # Public pedestrian access from the entrance on the northeast side of Banoon.
    walk=list(reversed(pts(623623868)))+list(reversed(pts(1350875740)))[1:]
    for lat,lon in (list(reversed(pts(16201017)))+list(reversed(pts(1128367806)))[1:-2]):
        walk.append((lat+.000025,lon-.000085))
    walk+=list(reversed(pts(1460694572)))[1:2]+[CAFE]
    data['walk']=[[round(x,1),round(y,1)] for x,y in simplify([project(p) for p in walk],.39)]
    data['station']=[round(x,1) for x in project(nodes['74882361'])]
    data['cafe']=[round(x,1) for x in project(CAFE)]
    data['attribution']='© OpenStreetMap contributors, ODbL 1.0'
    data['sources']=[OSM+'relation/18000728',OSM+'node/74882361',OSM+'node/6282037513','https://www.cookdcafe.com.au/',OSM+'copyright']
    return data


def line(points):return 'M'+' '.join(f'{x:g},{y:g}' for x,y in points)

def group(shapes,closed=False):
    return ''.join('<path d="'+line(s)+('Z' if closed else '')+'"/>' for s in shapes)


def label(text,x,y,angle=0,size=13):
    return f'<text transform="translate({x} {y}) rotate({angle})" font-size="{size}">{text}</text>'


def render(d):
    sx,sy=d['station'];cx,cy=d['cafe'];roads=group(d['local']);main=group(d['main']);rails=group(d['rail']);walk=line(d['walk'])
    logo=ElementTree.parse(ROOT/'dist/media/brand/wordmark.svg').getroot()
    wordmark=''.join(f'<path d="{path.attrib["d"]}"/>' for path in logo.iter('{http://www.w3.org/2000/svg}path'))
    labels=''.join([label('Boundary Rd',86,45,8,14),label('McCullough St',420,22,9,14),label('Turton St',388,168,9,14),label('Troughton Rd',271,185,-63,14)])
    # Spelling and positions aim for a readable card; all geometry and the
    # locations of both endpoints use the same local projection.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="visit-neighbourhood-map" viewBox="0 0 {W} {H}" role="img" aria-labelledby="neighbourhood-map-title neighbourhood-map-description" preserveAspectRatio="xMidYMid meet">
  <title id="neighbourhood-map-title">Cook’d Cafe, Sunnybank</title>
  <desc id="neighbourhood-map-description">Local map showing Cook’d at 88 Troughton Road, immediately south-west of McCullough Street, with Maughan Park to the north-east and a dotted walking path from Banoon station.</desc>
  <metadata>Street and park data © OpenStreetMap contributors, https://www.openstreetmap.org/copyright. Map rendered in November 2026.</metadata>
  <defs><pattern id="cookd-map-paper" width="16" height="19" patternUnits="userSpaceOnUse"><circle cx="3" cy="6" r=".55" fill="#9c8c6d" opacity=".26"/><circle cx="12" cy="16" r=".4" fill="#9c8c6d" opacity=".23"/></pattern><pattern id="cookd-map-park" width="18" height="13" patternUnits="userSpaceOnUse"><path d="M2 9l2-3m5 6 1-2" stroke="#909c73" stroke-width=".7" opacity=".62" fill="none"/></pattern></defs>
  <style>.visit-neighbourhood-map .visit-pin{{fill:#af352b;animation:cookd-location-glow 4.6s ease-in-out infinite}}@keyframes cookd-location-glow{{0%,100%{{fill:#a5362b}}50%{{fill:#da4f3e}}}}@media(prefers-reduced-motion:reduce){{.visit-neighbourhood-map .visit-pin{{animation:none}}}}</style>
  <rect width="500" height="300" fill="#eee8d8"/>
  <g fill="#e6dbc8">{group(d['school'],True)}</g>
  <g fill="#d9dfc4">{group(d['park'],True)}</g><g fill="#c8d5ac">{group(d['maughan'],True)}</g>
  <g fill="url(#cookd-map-park)">{group(d['park']+d['maughan'],True)}</g>
  <g fill="none" stroke-linecap="round" stroke-linejoin="round"><g stroke="#c7bea9" stroke-width="4.8">{roads}</g><g stroke="#fcf6e6" stroke-width="3.4">{roads}</g><g stroke="#bbb09a" stroke-width="9.4">{main}</g><g stroke="#fffaf0" stroke-width="7.6">{main}</g>
  <g stroke="#8a8d86" stroke-width="1.4">{rails}</g><g stroke="#8a8d86" stroke-width="5.2" stroke-dasharray="1.5 5">{rails}</g></g>
  <rect width="500" height="300" fill="url(#cookd-map-paper)"/>
  <path d="{walk}" stroke="#fffaeb" stroke-width="5.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="{walk}" stroke="#394460" stroke-width="2.35" stroke-dasharray=".7 5.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <g font-family="'DM Sans',Arial,sans-serif" font-weight="500" text-anchor="middle" fill="#464b51" stroke="#f7f1df" stroke-width="3" stroke-linejoin="round" paint-order="stroke">{labels}</g>
  <text transform="translate(359 68)" fill="#43533c" text-anchor="middle" font-family="Georgia,serif" font-weight="bold" font-style="italic" font-size="15" paint-order="stroke" stroke="#d6dfbd" stroke-width="2.4">Maughan Park</text>
  <g transform="translate({sx:.1f} {sy:.1f})"><rect x="-8" y="-7.5" width="16" height="15" rx="4" fill="#273655"/><g stroke="#fff6e5" fill="none" stroke-width="1.1" stroke-linecap="round"><rect x="-4" y="-5" width="8" height="9" rx="2"/><path d="M-3 -1.7h6m-6 6-1 1.2M3 4.3l1.1 1.2"/></g><text x="-13" y="5" text-anchor="end" fill="#273655" paint-order="stroke" stroke="#f7f0df" stroke-width="3.6" stroke-linejoin="round" font-size="15" font-weight="700" font-family="'DM Sans',Arial,sans-serif">Banoon station</text></g>
  <g transform="translate({cx:.1f} {cy:.1f})"><svg x="-85" y="-24" width="74" height="29.7" viewBox="{logo.attrib['viewBox']}" overflow="visible"><g fill="#19244d" stroke="#faf3e3" stroke-width="33" paint-order="stroke" stroke-linejoin="round">{wordmark}</g></svg><path class="visit-pin" d="M.2,.3 3.4,-21.3 7.5,-15.3 16.4,-27 22.1,-22.5 13.1,-10.9 21.1,-9.6Z" stroke="#fffaed" stroke-linejoin="round" stroke-width="2.2"/></g>
</svg>\n'''

if __name__=='__main__':
    if len(sys.argv)>1:
        data=extract(sys.argv[1]);GEOMETRY.write_text(json.dumps(data,separators=(',',':'))+'\n')
    else:data=json.loads(GEOMETRY.read_text())
    SVG.write_text(render(data))
