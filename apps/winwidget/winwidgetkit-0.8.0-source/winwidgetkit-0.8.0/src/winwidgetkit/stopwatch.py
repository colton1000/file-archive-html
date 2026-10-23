import time, tkinter as tk
from .base import DesktopWidget
class StopwatchWidget(DesktopWidget):
    def __init__(self,app,**kwargs):
        kwargs.setdefault('title','Stopwatch');kwargs.setdefault('width',280);kwargs.setdefault('height',190)
        s=app.settings_for(kwargs['widget_id']);self.elapsed=float(s.get('elapsed',0));self.running=False;self.started_at=0;self.laps=s.get('laps',[])
        super().__init__(app,**kwargs)
        self.time_label=tk.Label(self.body,text='00:00.00',bg=self.color,fg='white',font=('Consolas',28,'bold'));self.time_label.pack(pady=(16,8))
        row=tk.Frame(self.body,bg=self.color);row.pack();self.start_btn=tk.Button(row,text='Start',command=self.toggle);self.start_btn.pack(side='left',padx=4)
        tk.Button(row,text='Lap',command=self.lap).pack(side='left',padx=4);tk.Button(row,text='Reset',command=self.reset).pack(side='left',padx=4)
        self.lap_label=tk.Label(self.body,text='',bg=self.color,fg='#7dd3fc',font=('Segoe UI',9));self.lap_label.pack(pady=8)
        self._tick()
    def current(self):return self.elapsed+(time.perf_counter()-self.started_at if self.running else 0)
    def toggle(self):
        if self.running:self.elapsed=self.current();self.running=False;self.start_btn.config(text='Start');self.app.log('stopwatch_stopped',widget_id=self.widget_id,seconds=round(self.elapsed,3))
        else:self.started_at=time.perf_counter();self.running=True;self.start_btn.config(text='Stop');self.app.log('stopwatch_started',widget_id=self.widget_id)
        self.app.save_widget(self)
    def lap(self):
        value=self.current();self.laps.append(value);self.laps=self.laps[-5:];self._laps();self.app.save_widget(self);self.app.log('stopwatch_lap',widget_id=self.widget_id,seconds=round(value,3))
    def reset(self):self.running=False;self.elapsed=0;self.laps=[];self.start_btn.config(text='Start');self._laps();self.app.save_widget(self);self.app.log('stopwatch_reset',widget_id=self.widget_id)
    def _fmt(self,s):
        minutes=int(s//60);seconds=int(s%60);hundredths=int((s-int(s))*100);return f'{minutes:02d}:{seconds:02d}.{hundredths:02d}'
    def _laps(self):self.lap_label.config(text='  '.join(f'Lap {i+1}: {self._fmt(v)}' for i,v in enumerate(self.laps[-3:])))
    def _tick(self):
        if self.window.winfo_exists():self.time_label.config(text=self._fmt(self.current()));self.window.after(30,self._tick)
    def on_color_changed(self,c):self.time_label.config(bg=c);self.lap_label.config(bg=c)
    def get_settings(self):
        d=super().get_settings();d.update(elapsed=self.current(),laps=self.laps);return d
