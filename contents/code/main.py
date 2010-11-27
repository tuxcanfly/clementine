# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript

import os
import dbus
import urllib
import urllib2
import simplejson
import gobject
import dbus.mainloop.glib

CLEMENTINE_PATH = "/TrackList"
CLEMENTINE_IFACE = "org.mpris.clementine"
MEDIAPLAYER_IFACE = "org.freedesktop.MediaPlayer"
LAST_FM_KEY = "83dcb2276022c922b0140f4fde7425ec"
IMG_CACHE_DIR = "~/.config/Clementine/albumcovers/"

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


class Clementine(plasmascript.Applet):

    def __init__(self, parent, args=None):
         plasmascript.Applet.__init__(self, parent)

    def _handle_track_change(self, data):
        self.refresh()

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

        # cover image
        self.cover = Plasma.Label(self.applet)
        self.cover.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.cover)

        self.clementine_iface = self.get_dbus_object()
        self.clementine_iface.connect_to_signal("TrackChange", self._handle_track_change, MEDIAPLAYER_IFACE)
        self.refresh()

    def refresh(self):
        self.current_track = self.clementine_iface.GetCurrentTrack()
        self.metadata = dict(self.clementine_iface.GetMetadata(self.current_track))
        self.track = Track(**self.metadata)

        self.label_album.setText(self.track.album)
        self.label_artist.setText(self.track.artist)
        self.label_location.setText(self.track.location)
        self.label_time.setText(str(self.track.time))
        self.label_title.setText(self.track.title)

        self.cover.setImage(self.get_artwork())

    def get_dbus_object(self):
        self.bus = dbus.SessionBus()
        return  self.bus.get_object(CLEMENTINE_IFACE, CLEMENTINE_PATH)

    def get_artwork(self):
        """
            Hashes album data to check if clementine has the coverart.
            If no, downloads it and saves to clementine's directory.
        """
        try:
            hash = QtCore.QCryptographicHash(QtCore.QCryptographicHash.Sha1) 
            hash.addData(self.track.artist.lower())
            hash.addData(self.track.album.lower())
            filename = IMG_CACHE_DIR + str(hash.result()).encode('hex')
            if os.path.isfile(filename):
                return filename
            url = "http://ws.audioscrobbler.com/2.0/"
            params = { 
                    'format': 'json',
                    'method': 'album.getinfo',
                    'api_key': LAST_FM_KEY,
                    'album' : self.track.album,
                    'artist': self.track.artist,
            }
            full_url = url + "?" + urllib.urlencode(params)
            resp = urllib2.urlopen(full_url)
            data = resp.read()
            parsed = simplejson.loads(data)
            large_url = parsed['album']['image'][2]['#text']
            downloaded, headers = urllib.urlretrieve(large_url, filename)
        except:
            filename = '/usr/share/kde4/apps/amarok/images/nocover.png'
        finally:
            return filename

class Track(object):

    def __init__(self, album="", artist="", location="", 
            time=0, title="", tracknumber=-1):
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
