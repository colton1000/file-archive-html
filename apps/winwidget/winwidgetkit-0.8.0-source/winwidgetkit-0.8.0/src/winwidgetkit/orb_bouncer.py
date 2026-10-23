import ctypes,random,tkinter as tk
from ctypes import wintypes
from .core import DesktopWidget

def work_area(root):
    try:
        rect=wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(48,0,ctypes.byref(rect),0):
            return rect.left,rect.top,rect.right,rect.bottom
    except Exception:
        pass
    return 0,0,root.winfo_screenwidth(),root.winfo_screenheight()-48

class BouncingOrb:
    COLORS=("#7dd3fc","#a78bfa","#fb7185","#fbbf24","#34d399")
    def __init__(self,root,mode="desktop",size=56,speed=5,color=None):
        self.root=root;self.mode=mode;self.size=size;self.speed=speed;self.color=color or random.choice(self.COLORS);self.dx=random.choice((-1,1))*speed;self.dy=random.choice((-1,1))*max(2,speed-1);self.closed=False
        left,top,right,bottom=work_area(root);self.x=random.randint(left,max(left,right-size));self.y=(bottom-size-2 if mode=="taskbar" else random.randint(top,max(top,bottom-size)))
        self.window=tk.Toplevel(root);self.window.overrideredirect(True);self.window.attributes("-topmost",True);self.window.config(bg="magenta");self.window.attributes("-transparentcolor","magenta");self.window.geometry(f"{size}x{size}+{self.x}+{self.y}")
        self.canvas=tk.Canvas(self.window,width=size,height=size,bg="magenta",highlightthickness=0);self.canvas.pack();self.canvas.create_oval(3,3,size-3,size-3,fill=self.color,outline="white",width=3);self.canvas.create_oval(size*.22,size*.15,size*.48,size*.38,fill="#ffffff",outline="")
        self.canvas.bind("<Button-1>",lambda e:self.reverse());self.tick()
    def reverse(self):self.dx=-self.dx;self.dy=-self.dy
    def tick(self):
        if self.closed:return
        left,top,right,bottom=work_area(self.root)
        if self.mode=="taskbar":
            self.x+=self.dx;self.y=bottom-self.size-2
            if self.x<=left or self.x+self.size>=right:self.dx=-self.dx;self.x=max(left,min(self.x,right-self.size))
        else:
            self.x+=self.dx;self.y+=self.dy
            if self.x<=left or self.x+self.size>=right:self.dx=-self.dx;self.x=max(left,min(self.x,right-self.size))
            if self.y<=top or self.y+self.size>=bottom:self.dy=-self.dy;self.y=max(top,min(self.y,bottom-self.size))
        try:self.window.geometry(f"+{int(self.x)}+{int(self.y)}");self.job=self.window.after(16,self.tick)
        except tk.TclError:self.closed=True
    def destroy(self):
        self.closed=True
        try:self.window.destroy()
        except tk.TclError:pass

class OrbControllerWidget(DesktopWidget):
    def __init__(self,app,*,orb_count=3,orb_mode="desktop",**kwargs):
        kwargs.setdefault("title","Orb Controller");kwargs.setdefault("width",315);kwargs.setdefault("height",235);kwargs.setdefault("color","#20243a");self.orbs=[];self.is_on=False
        saved=app.settings_for(kwargs["widget_id"]);self.orb_count=int(saved.get("orb_count",orb_count));self.orb_mode=saved.get("orb_mode",orb_mode);self.orb_size=int(saved.get("orb_size",56));self.orb_speed=int(saved.get("orb_speed",5));super().__init__(app,**kwargs)
        self.state=tk.Label(self.body,text="ORBS OFF",bg=self.color,fg="#fca5a5",font=("Segoe UI",18,"bold"));self.state.pack(pady=(14,7));self.toggle_button=tk.Button(self.body,text="Turn Orbs On",command=self.toggle);self.toggle_button.pack()
        row=tk.Frame(self.body,bg=self.color);row.pack(pady=10);tk.Label(row,text="Mode",bg=self.color,fg="white").grid(row=0,column=0,padx=3);self.mode_var=tk.StringVar(value=self.orb_mode);tk.OptionMenu(row,self.mode_var,"desktop","taskbar",command=self.update_options).grid(row=0,column=1,padx=3);tk.Label(row,text="Count",bg=self.color,fg="white").grid(row=0,column=2,padx=3);self.count_var=tk.IntVar(value=self.orb_count);tk.Spinbox(row,from_=1,to=20,width=4,textvariable=self.count_var,command=self.update_options).grid(row=0,column=3,padx=3)
        row2=tk.Frame(self.body,bg=self.color);row2.pack();tk.Label(row2,text="Size",bg=self.color,fg="white").pack(side="left");self.size_var=tk.IntVar(value=self.orb_size);tk.Scale(row2,from_=24,to=100,orient="horizontal",variable=self.size_var,bg=self.color,fg="white",highlightthickness=0,command=lambda v:self.update_options()).pack(side="left");tk.Label(row2,text="Speed",bg=self.color,fg="white").pack(side="left");self.speed_var=tk.IntVar(value=self.orb_speed);tk.Spinbox(row2,from_=2,to=12,width=3,textvariable=self.speed_var,command=self.update_options).pack(side="left")
    def toggle(self):
        if self.is_on:self.turn_off()
        else:self.turn_on()
    def turn_on(self):
        self.update_options();self.turn_off(log=False);self.orbs=[BouncingOrb(self.app.root,self.orb_mode,self.orb_size,self.orb_speed) for _ in range(self.orb_count)];self.is_on=True;self.state.config(text="ORBS ON",fg="#86efac");self.toggle_button.config(text="Turn Orbs Off");self.app.log("desktop_orbs_enabled",mode=self.orb_mode,count=self.orb_count)
    def turn_off(self,log=True):
        for orb in self.orbs:orb.destroy()
        self.orbs=[];self.is_on=False
        if hasattr(self,"state"):self.state.config(text="ORBS OFF",fg="#fca5a5");self.toggle_button.config(text="Turn Orbs On")
        if log:self.app.log("desktop_orbs_disabled")
    def update_options(self,*args):
        self.orb_mode=self.mode_var.get() if hasattr(self,"mode_var") else self.orb_mode;self.orb_count=max(1,min(20,int(self.count_var.get()))) if hasattr(self,"count_var") else self.orb_count;self.orb_size=int(self.size_var.get()) if hasattr(self,"size_var") else self.orb_size;self.orb_speed=max(2,min(12,int(self.speed_var.get()))) if hasattr(self,"speed_var") else self.orb_speed;self.app.save_widget(self)
    def on_color_changed(self,color):
        for child in self.body.winfo_children():
            try:child.config(bg=color)
            except tk.TclError:pass
    def get_settings(self):
        d=super().get_settings();d.update(orb_mode=self.orb_mode,orb_count=self.orb_count,orb_size=self.orb_size,orb_speed=self.orb_speed);return d
    def close(self):self.turn_off();super().close()
