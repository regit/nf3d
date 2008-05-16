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
import getopt
import time

REFRESH = 1
COLOR = (0.5,0.5,1)
COLOR_TCP = (0.5,0.7,0.5)
COLOR_UDP = (0.5, 0.5, 0.7)
START_COLOR = (0.5,1,0.5)
END_COLOR = (1,0.5,0.5)
HIGHLIGHT_COLOR = (1,1,1)
BOX_COLOR = (0.5,0.5,0.5)
RADIUS = 10 
BORDER = 0.2
GRADUATION = 5 

visual.scene.width = 800
visual.scene.height = 600
visual.scene.forward = (0.25,-10.25,-10)
visual.scene.autocenter = 1

filters_list = { 'p': 'orig_l4_dport', 'd': 'orig_ip_daddr_str', 's': 'orig_ip_saddr_str', 'P': 'orig_l4_sport' }

class connection(visual.cylinder):
    """
    Store information about a connection and related object.
    """

    def __init__(self, start, end, conn, **kargs):
        visual.cylinder.__init__(self, **kargs)
        self.pos = (start,0, 0)
        self.color = self.icolor = COLOR
        self.radius = RADIUS
        self.axis = (end - start,0,0)
        self.conn = conn
        self.set_label()
        self.normal()

    def ordonate(self, index):
        self.z = (3*RADIUS)*index
        self.label.z = (3*RADIUS)*index

    def set_label(self):
        txtlabel = ''
        if (self.conn["orig_ip_protocol"] in (6,17)):
            txtlabel = 'SRC: %s:%d\nDST: %s:%d\n' % (self.conn["orig_ip_saddr_str"], self.conn["orig_l4_sport"], self.conn["orig_ip_daddr_str"], self.conn["orig_l4_dport"])
        if (self.conn["orig_ip_protocol"] == 6):
            txtlabel += 'PROTO: TCP'
        elif (self.conn["orig_ip_protocol"] == 17):
            txtlabel += 'PROTO: UDP'
        elif (self.conn["orig_ip_protocol"] == 1):
            txtlabel += 'PROTO: ICMP'
        if (self.conn["ct_event"] == 1):
            self.label = visual.label(pos=self.pos, xoffset = -10, yoffset = 10,  text='%s' % (txtlabel))
        elif (self.conn["ct_event"] == 4):
            self.label = visual.label(pos=self.pos, xoffset = -10, yoffset = 10,  text='%s\nIN: %d, OUT: %d bits\nDURATION: %f sec' % (txtlabel, self.conn["reply_raw_pktlen"],self.conn["orig_raw_pktlen"]  , self.axis.x))
        self.label.visible = 0
    def set_axis(self, timestamp):
        self.axis = (timestamp, 0, 0)

    def normal(self):
        if (self.conn["ct_event"] == 1):
            self.color = self.icolor = COLOR_TCP
        elif (self.conn["ct_event"] == 4):
            self.color = self.icolor = COLOR_UDP

    def highlight(self):
        self.color = HIGHLIGHT_COLOR
        self.label.visible = 1

class connections(list):
    """
    Connections list with visual elements
    """

    def __init__(self, start, end, duration, **kargs):
        list.__init__(self, **kargs)
        self.starttime = start
        self.endtime = end
        if (self.endtime < self.starttime):
            print "End before beginning, exiting"
            sys.exit(1)
        self.duration = duration
        if (self.starttime and self.endtime):
            self.duration = self.endtime - self.starttime
        if (not self.starttime and not self.endtime):
            self.mode = "duration"
        else:
            self.mode = "period"
        if (not self.endtime and self.starttime and self.duration):
            self.endtime = self.starttime + self.duration

    def from_pgsql(self, pgcnx, **kargs):
        if (self.mode == "period"):
            strquery = "SELECT flow_start_sec+flow_start_usec/1000000 AS start, \
            flow_end_sec+flow_end_usec/1000000 AS end, orig_ip_daddr_str, \
            orig_ip_saddr_str, orig_l4_sport, \
            orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen, orig_ip_protocol,\
            ct_event FROM ulog2_ct WHERE \
            (flow_end_sec > %f AND flow_start_sec < %f) \
            OR \
            (flow_end_sec IS NULL AND flow_start_sec < %f)\
            ORDER BY flow_start_sec DESC" % (self.starttime, self.endtime, self.endtime) 
        elif (self.mode == "duration"):
            ctime = time.time()
            strquery = "SELECT flow_start_sec+flow_start_usec/1000000 AS start, \
            flow_end_sec+flow_end_usec/1000000 AS end, orig_ip_daddr_str,\
            orig_ip_saddr_str, orig_l4_sport, \
            orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen, orig_ip_protocol,\
            ct_event FROM ulog2_ct WHERE flow_end_sec > %f OR flow_end_sec IS NULL\
            ORDER BY flow_start_sec DESC" % (ctime - self.duration) 
            self.starttime = ctime - self.duration
            self.endtime = ctime

        conns = pgcnx.query(strquery).dictresult()
        t = 0
        self.count = len(conns)
        print "Found %d connections" % (self.count)
        conns.sort(lambda x, y: cmp(x["start"], y["start"]))
        for elt in conns:
            if (elt["end"]):
                conn = connection(max(0, elt["start"]-self.starttime), min(elt["end"]-self.starttime, self.duration), elt)
            else:
                conn = connection(max(0,elt["start"]-self.starttime), self.endtime-self.starttime,elt)
            conn.ordonate(t)
            self.append(conn)
            t += 1

    def length(self):
        return self.endtime - self.starttime

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
            ctime = time.strftime("%H:%M:%S", time.localtime(self.starttime + GRADUATION*i))
            visual.label(pos=(field_length/GRADUATION*i,-(RADIUS+1)+1,0), text = '%s' % (ctime), border = 5, yoffset = 1.5*RADIUS)

    def refresh(self, pgnx):
        self.clear()
        self.from_pgsql(pgnx)
        self.plate()

    def highlight(self, highlight, filter):
        print 'filter : %s' % filter
        objlist = []
        objlist.append(highlight)
        for conn in self:
            if conn.conn[filter] == highlight.conn[filter]:
                objlist.append(conn)
                conn.highlight()
        return objlist


def normalize_objs(objlist):
    for object in objlist:
        object.normal()
        object.label.visible = 0
    return []

def main_loop(connlist, pgcnx):
    visual.rate(50)
    objlist = []
# Drag and drop loop
    while 1:
        if visual.scene.mouse.events:
            c = visual.scene.mouse.getevent()
            if c.pick and hasattr(c.pick,"icolor"):   # pick up the object
                if not c.shift:
                    objlist = normalize_objs(objlist)
                if (hasattr(c.pick, "label")):
                    objlist.append(c.pick)
                    c.pick.highlight()
                else:
                    objlist = normalize_objs(objlist)
        if visual.scene.kb.keys: # is there an event waiting to be processed?
            s = visual.scene.kb.getkey() # obtain keyboard information
            if (len(s) == 1):
                if (s in filters_list) and (len(objlist) == 1):
                    objlist = connlist.highlight(objlist[0], filters_list[s])
                elif (s == 'r'):
                    connlist.refresh(pgcnx)
                elif (s == 'c'):
                    normalize_objs(objlist)
                    

def usage():
    print "conntrix.py [-h] [-s START] [-e END] [-d DURATION]\n"


def main():
    start = 0
    end = 0
    duration = 600
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:e:d:", ["help", "start=", "end=", "duration="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-s", "--start"):
            start = int(a)
        elif o in ("-e", "--end"):
            end = int(a)
        elif o in ("-d", "--duration"):
            duration = int(a)
        else:
            assert False, "unhandled option"

    # Init connections list
    pgcnx = pg.connect('ulog2', 'localhost', 5432, None, None, 'ulog2', 'ulog2')
    connlist = connections(start, end, duration)
    connlist.from_pgsql(pgcnx)
    connlist.plate()
    main_loop(connlist, pgcnx)

if __name__ == "__main__":
    main()

