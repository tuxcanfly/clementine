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
        self.layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.setLayout(self.layout)

        # album label
        self.label_album = Plasma.Label(self.applet)
        self.label_album.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_album)
        
        # artist label
        self.label_artist = Plasma.Label(self.applet)
        self.label_artist.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_artist)

        # location label
        self.label_location = Plasma.Label(self.applet)
        self.label_location.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_location)

        # time label
        self.label_time = Plasma.Label(self.applet)
        self.label_time.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_time)

        # title label
        self.label_title = Plasma.Label(self.applet)
        self.label_title.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_title)

        self.clementine_iface = self.get_dbus_object()
        self.current_track = self.clementine_iface.GetCurrentTrack()
        self.metadata = dict(self.clementine_iface.GetMetadata(self.current_track))
        self.track = Track(**self.metadata)

        self.label_album.setText(self.track.album)
        self.label_artist.setText(self.track.artist)
        self.label_location.setText(self.track.location)
        self.label_time.setText(str(self.track.time))
        self.label_title.setText(self.track.title)

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
