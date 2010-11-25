# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript

import dbus

CLEMENTINE_PATH = "/TrackList"
CLEMNTINE_IFACE = "org.mpris.clementine"

class Clementine(plasmascript.Applet):
    def __init__(self, parent, args=None):
         plasmascript.Applet.__init__(self, parent)

    def init(self):
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.resize(200, 150)
        self.setHasConfigurationInterface(False)
        self.layout = QGraphicsLinearLayout(Qt.Horizontal, self.applet)
        self.setLayout(self.layout)
        self.label = Plasma.Label(self.applet)
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label)
        self.clementine_iface = self.get_dbus_object()
        self.current_track = self.clementine_iface.GetCurrentTrack()
        self.metadata = dict(self.clementine_iface.GetMetadata(self.current_track))
        self.track = Track(**self.metadata)
        print self.track
        #print self.clementine_iface.GetMetadata(self.current_track)

    def get_dbus_object(self):
        self.bus = dbus.SessionBus()
        return  self.bus.get_object(CLEMNTINE_IFACE, CLEMENTINE_PATH)

class Track(object):

    def __init__(self, album=None, artist=None, location=None, 
            time=0, title=None, tracknumber=-1):
        self.album = album
        self.artist = artist
        self.location = location
        self.time = time
        self.title = title
        self.tracknumber = tracknumber

    def __str__(self):
        return self.title or "Unknown"

def CreateApplet(parent):
    return Clementine(parent)
