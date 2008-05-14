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
COLOR_TCP = (0.5,0.7,0.5)
COLOR_UDP = (0.5, 0.5, 0.7)
START_COLOR = (0.5,1,0.5)
END_COLOR = (1,0.5,0.5)
HIGHLIGHT_COLOR = (1,1,1)
BOX_COLOR = (0.5,0.5,0.5)
RADIUS = 10 
BORDER = 0.2
GRADUATION = 10

visual.scene.width = 800
visual.scene.height = 600
visual.scene.forward = (0.25,-10.25,-10)
visual.scene.autocenter = 1

class connection(visual.cylinder):
    """
    Store information about a connection and related object.
    """

    def __init__(self, start, end, state, **kargs):
        visual.cylinder.__init__(self, **kargs)
        self.pos = (start,0, 0)
        self.color = self.icolor = COLOR
        self.radius = RADIUS
        self.axis = (end - start,0,0)
        self.label = "None"
        self.state = state
        self.normal()

    def ordonate(self, index):
        self.z = (3*RADIUS)*index
        self.label.z = (3*RADIUS)*index

    def set_label(self, ip_dest, port_dest, bytes_in, bytes_out):
        if (self.state == 1):
            self.label = visual.label(pos=self.pos, xoffset = -10, yoffset = 10,  text='%s:%d\n%d/%d bits' % (ip_dest, port_dest, bytes_in, bytes_out))
        elif (self.state == 4):
            self.label = visual.label(pos=self.pos, xoffset = -10, yoffset = 10,  text='%s:%d\n%d/%d bits\n%f sec' % (ip_dest, port_dest, bytes_in, bytes_out, self.axis.x))
        self.label.visible = 0
        self.set_port(port_dest)

    # FIXME: has to be improved
    def set_port(self, port):
        self.dport = port

    def normal(self):
        if (self.state == 1):
            self.color = self.icolor = COLOR_TCP
        elif (self.state == 4):
            self.color = self.icolor = COLOR_UDP

    def highlight(self):
        self.color = HIGHLIGHT_COLOR
        self.label.visible = 1

class connections(list):
    """
    Connections list with visual elements
    """

    def from_pgsql(self, count, **kargs):
#        conns = pgcnx.query("SELECT flow_start_sec+flow_start_usec/1000000 AS start, flow_end_sec+flow_end_usec/1000000 AS end, orig_ip_daddr_str, orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen, orig_ip_protocol FROM ulog2_ct  where flow_end_sec IS NOT NULL ORDER BY flow_start_sec DESC LIMIT %s" % (count)).getresult()
        conns = pgcnx.query("SELECT flow_start_sec+flow_start_usec/1000000 AS start, flow_end_sec+flow_end_usec/1000000 AS end, orig_ip_daddr_str, orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen, orig_ip_protocol, ct_event FROM ulog2_ct ORDER BY flow_start_sec DESC LIMIT %s" % (count)).getresult()
        t = 0
        self.count = len(conns)
        conns.sort(lambda x, y: cmp(x[0], y[0]))
        self.inittime = conns[0][0]
        ctime = time.time()
        for elt in conns:
            if (elt[1]):
                conn = connection(elt[0]-self.inittime, elt[1]-self.inittime,elt[7])
            else:
                conn = connection(elt[0]-self.inittime, ctime-self.inittime,elt[7])
            conn.set_label(elt[2], elt[3], elt[4], elt[5])
            conn.ordonate(t)
            self.append(conn)
            t += 1

    def length(self):
        return max(self).axis.x+max(self).pos.x

    def clear(self):
        self = []
        for obj in visual.scene.objects:
            obj.visible = 0

    def plate(self):
        field_length =  self.length() + 2*RADIUS
        field_width = 3*RADIUS*self.count + 10
        visual.box(pos = (field_length/2,-(RADIUS+1),field_width/2), width = field_width, length = field_length, height = 1, color = BOX_COLOR)
        for i in range(GRADUATION):
            visual.curve(pos=[(field_length/GRADUATION*i,-(RADIUS+1)+1,0), (field_length/GRADUATION*i,-(RADIUS+1)+1,field_width)])
            ctime = time.strftime("%H:%M:%S", time.localtime(self.inittime + GRADUATION*i))
            visual.label(pos=(field_length/GRADUATION*i,-(RADIUS+1)+1,0), text = '%s' % (ctime), border = 5, yoffset = 1.5*RADIUS)

def main_loop():
    visual.rate(50)
    objlist = []
# Drag and drop loop
    while 1:
        if visual.scene.mouse.events:
            c = visual.scene.mouse.getevent()
            if c.pick and hasattr(c.pick,"icolor"):   # pick up the object
                if not c.shift:
                    for object in objlist:
                        object.normal()
                        object.label.visible = 0
                objlist = []
                if (hasattr(c.pick, "label")):
                    objlist.append(c.pick)
                    c.pick.highlight()
        if visual.scene.kb.keys: # is there an event waiting to be processed?
            s = visual.scene.kb.getkey() # obtain keyboard information
            if (len(s) == 1):
                if (s == 'p') and (len(objlist) == 1):
                    highlight = objlist[0]
                    for conn in connlist:
                        if hasattr(conn, "dport") and  hasattr(highlight, "dport") and conn.dport == highlight.dport:
                            objlist.append(conn)
                            conn.highlight()

                elif (s == 'r'):
                    connlist.clear()
                    connlist.from_pgsql(CONN_COUNT)
                    connlist.plate()


# Init connections list
pgcnx = pg.connect('ulog2', 'localhost', 5432, None, None, 'ulog2', 'ulog2')
connlist = connections()
connlist.from_pgsql(CONN_COUNT)
connlist.plate()
main_loop()

