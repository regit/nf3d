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

# SETUP YOUR DATABASE HERE
DATABASE='ulog2'
HOST = 'localhost'
PORT = 5432
LOGIN ='ulog2'
PASSWORD ='ulog2'

import visual
from random import uniform, randint

import pg
import sys
import getopt
import time

TIME_STEP = 60

COLOR = (0.5,0.5,1)
COLOR_TCP = (0.5,0.7,0.5)
COLOR_UDP = (0.5, 0.5, 0.7)
START_COLOR = (0.5,1,0.5)
END_COLOR = (1,0.5,0.5)
HIGHLIGHT_COLOR = (1,1,1)
BOX_COLOR = (0.5,0.5,0.5)
RADIUS = 10 
BORDER = 0.2
GRADUATION = 12
TICK = 4

visual.scene.title = "fwtron"
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

    def set_level(self, level):
        self.pos.x = self.pos.x - level
        self.label.pos.x =  self.label.pos.x - level

    def normal(self):
        if (self.conn["ct_event"] == 1):
            self.color = self.icolor = COLOR_TCP
        elif (self.conn["ct_event"] == 4):
            self.color = self.icolor = COLOR_UDP

    def highlight(self):
        self.color = HIGHLIGHT_COLOR
        self.label.visible = 1

class connections():
    """
    Connections list with visual elements
    """

    def __init__(self, start, end, duration, **kargs):
        self.starttime = self.mintime = start
        self.endtime = self.maxtime = end
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
        self.conns = []
        self.container = None
        self.objlist = []
        self.filter = {}
        self.highlight_filter = {}
        self.pgconn = None
        self.adaptative = False
        self.selected = None
        self.level = 0

    def set_level(self, level):
        self.level = level
        for conn in self.conns:
            conn.set_level(self.level)
        self.container.pos.x = self.container.pos.x - self.level

    def build_str_filter(self, sep, prefix=''):
        query_filter = ''
        i = 0
        for k in self.filter:
            if (i>0):
                query_filter +=  sep 
            else:
                if (prefix != ''):
                    query_filter = prefix
                else:
                    query_filter +=  sep 
            if type(self.filter[k]) == (type(1)):
                query_filter += k + "=%d" % (self.filter[k])
            elif type(self.filter[k]) == (type('str')):
                query_filter += k + "='%s'" % (self.filter[k])
            i += 1
        return query_filter
        
    def from_pgsql(self, pgcnx, **kargs):
        if pgcnx != None:
            self.pgconn = pgcnx
        # compute filter
        query_filter = self.build_str_filter(" AND ")
        # Build query
        if (self.mode == "period"):
            strquery = "SELECT flow_start_sec+flow_start_usec/1000000 AS start, \
            flow_end_sec+flow_end_usec/1000000 AS end, orig_ip_daddr_str, \
            orig_ip_saddr_str, orig_l4_sport, \
            orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen, orig_ip_protocol,\
            ct_event FROM ulog2_ct WHERE ((flow_end_sec > %f AND flow_start_sec < %f) \
            OR \
            (flow_end_sec IS NULL AND flow_start_sec < %f)) %s\
            ORDER BY flow_start_sec DESC" % ( self.starttime, self.endtime, self.endtime, query_filter) 
        elif (self.mode == "duration"):
            ctime = time.time()
            strquery = "SELECT flow_start_sec+flow_start_usec/1000000 AS start, \
            flow_end_sec+flow_end_usec/1000000 AS end, orig_ip_daddr_str,\
            orig_ip_saddr_str, orig_l4_sport, \
            orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen, orig_ip_protocol,\
            ct_event FROM ulog2_ct WHERE (flow_end_sec > %f OR flow_end_sec IS NULL) %s\
            ORDER BY flow_start_sec DESC" % (ctime - self.duration, query_filter) 
            self.starttime = ctime - self.duration
            self.endtime = ctime

        conns = self.pgconn.query(strquery).dictresult()
        t = 0
        self.count = len(conns)
        print "Found %d connections" % (self.count)
        conns.sort(lambda x, y: cmp(x["start"], y["start"]))
        if self.adaptative:
            self.mintime = max(self.starttime, conns[0]["start"])
        else:
            self.mintime = self.starttime
            self.maxtime = self.endtime
        maxtime = 0
        for elt in conns:
            if (elt["end"]):
                if elt["start"]:
                    conn = connection(max(0, elt["start"]-self.mintime), min(elt["end"]-self.mintime, self.duration), elt)
                    if self.adaptative:
                        maxtime = max(maxtime, elt["end"])
                else:
                    print "No timestamp in connection, can't display !"
                    continue
            else:
                if elt["start"]:
                    conn = connection(max(0,elt["start"]-self.mintime), self.endtime-self.mintime,elt)
                else:
                    print "No timestamp in connection, can't display !"
                    continue
                maxtime = self.endtime
            self.maxtime = min(self.endtime, maxtime)
            conn.set_level(self.level)
            conn.ordonate(t)
            self.conns.append(conn)
            t += 1

    def length(self):
        if (self.adaptative):
            return self.maxtime - self.mintime
        else:
            return self.endtime - self.starttime

    def clear(self):
        for obj in self.conns:
            obj.label.visible = 0
            obj.visible = 0
        self.conns = []
        for obj in self.container.objects:
            obj.visible = 0
        self.container = None

    def plate(self):
        self.container = visual.frame()
        field_length =  self.length() + 2*RADIUS
        field_width = 3*RADIUS*self.count + 10
        visual.box(frame=self.container, pos = (field_length/2 - self.level, -(RADIUS+1),field_width/2), width = field_width, length = field_length, height = 1, color = BOX_COLOR)

        desctext = 'From %s to %s\n' % (time.strftime("%H:%M:%S", time.localtime(self.starttime)), \
            time.strftime("%H:%M:%S", time.localtime(self.endtime)))
        desctext += self.build_str_filter(" and ", "Filtering on ")
        visual.label(frame=self.container, pos = (field_length/2 - self.level, RADIUS+0.5,0), yoffset = 4*RADIUS, text = desctext)
        for i in range(GRADUATION):
            visual.curve(frame=self.container, pos=[(field_length/GRADUATION*i - self.level, -(RADIUS+1)+1,0), (field_length/GRADUATION*i - self.level,-(RADIUS+1)+1,field_width)])
        for i in range(GRADUATION/TICK+1):
            ctime = time.strftime("%H:%M:%S", time.localtime(self.starttime + GRADUATION*TICK*i))
            visual.label(frame=self.container, pos=(field_length/GRADUATION*TICK*i - self.level, -(RADIUS+1)+1,0), text = '%s' % (ctime), border = 5, yoffset = 1.5*RADIUS)

    def refresh(self):
        self.clear()
        self.from_pgsql(None)
        self.plate()

    def highlight(self, filter):
        if len(self.objlist) != 1:
            print "%d selected entryies , unable to filter" % (len(self.objlist))
            return
        highlight = self.objlist[0]
        self.highlight_filter = {}
        self.highlight_filter[filter] = highlight.conn[filter]
        for conn in self.conns:
            if conn != highlight and conn.conn[filter] == highlight.conn[filter]:
                self.objlist.append(conn)
                conn.highlight()

    def select(self, c):
        self.objlist = []
        self.objlist.append(c)
        c.highlight()
        self.selected = c

    def move_select(self, dir):
        if self.selected == None:
            self.select(self.conns[0])
            return
        for t in range(len(self.conns)):
            if (self.selected == self.conns[t]):
                self.normalize()
                if (dir == 'up'):
                    self.select(self.conns[t-1])
                else:
                    self.select(self.conns[t+1])
                    return

    def normalize(self):
        for object in self.objlist:
            object.normal()
            object.label.visible = 0
        self.objlist = []
        self.selected = None

    def toggle_label(self):
        for object in self.objlist:
            object.label.visible = not object.label.visible

    def apply_filter(self):
        self.filter.update(self.highlight_filter)
        self.refresh()

    def reset_filter(self):
        self.filter = {}
        self.mintime = self.starttime
        self.maxtime = self.endtime
        self.refresh()

    def toggle_adaptative(self):
        self.adaptative = not self.adaptative
        self.refresh()

    def move_time(self, s):
        self.mode = 'period'
        if (s == 'right'):
            timeshift = TIME_STEP
        else:
            timeshift = - TIME_STEP
        self.starttime += timeshift
        self.endtime += timeshift
        self.refresh()

def main_loop(connlists):
    visual.rate(50)
# Drag and drop loop
    connlist = connlists[0]
    while 1:
        if visual.scene.mouse.events:
            c = visual.scene.mouse.getevent()
            if c.pick and hasattr(c.pick,"icolor"):   # pick up the object
                for connl in connlists:
                    if c.pick in connl.conns:
                        connlist = connl
                        break
                if not c.shift:
                    connlist.normalize()
                if (hasattr(c.pick, "label")):
                    connlist.select(c.pick) 
                else:
                    connlist.normalize()
        if visual.scene.kb.keys: # is there an event waiting to be processed?
            s = visual.scene.kb.getkey() # obtain keyboard information
            if (len(s) == 1):
                if (s in filters_list):
                    connlist.highlight(filters_list[s])
                elif (s == 'r'):
                    connlist.refresh()
                elif (s == 'c'):
                    for connsl in connlists:
                        connsl.normalize()
                elif (s == 'l'):
                    for connsl in connlists:
                        connsl.toggle_label()
                elif (s == 'F'):
                    connlist.apply_filter()
                elif (s == 'R'):
                    connlist.reset_filter()
                elif (s == 'a'):
                    connlist.toggle_adaptative()
                elif (s == 'C'):
                    for connsl in connlists:
                        connsl.set_level(connlist.length()+15*RADIUS)
                    newconns = connections(connlist.starttime, connlist.endtime, connlist.duration)
                    newconns.from_pgsql(connlist.pgconn)
                    newconns.plate()
                    connlists.append(newconns)
                elif (s == 'D'):
                    if (len(connlists) > 1):
                        connlist.clear()
                        for connsl in connlists:
                            if (connsl == connlist):
                                break
                            connsl.set_level(-(connlist.length()+100*RADIUS))
                        connlists.remove(connlist)
                        connlist = connlists[0]
                    else:
                        print "Will not destroy to avoid null display"
            elif (s in ('up', 'down')):
                connlist.move_select(s)
            elif (s in ('left', 'right')):
                connlist.move_time(s)
            else:
                print "Key pressed: %s" % (s)

def usage():
    print "fwtron.py [-h] [-s START] [-e END] [-d DURATION]\n"

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
    pgcnx = pg.connect(DATABASE, HOST, PORT, None, None, LOGIN, PASSWORD)
    connlist = connections(start, end, duration)
    connlist.from_pgsql(pgcnx)
    connlist.plate()
    connlists = []
    connlists.append(connlist)
    main_loop(connlists)

if __name__ == "__main__":
    main()

