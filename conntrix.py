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

import visual
from random import uniform, randint

import pg
import sys
import time

CONN_COUNT = 40
COLOR = (0.5,0.5,1)
START_COLOR = (0.5,1,0.5)
END_COLOR = (1,0.5,0.5)
HIGHLIGHT_COLOR = (1,1,1)
BOX_COLOR = (0.5,0.5,0.5)
RADIUS = 10 
BORDER = 0.2
GRADUATION = 300

visual.scene.width = 800
visual.scene.height = 600
visual.scene.forward = (0.25,-10.25,-10)
visual.scene.autocenter = 1

class connection(visual.cylinder):
    """
    Store information about a connection and related object.
    """

    def __init__(self, start, end, **kargs):
        visual.cylinder.__init__(self, **kargs)
        self.pos = (start,0, 0)
        self.color = self.icolor = COLOR
        self.radius = RADIUS
        self.axis = (end - start,0,0)
        self.label = "None"

    def ordonate(self, index):
        self.z = (3*RADIUS)*index
        self.label.z = (3*RADIUS)*index

    def set_label(self, ip_dest, port_dest, bytes_in, bytes_out):
        self.label = visual.label(pos=self.pos, xoffset = 10, yoffset = 10,  text='%s:%d\n%d/%d bits\n%f sec' % (ip_dest, port_dest, bytes_in, bytes_out, self.axis.x))
        self.label.visible = 0
        self.set_port(port_dest)

    # FIXME: has to be improved
    def set_port(self, port):
        self.dport = port

class connections(list):
    """
    Connections list with visual elements
    """

    def from_pgsql(self, count, **kargs):
        pgcnx = pg.connect('ulog2', 'localhost', 5432, None, None, 'ulog2', 'ulog2')
        conns = pgcnx.query("SELECT flow_start_sec+flow_start_usec/1000000 AS start, flow_end_sec+flow_end_sec/1000000 AS end, orig_ip_daddr_str, orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen FROM ulog2_ct  where flow_end_sec IS NOT NULL ORDER BY flow_start_sec ASC LIMIT %s" % (count)).getresult()
        t = 0
        self.count = count
        self.inittime = conns[0][0]
        for elt in conns:
            conn = connection(elt[0]-self.inittime, elt[1]-self.inittime)
            conn.set_label(elt[2], elt[3], elt[4], elt[5])
            conn.ordonate(t)
            self.append(conn)
            t += 1

    def length(self):
        return max(self).axis.x+max(self).pos.x

    def plate(self):
        field_length =  self.length() + 2*RADIUS
        field_width = 3*RADIUS*self.count + 10
        visual.box(pos = (field_length/2,-(RADIUS+1),field_width/2), width = field_width, length = field_length, height = 1, color = BOX_COLOR)
        for i in range(field_length/GRADUATION):
            visual.curve(pos=[(GRADUATION*i,-(RADIUS+1)+1,0), (GRADUATION*i,-(RADIUS+1)+1,field_width)])
            ctime = time.strftime("%H:%M:%S", time.localtime(self.inittime + GRADUATION*i))
            visual.label(pos=(GRADUATION*i,-(RADIUS+1)+1,0), text = '%s' % (ctime), height = 2, yoffset = 1.5*RADIUS)



# Init connections list
connlist = connections()
connlist.from_pgsql(CONN_COUNT)
connlist.plate()

objlist = []
# Drag and drop loop
while 1:
    if visual.scene.mouse.events:
        c = visual.scene.mouse.getevent()
        if c.pick and hasattr(c.pick,"icolor"):   # pick up the object
            if not c.shift:
                for object in objlist:
                    object.color = object.icolor = COLOR
                    object.label.visible = 0
            objlist = []
            if (hasattr(c.pick, "label")):
                objlist.append(c.pick)
                c.pick.label.visible = 1
                c.pick.color = HIGHLIGHT_COLOR
    if visual.scene.kb.keys: # is there an event waiting to be processed?
        s = visual.scene.kb.getkey() # obtain keyboard information
        if (len(s) == 1):
            if (s == 'p') and (len(objlist) == 1):
                highlight = objlist[0]
                for conn in connlist:
                    if hasattr(conn, "dport") and  hasattr(highlight, "dport") and conn.dport == highlight.dport:
                        objlist.append(conn)
                        conn.color = HIGHLIGHT_COLOR
                        conn.label.visible = 1
