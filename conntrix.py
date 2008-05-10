from visual import *
from random import uniform, randint

import pg
import sys


border = 0.2
conn_count = 80

def select_data():
  pgcnx = pg.connect('ulog2', 'localhost', 5432, None, None, 'ulog2', 'ulog2')
  connlist = pgcnx.query("SELECT flow_start_sec, flow_end_sec FROM ulog2_ct  where flow_end_sec IS NOT NULL ORDER BY flow_start_sec ASC LIMIT %s" % (conn_count)).getresult()
  return connlist
 
connlist = select_data()

scene.forward = (-0.25,-0.25,1)
scene.autocenter = 1

# Create some random boxes:
nodes = []
for t in range(conn_count):
  b = cylinder( pos=(connlist[t][0]-connlist[0][0],0,2*t) )
  b.color = b.icolor = (0.5,0.5,1)
  height = connlist[t][1] - connlist[t][0] - border
  b.axis = (height,0,0)
  nodes.append( b )
  b = cylinder( pos=(connlist[t][0]-connlist[0][0],0,2*t) )
  b.color = b.icolor = (0.5,1,0.5)
  b.axis = (border,0,0)
  nodes.append( b )
  b = cylinder( pos=(connlist[t][1]-connlist[0][0]-border,0,2*t) )
  b.color = b.icolor = (1,0.5,0.5)
  b.axis = (border,0,0)
  nodes.append( b )



# Draw a grid:
#for i in range(conn_count):
#    curve(pos=[(2*i-20,0,-20),(2*i-20,0,20)], color=color.cyan)       
#    curve(pos=[(-20,0,2*i-20),(20,0,2*i-20)], color=color.cyan)
field_length = max(connlist)[1] - connlist[0][0] + 4
field_width = conn_count*2 + 4
box(pos=(field_length/2,-2,field_width/2),width=field_width,length=field_length,height=1,color=(0.5,0.5,0.5))

# Drag and drop loop
drag = None
while 1:
  if scene.mouse.events:
    c = scene.mouse.getevent()
    if drag and (c.drop or c.click):   # drop the selected object
      dp = c.project(normal=scene.up)
      if dp: drag.pos = dp
      drag.color = drag.icolor
      drag = None
    elif c.pick and hasattr(c.pick,"icolor"):   # pick up the object
      drag = c.pick
      drag.color = color.white
  if drag:
    dp = scene.mouse.project(normal=scene.up)
    if dp: drag.pos = dp

  #for lnk in links: lnk.pos = lnk.ends
