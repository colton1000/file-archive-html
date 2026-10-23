import math,tkinter as tk
from .base import DesktopWidget
class WaterWidget(DesktopWidget):
 def __init__(self,app,**kw):kw.setdefault('title','Water');kw.setdefault('color','#082f49');self.p=[0.0]*24;self.v=[0.0]*24;self.shift=0;super().__init__(app,**kw);self.canvas=tk.Canvas(self.body,bg=self.color,highlightthickness=0);self.canvas.pack(fill='both',expand=True);self.tick()
 def on_move(self,dx,dy):
  self.shift-=dx*.2
  for i in range(24):self.v[i]+=(i/23-.5)*self.shift*.02
 def tick(self):
  try:
   nv=[]
   for i in range(24):l=self.p[i-1] if i else self.p[i];r=self.p[i+1] if i<23 else self.p[i];nv.append((self.v[i]-self.p[i]*.05+(l+r-2*self.p[i])*.2)*.96)
   self.v=nv;self.p=[a+b for a,b in zip(self.p,self.v)];self.shift*=.9;self.draw();self.window.after(20,self.tick)
  except tk.TclError:pass
 def draw(self):
  c=self.canvas;c.delete('all');w,h=max(20,c.winfo_width()),max(20,c.winfo_height());pts=[0,h]
  for i,y in enumerate(self.p):pts.extend((w*i/23,h*.38+y+math.sin(i*.5)*1.5))
  pts.extend((w,h));c.create_polygon(pts,fill='#38bdf8',outline='');c.create_line(*pts[2:-2],fill='#bae6fd',width=3,smooth=True)
