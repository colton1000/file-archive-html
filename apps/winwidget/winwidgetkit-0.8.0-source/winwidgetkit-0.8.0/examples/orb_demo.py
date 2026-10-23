from winwidgetkit import WidgetApp,OrbControllerWidget
app=WidgetApp(app_name='Bouncing Orb Demo')
OrbControllerWidget(app,widget_id='orb-controller',orb_count=3,orb_mode='desktop')
app.run()
