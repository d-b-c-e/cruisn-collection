"""CPU layout fixture executing the real settings draw method; no GL or devices.

This verifies placement/text only. It is not packaged GPU or input acceptance.
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
import collection
import settings_view


class Fixture(collection.Shell):
    def __init__(self, width, height):
        self.w,self.h=width,height
        self.ctx=SimpleNamespace(enable=lambda _:None)
        self.bg=collection.background_image(width,height)
        self.title=collection.text_image("CRUIS'N  COLLECTION",height//14,
            fill=(255,224,160,255),glow=(255,96,32,200))
        self.foot_cache={};self.text_cache={}
        self.canvas=Image.new('RGBA',(width,height));self.bounds=[]

    def tex(self, image):return image

    def rect(self, image, x,y,width,height,tint=(1,1,1,1)):
        width,height=max(1,round(width)),max(1,round(height))
        sample=image.resize((width,height),Image.Resampling.LANCZOS)
        if tint!=(1,1,1,1):
            sample=Image.merge('RGBA',tuple(c.point(lambda v,t=t:v*t) for c,t in zip(sample.split(),tint)))
        self.canvas.alpha_composite(sample,(round(x),round(y)))

    def text_at(self,text,px,x,y,tint=(1,1,1,1),align='l'):
        image=self.text_tex(text,px);h=px*1.9;w=image.width*h/image.height
        left=x-w if align=='r' else x
        self.bounds.append(dict(text=text,x=left,y=y,width=w,height=h))
        super().text_at(text,px,x,y,tint,align)

    def center_text(self,text,px,y,tint=(1,1,1,1)):
        image=self.text_tex(text,px);h=px*1.9;w=image.width*h/image.height
        self.bounds.append(dict(text=text,x=(self.w-w)/2,y=y,width=w,height=h))
        super().center_text(text,px,y,tint)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    with patch.object(collection,'CFG',str(args.output/'absent.ini')):
        state=collection.load_config()
    state['bindings']={'steer':'A very long racing wheel name|axis:0:0:pos','gas':'Separate USB pedals|axis:1:0:neg','brake':'Separate USB pedals|axis:2:0:neg'}
    report=dict(scope='CPU execution of actual settings layout; no GPU, device or input acceptance',images=[])
    for width,height in ((1280,720),(3840,2160)):
        for selected,page in (('simple','setup'),('simple','controls'),('simple','ffb'),('advanced','root'),('advanced','buttons')):
            state['settings_view']=selected
            rows=collection.settings_rows(page,state,False,'Fixture')
            focus=len(rows)-2 if page=='buttons' else 1
            fixture=Fixture(width,height)
            fixture.draw_settings(focus,collection.SETTINGS_TITLE[page],[(r[1],r[2]) for r in rows],rows[focus][3],0.0)
            path=args.output/f'{width}-{selected}-{page}.png';fixture.canvas.convert('RGB').save(path)
            outside=[r for r in fixture.bounds if r['x']<0 or r['x']+r['width']>width or r['y']+r['height']>height]
            collisions=[]
            for i,a in enumerate(fixture.bounds):
                for b in fixture.bounds[i+1:]:
                    if a['y']==b['y'] and a['x']<b['x']+b['width'] and b['x']<a['x']+a['width']:
                        collisions.append((a['text'],b['text']))
            report['images'].append(dict(file=path.name,view=selected,page=page,width=width,height=height,
                                         outside=outside,collisions=collisions))
    report['passed']=all(not i['outside'] and not i['collisions'] for i in report['images'])
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
