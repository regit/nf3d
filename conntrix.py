#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright(C) 2008 Eric Leblond

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
"""

from visual import *
from random import uniform, randint

import pg
import sys


CONN_COUNT = 40
COLOR = (0.5,0.5,1)
START_COLOR = (0.5,1,0.5)
END_COLOR = (1,0.5,0.5)
HIGHLIGHT_COLOR = (1,1,1)
BOX_COLOR = (0.5,0.5,0.5)
RADIUS = 2
BORDER = 0.2

def select_data():
  pgcnx = pg.connect('ulog2', 'localhost', 5432, None, None, 'ulog2', 'ulog2')
  connlist = pgcnx.query("SELECT flow_start_sec+flow_start_usec/1000000 AS start, flow_end_sec+flow_end_sec/1000000 AS end, orig_ip_daddr_str, orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen FROM ulog2_ct  where flow_end_sec IS NOT NULL ORDER BY flow_start_sec ASC LIMIT %s" % (CONN_COUNT)).getresult()
  return connlist
 
connlist = select_data()

scene.forward = (0.25,0.25,10)
scene.autocenter = 1

conns = []
for t in range(CONN_COUNT):
  conn = cylinder( pos=(connlist[t][0]-connlist[0][0],0,(3*RADIUS)*t) )
  conn.color = conn.icolor = COLOR
  conn.radius = RADIUS
  height = connlist[t][1] - connlist[t][0] - BORDER
  conn.axis = (height,0,0)
  conn.label = label(pos=conn.pos, xoffset = 10, yoffset = 10,  text='%s:%d\n%d/%d bits\n%f sec' % (connlist[t][2], connlist[t][3], connlist[t][4], connlist[t][5],connlist[t][1] - connlist[t][0]))
  conn.dport = connlist[t][3]
  conn.label.visible = 0
  conns.append (conn)
  b = cylinder( pos=(connlist[t][0]-connlist[0][0],0,(3*RADIUS)*t) )
  b.radius = RADIUS
  b.color = b.icolor = START_COLOR
  b.axis = (BORDER,0,0)
  b = cylinder( pos=(connlist[t][1]-connlist[0][0]-BORDER,0,(3*RADIUS)*t) )
  b.radius = RADIUS
  b.color = b.icolor = END_COLOR
  b.axis = (BORDER,0,0)



# Draw a grid:
#for i in range(CONN_COUNT):
#    curve(pos=[(2*i-20,0,-20),(2*i-20,0,20)], color=color.cyan)       
#    curve(pos=[(-20,0,2*i-20),(20,0,2*i-20)], color=color.cyan)
field_length = max(connlist)[1] - connlist[0][0] + 2*RADIUS 
field_width = CONN_COUNT*3*RADIUS + 10
box(pos=(field_length/2,-2,field_width/2),width=field_width,length=field_length,height=1,color=BOX_COLOR)

objlist = []
# Drag and drop loop
while 1:
  if scene.mouse.events:
    c = scene.mouse.getevent()
    if c.pick and hasattr(c.pick,"icolor"):   # pick up the object
      if not c.shift:
	 for object in objlist:
            object.label.visible=0
	    object.color = object.icolor = COLOR
	 objlist = []
      if (hasattr(c.pick, "label")):
         objlist.append(c.pick)
	 c.pick.label.visible = 1
         c.pick.color = HIGHLIGHT_COLOR
  if scene.kb.keys: # is there an event waiting to be processed?
        s = scene.kb.getkey() # obtain keyboard information
	if len(s) == 1:
	  if s == 'p' and len(objlist) == 1:
             highlight = objlist[0]
             for conn in conns:
		if conn.dport == highlight.dport:
		    objlist.append(conn)
		    conn.color = HIGHLIGHT_COLOR
		    conn.label.visible = 1
