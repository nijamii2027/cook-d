"""Bake the published Bagel atlas set: python3 make_mascots.py
Requires Pillow, SciPy, NumPy and PyCairo. --index-only regenerates CSS and JSON.
"""
from pathlib import Path
import sys
import json
import subprocess
import os

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).resolve().parent
DEST=ROOT/'dist/media/mascot'
ACTIONS={'climb':(288,1.34),'hang':(288,2.4),'traverse':(288,1.4),'crest':(288,1.3),
         'turnaround':(288,1.38),'hop':(288,1.28),'hop-turn':(288,1.18),'pan':(256,2.65),'pour':(256,2.8),'knead':(256,2.1),'peel':(320,3.6),'chop':(256,2.2),'hello':(256,3.35),'garnish':(256,2.5),'dust':(256,2.5),'arrive':(256,2.7),
         'tamp':(256,2.6),'shake':(256,2.55),'nod':(288,3.2),
         'run':(256,.80),'route':(256,.90),'sip':(256,2.4),'sip-run':(256,.9)}
N=48; COLS=8; ROWS=6
def write_index():
    css=['.cookd-sprite { display: block; width: 100%; aspect-ratio: 1; background-repeat: no-repeat; background-size: 800% 600%; animation: cookd-frames var(--cookd-cycle, 1s) steps(1, end) infinite; }']
    data={'frames':N,'grid':[COLS,ROWS],'contacts':'contacts.json','turnContacts':'turnaround.json','hopContacts':'hop.json',
          'facing':{k:'right' for k in ('run','route','sip','sip-run','climb','hang','crest','traverse','hop')},'actions':{}}
    for name,(size,seconds) in ACTIONS.items():
        css.append(f'.cookd-sprite[data-action="{name}"] {{ background-image: url("./{name}.webp"); --cookd-cycle: {seconds}s; }}')
        data['actions'][name]={'file':f'{name}.webp','cell':[size,size],'durationSeconds':seconds,'still':name+'-still.webp'}
    css.append('@keyframes cookd-frames {')
    for i in range(N):
        css.append(f'  {100*i/N:.6f}% {{ background-position: {100*(i%COLS)/(COLS-1):.6f}% {100*(i//COLS)/(ROWS-1):.6f}%; }}')
    css.extend(['  100% { background-position: 0% 0%; }','}',
                '@media (prefers-reduced-motion: reduce) { .cookd-sprite { animation-play-state: paused; } }'])
    (DEST/'sprites.css').write_text('\n'.join(css)+'\n')
    (DEST/'sprites.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':
    if '--index-only' not in sys.argv:
        env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
        for args in (['map_nod.py'], ['portrait_peek.py'], ['garnish.py'], ['finishers.py'], ['drink_stations.py'], ['pan_offer.py'], ['knead_action.py'], ['baker_peel.py'],
                     ['menu_chop.py'], ['pouring.py'], ['coffee_run.py'], ['climbing.py'], ['turnaround.py'], ['hero_hop.py']):
            subprocess.run([sys.executable,str(SOURCE/args[0]),*args[1:]],check=True,env=env)
    write_index()
