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
import pg
import sys
import os
import time

filters_list = { 'p': 'orig_l4_dport', 'd': 'orig_ip_daddr_str', 's': 'orig_ip_saddr_str', 'P': 'orig_l4_sport', 'I': 'orig_ip_protocol', 'm': 'ct_mark'}

class connobj(object):
    """
    generic connections list related object
    """

    def __init__(self, **kargs):
        self.config = kargs['config']
        self.color = self.icolor = self.config['colors']['base']

    def ordonate(self, index):
        self.z = (3*self.config['display']['radius'])*index
        self.label.z = (3*self.config['display']['radius'])*index

    def highlight(self):
        self.color = self.icolor = self.config['colors']['highlight']
        self.label.visible = 1

    def normal(self):
        self.color = self.config['colors']['base']
        self.label.visible = 0

    def set_level(self, level):
        self.pos.x = self.pos.x - level
        self.label.pos.x =  self.label.pos.x - level

    def dumpinfo(self):
        print "Object information:"
        for k in self.obj.keys():
            if type(self.obj[k]) == (type(1)):
                print "\t* " + k + "=%d" % (self.obj[k])
            elif type(self.obj[k]) == (type('str')):
                print "\t* " + k + "='%s'" % (self.obj[k])



class packet(visual.sphere, connobj):
    """
    Store information about a logged packet
    """

    def __init__(self, start, pckt, **kargs):
        visual.sphere.__init__(self, **kargs)
        connobj.__init__(self, **kargs)
        self.radius = 1.5 * self.config['display']['radius']
        self.pos.x = start
        self.obj = pckt
        self.set_label()

    def set_label(self):
        txtlabel = ''
        if (self.obj["ip_protocol"] == 6):
            txtlabel = 'SRC: %s:%d\nDST: %s:%d\n' % (self.obj["ip_saddr_str"], self.obj["tcp_sport"], self.obj["ip_daddr_str"], self.obj["tcp_dport"])
            txtlabel += 'PROTO: TCP\n'
        elif (self.obj["ip_protocol"] == 17):
            txtlabel = 'SRC: %s:%d\nDST: %s:%d\n' % (self.obj["ip_saddr_str"], self.obj["udp_sport"], self.obj["ip_daddr_str"], self.obj["udp_dport"])
            txtlabel += 'PROTO: UDP\n'
        elif (self.obj["ip_protocol"] == 1):
            txtlabel += 'PROTO: ICMP\n'
        if (self.obj['oob_in']):
            txtlabel += 'IN: %s ' % (self.obj['oob_in'])
        if (self.obj['oob_out']):
            txtlabel += 'OUT: %s\n' % (self.obj['oob_out'])
        else:
            txtlabel += '\n'
        if (self.obj['oob_prefix']):
            txtlabel += 'PREFIX: %s' % (self.obj['oob_prefix'])

        self.label = visual.label(pos=self.pos, xoffset = -10, yoffset = 10,  text='%s' % (txtlabel))
        self.label.visible = 0

    def normal(self):
        connobj.normal(self)
        self.radius = 1.5 * self.config['display']['radius']

    def highlight(self):
        connobj.highlight(self)
        self.radius += 0.2 


class connection(visual.cylinder, connobj):
    """
    Store information about a connection and related object.
    """

    def __init__(self, start, end, conn, **kargs):
        visual.cylinder.__init__(self, **kargs)
        connobj.__init__(self, **kargs)
        self.pos = (start,0, 0)
        self.radius = self.config['display']['radius']
        self.axis = (end - start,0,0)
        self.obj = conn
        self.set_label()
        self.normal()

    def set_label(self):
        txtlabel = ''
        if (self.config['display']['extended_label'] != 0):
            if (self.obj["orig_ip_protocol"] in (6,17)):
                txtlabel = 'ORIG SRC: %s:%d\n     DST: %s:%d\nREPL SRC: %s:%d\n     DST: %s:%d\n' % (self.obj["orig_ip_saddr_str"], self.obj["orig_l4_sport"],  self.obj["orig_ip_daddr_str"], self.obj["orig_l4_dport"] ,\
             self.obj["reply_ip_saddr_str"], self.obj["reply_l4_sport"],  self.obj["reply_ip_daddr_str"], self.obj["reply_l4_dport"])
            elif (self.obj["orig_ip_protocol"] == 1):
                txtlabel = 'ORIG SRC: %s\n     DST: %s\nREPL SRC: %s\n     DST: %s\nCODE: %d TYPE: %d\n' % (self.obj["orig_ip_saddr_str"], \
                    self.obj["orig_ip_daddr_str"],  self.obj["reply_ip_saddr_str"],  \
                    self.obj["reply_ip_daddr_str"], self.obj["icmp_code"], self.obj["icmp_type"])
            else:
                txtlabel = 'ORIG SRC: %s\n     DST: %s\nREPL SRC: %s\n     DST: %s\n' % (self.obj["orig_ip_saddr_str"],self.obj["reply_ip_saddr_str"],  self.obj["orig_ip_daddr_str"],  self.obj["reply_ip_daddr_str"])
        else:
            if (self.obj["orig_ip_protocol"] in (6,17)):
                txtlabel = 'SRC: %s:%d\nDST: %s:%d\n' % (self.obj["orig_ip_saddr_str"], self.obj["orig_l4_sport"], self.obj["orig_ip_daddr_str"], self.obj["orig_l4_dport"])
            else:
                txtlabel = 'SRC: %s\nDST: %s\n' % (self.obj["orig_ip_saddr_str"], self.obj["orig_ip_daddr_str"])
        if (self.obj["orig_ip_protocol"] == 6):
            txtlabel += 'PROTO: TCP'
        elif (self.obj["orig_ip_protocol"] == 17):
            txtlabel += 'PROTO: UDP'
        elif (self.obj["orig_ip_protocol"] == 1):
            txtlabel += 'PROTO: ICMP'
        if (self.obj["ct_event"] == 1):
            self.label = visual.label(pos=self.pos, xoffset = -10, yoffset = 10,  text='%s' % (txtlabel))
        elif (self.obj["ct_event"] == 4):
            self.label = visual.label(pos=self.pos, xoffset = -10, yoffset = 10,  text='%s\nIN: %d, OUT: %d bits\nDURATION: %f sec' % (txtlabel, self.obj["reply_raw_pktlen"],self.obj["orig_raw_pktlen"]  , self.axis.x))
        self.label.visible = 0

    def set_axis(self, timestamp):
        self.axis = (timestamp, 0, 0)

    def normal(self):
        connobj.normal(self)
        if (self.obj["ct_event"] == 1):
            self.color = self.icolor = self.config['colors']['opened']
        elif (self.obj["ct_event"] == 4):
            self.color = self.icolor = self.config['colors']['closed']

def conn_comp(x,y,criter):
    ret = cmp(x.obj[criter], y.obj[criter])
    if (ret == 0):
        return cmp(x.obj["start"], y.obj["start"])
    else:
        return ret

class connections(object):
    """
    Connections list with visual elements
    """

    def __init__(self, start, end, duration, config, **kargs):
        self.config = config
        self.starttime = start
        self.endtime = end
        if (duration == 0):
            self.duration = config['setup']['duration']
        else:
            self.duration = duration
        if (self.endtime and self.endtime < self.starttime):
            print "End before beginning, exiting"
            sys.exit(1)
        if (self.starttime and self.endtime):
            self.duration = self.endtime - self.starttime
        if (not self.starttime and self.endtime):
            self.starttime = self.endtime - self.duration
        if (not self.starttime and not self.endtime):
            self.mode = "duration"
        else:
            self.mode = "period"
        if (not self.endtime and self.starttime and self.duration):
            self.endtime = self.starttime + self.duration

        self.mintime = self.starttime
        self.maxtime = self.endtime

        self.conns = []
        self.packets = []
        self.container = None
        self.objlist = []
        self.filter = {}
        self.highlight_filter = {}
        self.pgconn = None
        self.adaptative = False
        self.selected = None
        self.level = 0
        self.count = 0
        self.ordered = False
        self.orderby = None

        self.ctiddict = {}

    def set_level(self, level):
        self.level = level
        for obj in self.conns + self.packets:
            obj.set_level(self.level)
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
        
    def from_pgsql(self, **kargs):
        if kargs.has_key('conn'):
            self.pgconn = kargs['conn']
        fields_list = 'orig_ip_daddr_str, \
            orig_ip_saddr_str, orig_l4_sport, \
            orig_l4_dport ,orig_raw_pktlen, reply_raw_pktlen, orig_ip_protocol,\
            ct_event, icmp_code, icmp_type, ct_mark'
        if (self.config['display']['extended_label'] != 0):
            fields_list += ', reply_ip_daddr_str, \
            reply_ip_saddr_str, reply_l4_sport, \
            reply_l4_dport'
        # compute filter
        query_filter = self.build_str_filter(" AND ")
        # Build query
        if (self.mode == "period"):
            strquery = "SELECT _ct_id, flow_start_sec+flow_start_usec*1.0/1000000 AS start, \
            flow_end_sec+flow_end_usec*1.0/1000000 AS end,  %s FROM ulog2_ct WHERE ((flow_end_sec > %f AND flow_start_sec < %f) \
            OR \
            (flow_end_sec IS NULL AND flow_start_sec < %f)) %s\
            ORDER BY flow_start_sec DESC" % (fields_list, self.starttime, self.endtime, self.endtime, query_filter) 
        elif (self.mode == "duration"):
            ctime = time.time()
            strquery = "SELECT _ct_id, flow_start_sec+flow_start_usec*1.0/1000000 AS start, \
            flow_end_sec+flow_end_usec*1.0/1000000 AS end, %s \
            FROM ulog2_ct WHERE (flow_end_sec > %f OR flow_end_sec IS NULL) %s\
            ORDER BY flow_start_sec DESC" % (fields_list, ctime - self.duration, query_filter) 
            self.starttime = ctime - self.duration
            self.endtime = ctime

        if int(self.config['debug']['query']) == 1:
            print strquery
        try:
            conns = self.pgconn.query(strquery).dictresult()
        except(pg.ProgrammingError):
            print "Bad request, maybe filter is wrong"
            return
        t = 0
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
                    conn = connection(max(0, float(elt["start"])-self.mintime), min(float(elt["end"])-self.mintime, self.duration),elt, config = self.config)
                    self.ctiddict[elt["_ct_id"]] = t
                    if self.adaptative:
                        maxtime = max(maxtime, elt["end"])
                else:
                    print "No start timestamp in connection, can't display !"
                    continue
            else:
                if elt["start"]:
                    conn = connection(max(0,float(elt["start"])-self.mintime), self.endtime-self.mintime,elt, config = self.config)
                    self.ctiddict[elt["_ct_id"]] = int(t)
                else:
                    print "No timestamp in connection, can't display !"
                    continue
                maxtime = self.endtime
            self.maxtime = min(self.endtime, maxtime)
            conn.set_level(self.level)
            conn.ordonate(t)
            self.conns.append(conn)
            t += 1
        self.count = len(self.conns)
        print "Found %d connections" % (self.count)
        
        if int(self.config['display']['packets']) == 1:
            strquery = "SELECT oob_time_sec+oob_time_usec/1000000 AS time, * FROM ulog2 JOIN tcp on _id=_tcp_id JOIN ulog2_ct ON ip_saddr_str=orig_ip_saddr_str AND ip_daddr_str=orig_ip_daddr_str AND ip_protocol=orig_ip_protocol AND tcp_sport=orig_l4_sport AND tcp_dport=orig_l4_dport where oob_time_sec >= %f AND oob_time_sec < %f %s" % (self.starttime, self.endtime, query_filter)

            if int(self.config['debug']['query']) == 1:
                print strquery
            packetlist = self.pgconn.query(strquery).dictresult()
            strquery = "SELECT oob_time_sec+oob_time_usec/1000000 AS time, * FROM ulog2 JOIN udp on _id=_udp_id JOIN ulog2_ct ON ip_saddr_str=orig_ip_saddr_str AND ip_daddr_str=orig_ip_daddr_str AND ip_protocol=orig_ip_protocol AND udp_sport=orig_l4_sport AND udp_dport=orig_l4_dport where oob_time_sec >= %f AND oob_time_sec < %f %s" % (self.starttime, self.endtime, query_filter)
            packetlist += self.pgconn.query(strquery).dictresult()
            for pckt in packetlist:
                if pckt["time"]:
                    if (self.ctiddict.has_key(pckt["_ct_id"])):
                        np = packet(float(pckt["time"]) - self.mintime, pckt, config = self.config)
                        np.ordonate(self.ctiddict[pckt["_ct_id"]])
                        np.set_level(self.level)
                        self.packets.append(np)


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
        for obj in self.packets:
            obj.label.visible = 0
            obj.visible = 0
        self.packets = []
        for obj in self.container.objects:
            obj.visible = 0
        self.container = None

    def plate(self):
        if (self.container):
            for obj in self.container.objects:
                obj.visible = 0
        self.container = visual.frame()
        field_length =  self.length() + 2*self.config['display']['radius']
        field_width = 3*self.config['display']['radius']*self.count + 10
        if (self.ordered):
            init = self.conns[0].obj[self.orderby]
            pborder = 0
            t = -1
            i = 0
            for conn in self.conns:
                if (init != conn.obj[self.orderby]):
                    if ((i % 2) == 1):
                        bcolor = self.config['colors']['box_light']
                    else:
                        bcolor = self.config['colors']['box']

                    if type(init) == (type(1)):
                        labeltext = self.orderby + "\n%d" % (init)
                    elif type(init) == (type('str')):
                        labeltext = self.orderby + "\n'%s'" % (init)
                    visual.box(frame=self.container, pos=(field_length/2 - self.level, -(self.config['display']['radius']+1), 3*self.config['display']['radius']*t/2+self.config['display']['radius'] + pborder/2), \
                             width = (3*self.config['display']['radius']*t - pborder), length = field_length, height = 1, color = bcolor)
                    visual.label(frame=self.container, pos = (self.config['display']['radius'] -self.level, 0,  3*self.config['display']['radius']*t/2+self.config['display']['radius'] + pborder/2),\
                        yoffset = 4*self.config['display']['radius'], xoffset = -4* self.config['display']['radius'],text = labeltext)
                    pborder = 3*self.config['display']['radius']*t+self.config['display']['radius']
                    init = conn.obj[self.orderby]
                    i += 1
                t += 1

            if type(init) == (type(1)):
                labeltext = self.orderby + "\n%d" % (init)
            elif type(init) == (type('str')):
                labeltext = self.orderby + "\n'%s'" % (init)
            if ((i % 2) == 1):
                bcolor = self.config['colors']['box_light']
            else:
                bcolor = self.config['colors']['box']
            visual.box(frame=self.container, pos=(field_length/2 - self.level, -(self.config['display']['radius']+1), 3*self.config['display']['radius']*t/2+self.config['display']['radius'] + pborder/2), \
                     width = (3*self.config['display']['radius']*t - pborder), length = field_length, height = 1, color = bcolor)
            visual.label(frame=self.container, pos = (self.config['display']['radius'] - self.level, 0, 3*self.config['display']['radius']*t/2+self.config['display']['radius'] + pborder/2),\
                yoffset = 4*self.config['display']['radius'], xoffset = -4* self.config['display']['radius'], text = labeltext)
        else:
             visual.box(frame=self.container, pos = (field_length/2 - self.level, -(self.config['display']['radius']+1),field_width/2), width = field_width, length = field_length, height = 1, color = self.config['colors']['box'])

        desctext = 'From %s to %s\n' % (time.strftime("%F %H:%M:%S", time.localtime(self.starttime)), \
            time.strftime("%F %H:%M:%S", time.localtime(self.endtime)))
        desctext += self.build_str_filter(" and ", "Filtering on ")
        visual.label(frame=self.container, pos = (field_length/2 - self.level, self.config['display']['radius']+0.5,0), yoffset = 4*self.config['display']['radius'], text = desctext)
        for i in range(self.config['display']['graduation']):
            visual.curve(frame=self.container, pos=[(field_length/self.config['display']['graduation']*i - self.level, -(self.config['display']['radius']+1)+1,0), (field_length/self.config['display']['graduation']*i - self.level,-(self.config['display']['radius']+1)+1,field_width)])
        for i in range(self.config['display']['graduation']/self.config['display']['tick']+1):
            ctime = time.strftime("%H:%M:%S", time.localtime(self.mintime + field_length/self.config['display']['graduation']*self.config['display']['tick']*i))
            visual.label(frame=self.container, pos=(field_length/self.config['display']['graduation']*self.config['display']['tick']*i - self.level, -(self.config['display']['radius']+1)+1,0), text = '%s' % (ctime), border = 5, yoffset = 1.5*self.config['display']['radius'])

    def build(self, **kargs):
        if (self.config['global']['input'] == 'database') and (self.config['database']['type'] == 'pgsql'):
            self.from_pgsql(**kargs)

    def refresh(self):
        self.clear()
        self.build()
        self.order()
        self.plate()

    def highlight(self, filter):
        if len(self.objlist) != 1:
            print "%d selected entries , unable to filter" % (len(self.objlist))
            return
        highlight = self.objlist[0]
        self.highlight_filter = {}
        self.highlight_filter[filter] = highlight.obj[filter]
        if highlight in self.conns:
            for conn in self.conns:
                if conn != highlight and conn.obj[filter] == highlight.obj[filter]:
                    self.objlist.append(conn)
                    conn.highlight()
        elif highlight in self.packets:
            for packets in self.packets:
                if packets != highlight and packets.obj[filter] == highlight.obj[filter]:
                    self.objlist.append(packets)
                    packets.highlight()

    def order(self):
        if (self.ordered):
            self.conns.sort(lambda x, y: conn_comp(x,y,self.orderby))
        else:
            self.conns.sort(lambda x,y: cmp(x.obj['start'], y.obj['start']))
        t = 0
        for conn in self.conns:
            conn.ordonate(t)
            self.ctiddict[conn.obj["_ct_id"]] = t
            t += 1
        for np in self.packets:
            np.ordonate(self.ctiddict[np.obj["_ct_id"]])
        self.plate()
        

    def switch_order(self):
        self.normalize()
        if (self.highlight_filter):
            if (self.orderby != self.highlight_filter.keys()[0]):
                self.ordered = True
                self.orderby = self.highlight_filter.keys()[0]
            else:
                self.ordered = not self.ordered
        else:
            return
        self.order()

    def select(self, c):
        self.objlist.append(c)
        c.highlight()
        self.selected = c

    def move_select(self, dir):
        if self.selected == None:
            self.select(self.conns[0])
            return
        if self.selected in self.conns:
            objlist = self.conns
        elif self.selected in self.packets:
            objlist = self.packets
        else:
            print "Unknown object type"
            return
        for t in range(len(objlist)):
            if (self.selected == objlist[t]):
                self.normalize()
                if (dir == 'up'):
                    self.select(objlist[(t-1) % len(objlist)])
                else:
                    self.select(objlist[(t+1) % len(objlist)])
                    return

    def normalize(self):
        for object in self.objlist:
            object.normal()
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
            timeshift = int(self.config['setup']['time_step'])
        else:
            timeshift = - int(self.config['setup']['time_step'])
        self.starttime += timeshift
        self.endtime += timeshift
        self.refresh()

    def highlight_write(self):
        for obj in self.objlist:
            obj.dumpinfo()


