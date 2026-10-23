import calendar,importlib.util,os,random,time,tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import colorchooser,filedialog,simpledialog
from .base import DesktopWidget
class CalendarWidget(DesktopWidget):
 def __init__(self,app,*,holidays=None,**kw):
  today=date.today();s=app.settings_for(kw['widget_id']);self.year=s.get('year',today.year);self.month=s.get('month',today.month);self.holidays=s.get('holidays',holidays or {});kw.setdefault('title','Calendar');kw.setdefault('width',340);kw.setdefault('height',310);super().__init__(app,**kw);nav=tk.Frame(self.body,bg=self.color);nav.pack(fill='x');tk.Button(nav,text='<',command=lambda:self.change(-1)).pack(side='left');self.label=tk.Label(nav,bg=self.color,fg='white');self.label.pack(side='left',expand=True);tk.Button(nav,text='>',command=lambda:self.change(1)).pack(side='right');self.grid=tk.Frame(self.body,bg=self.color);self.grid.pack(fill='both',expand=True);self.menu.insert_command(0,label='Add holiday',command=self.add_holiday);self.draw()
 def change(self,n):m=self.month+n;self.year+=(m-1)//12;self.month=(m-1)%12+1;self.draw();self.app.save_widget(self)
 def add_holiday(self):
  key=simpledialog.askstring('Holiday','Date YYYY-MM-DD:',parent=self.window)
  try:d=date.fromisoformat(key or '')
  except ValueError:return
  name=simpledialog.askstring('Holiday','Name:',parent=self.window) or 'Holiday';color=colorchooser.askcolor('#ef4444',parent=self.window)[1] or '#ef4444';self.holidays[key]={'name':name,'color':color};self.year,self.month=d.year,d.month;self.draw();self.app.save_widget(self)
 def draw(self):
  for w in self.grid.winfo_children():w.destroy()
  self.label.config(text=f'{calendar.month_name[self.month]} {self.year}')
  for c,n in enumerate(('Mon','Tue','Wed','Thu','Fri','Sat','Sun')):tk.Label(self.grid,text=n,bg=self.color,fg='#7dd3fc').grid(row=0,column=c,sticky='nsew')
  for r,week in enumerate(calendar.Calendar().monthdayscalendar(self.year,self.month),1):
   for c,day in enumerate(week):key=f'{self.year:04d}-{self.month:02d}-{day:02d}' if day else '';h=self.holidays.get(key);tk.Label(self.grid,text=(str(day)+(' ★' if h else '')) if day else '',bg=h['color'] if h else self.color,fg='white').grid(row=r,column=c,sticky='nsew')
  for c in range(7):self.grid.columnconfigure(c,weight=1)
 def get_settings(self):d=super().get_settings();d.update(year=self.year,month=self.month,holidays=self.holidays);return d
class ShortcutWidget(DesktopWidget):
 def __init__(self,app,*,target=None,label=None,**kw):
  kw.setdefault('title','Shortcut');super().__init__(app,**kw);self.target=app.settings_for(self.widget_id).get('target',target or '');self.lab=tk.Label(self.body,text='↗\n'+(label or 'Choose a file'),bg=self.color,fg='white',font=('Segoe UI',16,'bold'));self.lab.pack(expand=True);self.lab.bind('<Double-1>',lambda e:self.open());self.menu.insert_command(0,label='Select target',command=self.select)
 def select(self):
  value=filedialog.askopenfilename(parent=self.window)
  if value:self.target=value;self.lab.config(text='↗\n'+Path(value).name);self.app.save_widget(self)
 def open(self):
  if not self.target:return self.select()
  os.startfile(self.target)
 def on_color_changed(self,c):self.lab.config(bg=c)
 def get_settings(self):d=super().get_settings();d['target']=self.target;return d
class NoteWidget(DesktopWidget):
 def __init__(self,app,*,max_notes=5,**kw):
  kw.setdefault('title','Notes');kw.setdefault('color','#f4d35e');kw.setdefault('width',400);kw.setdefault('height',300);s=app.settings_for(kw['widget_id']);self.maximum=s.get('maximum',max_notes);self.notes=s.get('notes',['']);self.index=min(s.get('index',0),len(self.notes)-1);super().__init__(app,**kw);bar=tk.Frame(self.body,bg=self.color);bar.pack(fill='x');tk.Button(bar,text='<',command=lambda:self.switch(-1)).pack(side='left');self.count=tk.Label(bar,bg=self.color);self.count.pack(side='left',expand=True);tk.Button(bar,text='+',command=self.add).pack(side='right');tk.Button(bar,text='>',command=lambda:self.switch(1)).pack(side='right');self.text=tk.Text(self.body,wrap='word',bg='#fff6b7');self.text.pack(fill='both',expand=True,padx=4,pady=4);self.text.bind('<KeyRelease>',lambda e:self.save());self.load()
 def save(self):self.notes[self.index]=self.text.get('1.0','end-1c');self.app.save_widget(self)
 def load(self):self.text.delete('1.0','end');self.text.insert('1.0',self.notes[self.index]);self.count.config(text=f'{self.index+1}/{len(self.notes)} Max {self.maximum}')
 def switch(self,n):self.notes[self.index]=self.text.get('1.0','end-1c');self.index=(self.index+n)%len(self.notes);self.load()
 def add(self):
  if len(self.notes)<self.maximum:self.notes.append('');self.index=len(self.notes)-1;self.load();self.app.save_widget(self)
 def get_settings(self):
  if hasattr(self,'text'):self.notes[self.index]=self.text.get('1.0','end-1c')
  d=super().get_settings();d.update(notes=self.notes,index=self.index,maximum=self.maximum);return d
class FocusOrbWidget(DesktopWidget):
 def __init__(self,app,*,minutes=25,**kw):
  kw.setdefault('title','Focus Orb');self.remaining=minutes*60;self.running=False;self.started=0;super().__init__(app,**kw);self.label=tk.Label(self.body,bg=self.color,fg='white',font=('Segoe UI',25,'bold'));self.label.pack(expand=True);tk.Button(self.body,text='Start / Pause',command=self.toggle).pack(pady=8);self.tick()
 def toggle(self):
  if self.running:self.remaining=max(0,self.remaining-(time.perf_counter()-self.started));self.running=False
  else:self.started=time.perf_counter();self.running=True
 def tick(self):r=max(0,self.remaining-(time.perf_counter()-self.started if self.running else 0));self.label.config(text=f'◉\n{int(r//60):02d}:{int(r%60):02d}');self.window.after(200,self.tick)
class MagicOrbWidget(DesktopWidget):
 def __init__(self,app,**kw):kw.setdefault('title','Magic Orb');kw.setdefault('color','#241044');super().__init__(app,**kw);self.label=tk.Label(self.body,text='ASK',bg='#3b1773',fg='white',font=('Segoe UI',24,'bold'));self.label.pack(fill='both',expand=True,padx=30,pady=20);tk.Button(self.body,text='Ask',command=lambda:self.label.config(text=random.choice(('YES','NO')))).pack()
class CombinedWidget(DesktopWidget):
 def __init__(self,app,*,panels=None,columns=2,**kw):
  kw.setdefault('title','Combined Widget');kw.setdefault('width',480);kw.setdefault('height',330);super().__init__(app,**kw)
  for title,builder in panels or []:frame=tk.LabelFrame(self.body,text=title);frame.pack(side='left',fill='both',expand=True);builder(frame,self)
class CustomWidget(DesktopWidget):
 def __init__(self,app,*,build,**kw):super().__init__(app,**kw);build(self)
class ScriptWidget(CustomWidget):
 def __init__(self,app,*,script_path,**kw):path=Path(script_path);spec=importlib.util.spec_from_file_location('external_widget',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);super().__init__(app,build=module.build,**kw)
