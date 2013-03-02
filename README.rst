====
nf3d
====

Introduction
============

nf3d is a Netfilter visualisation tool. It displays connections and logged 
packets in a GANTT diagram fashion.

Prerequisites
=============

nf3d is currently using ulogd2 pgsql output to read information. You will
thus need a working ulogd2 setup to be able to use this tool.

Ulogd2 needs to store the connection tracking entries into a Postgresql database.
This can  be done by activating the following stack in ulogd.conf ::

	stack=ct1:NFCT,ip2str1:IP2STR,pgsql2:PGSQL

The INSERT_OR_REPLACE_CT procedure is the most interesting here as you will have information
about the status of a connection (opened or close).

For recent kernel, if you want to have bytes information, you need to activate connection
accounting. It can be done via ::

	echo "1"> /proc/sys/net/netfilter/nf_conntrack_acct

Installation
============

nf3d is using visual python and pygresql as well as other standard modules. You will need them
to run this software.
On debian, you can install them by typing ::

	aptitude install python-visual python-pygresql python-configobj python-setuptools

Then go to nf3d directory and type ::

	python ./setup.py install
	cp nf3d.conf /etc/nf3d.conf

Running it
==========

nf3d -h will return an usage message.

To display connections and logged packets over one hour period ::

	nf3d -D 3600

Keyboard usage
--------------
Global
~~~~~~
 
 * 'c': switch highlighted items to normal
 * 'l': toggle label fisplay on selected items
 * 'r': refresh current connection table
 * down arrow: highlight next item
 * up arrow: highlight prev item
 * 'w': dump information about highlighted object to stdout
 * '?': display help message

Selection
~~~~~~~~~

Click on a selection to highlight it and you can now use selection feature. Pressing the
following key will highlight all connections matching filter:

 * 'd': original destination IP
 * 's': original source IP
 * 'p': original destination port
 * 'P': original source port

original is referring to the existence of original and reply IP tuple in Netfilter conntrack.

Connections lists handling
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can change the displayed time window with the following keys:

 * right arrow: move time window right
 * left arrow: move time window left

You can modify the displayed connections by using filter:

 * 'F': only display highlighted connections
 * 'R': reset filter and display all connections in the time window
 * 'O': order connections by last filter
 * ':': interactive filter, give a filter with syntax 'key=value'

You can also duplicate connections to be able to compare different time window or filter:

 * 'C': duplicate the selected table
 * 'D': delete the selected table
