#!/usr/bin/python

from visual import *
from random import uniform, randint

import pg
import sys


border = 0.2
conn_count = 40

def select_data():
  pgcnx = pg.connect('ulog2', 'localhost', 5432, None, None, 'ulog2', 'ulog2')
  connlist = pgcnx.query("SELECT flow_start_sec+flow_start_usec/1000000 AS start, flow_end_sec+flow_end_sec/1000000 AS end, orig_ip_daddr_str, orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen FROM ulog2_ct  where flow_end_sec IS NOT NULL ORDER BY flow_start_sec ASC LIMIT %s" % (conn_count)).getresult()
  return connlist
 
connlist = select_data()

scene.forward = (-0.25,-0.25,1)
scene.autocenter = 1

# Create some random boxes:
conns = []
for t in range(conn_count):
  conn = cylinder( pos=(connlist[t][0]-connlist[0][0],0,2*t) )
  conn.color = conn.icolor = (0.5,0.5,1)
  height = connlist[t][1] - connlist[t][0] - border
  conn.axis = (height,0,0)
  conn.label = '%s:%d\n%d/%d bits\n%f sec' % (connlist[t][2], connlist[t][3], connlist[t][4], connlist[t][5],connlist[t][1] - connlist[t][0])
  conns.append (conn)
  b = cylinder( pos=(connlist[t][0]-connlist[0][0],0,2*t) )
  b.color = b.icolor = (0.5,1,0.5)
  b.axis = (border,0,0)
  b = cylinder( pos=(connlist[t][1]-connlist[0][0]-border,0,2*t) )
  b.color = b.icolor = (1,0.5,0.5)
  b.axis = (border,0,0)



# Draw a grid:
#for i in range(conn_count):
#    curve(pos=[(2*i-20,0,-20),(2*i-20,0,20)], color=color.cyan)       
#    curve(pos=[(-20,0,2*i-20),(20,0,2*i-20)], color=color.cyan)
field_length = max(connlist)[1] - connlist[0][0] + 4
field_width = conn_count*2 + 4
box(pos=(field_length/2,-2,field_width/2),width=field_width,length=field_length,height=1,color=(0.5,0.5,0.5))

prevlabel = None
prevobject = None
# Drag and drop loop
while 1:
  if scene.mouse.events:
    c = scene.mouse.getevent()
    if c.pick and hasattr(c.pick,"icolor"):   # pick up the object
      if (hasattr(prevlabel, "pos")):
	 prevlabel.visible = 0
      if (hasattr(prevobject, "pos")):
	 prevobject.color = prevobject.icolor = (0.5,0.5,1)
      prevobject = c.pick
      c.pick.color = (1,1,1)
      prevlabel = label(pos=c.pick.pos, xoffset = 1, yoffset = 1, text = c.pick.label)
