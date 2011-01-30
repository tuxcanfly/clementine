# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.kdeui import *
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
PLAYER_PATH = "/Player"
CLEMENTINE_IFACE = "org.mpris.clementine"
MEDIAPLAYER_IFACE = "org.freedesktop.MediaPlayer"
LAST_FM_KEY = "83dcb2276022c922b0140f4fde7425ec"
IMG_CACHE_DIR = os.path.expanduser("~/.config/Clementine/albumcovers/")

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


class Clementine(plasmascript.Applet):

    def __init__(self, parent, args=None):
         plasmascript.Applet.__init__(self, parent)

    def _handle_track_change(self, data):
        self.refresh()

    def _get_is_paused(self):
        return self.player_iface.GetStatus()[0]

    def _play_clicked(self):
        if self._get_is_paused():
            self.play.setText("Play")
            self.play.setIcon(KIcon("media-playback-start"))
            self.player_iface.Play()
        else:
            self.play.setText("Pause")
            self.play.setIcon(KIcon("media-playback-pause"))
            self.player_iface.Pause()

    def _next_clicked(self):
        self.player_iface.Next()

    def _prev_clicked(self):
        self.player_iface.Prev()

    def _stop_clicked(self):
        self.player_iface.Stop()

    def _retry_clicked(self):
        self.message.deleteLater()
        self.retry.deleteLater()
        self.init()

    def init(self):

        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.resize(200, 200)
        self.setHasConfigurationInterface(False)
        self.layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.setLayout(self.layout)

        self.clementine_iface = self.get_tracklist_object()
        self.player_iface = self.get_player_object()

        if self.clementine_iface is None:

            # not running message
            self.message = Plasma.Label(self.applet)
            self.message.setAlignment(Qt.AlignCenter)
            self.message.setText("Clementine is not running")
            self.layout.addItem(self.message)

            # retry button
            self.retry = Plasma.PushButton(self.applet)
            self.retry.setText("Refresh")
            self.retry.setIcon(KIcon('view-refresh'))
            QObject.connect(self.retry, SIGNAL("clicked()"), self._retry_clicked)
            self.layout.addItem(self.retry)

            # no clementine running; no plasma app for you
            return

        self.clementine_iface.connect_to_signal("TrackChange", 
                                                self._handle_track_change, 
                                                MEDIAPLAYER_IFACE)

        # title label
        self.label_title = Plasma.Label(self.applet)
        self.label_title.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_title)

        # album label
        self.label_album = Plasma.Label(self.applet)
        self.label_album.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_album)
        
        # artist label
        self.label_artist = Plasma.Label(self.applet)
        self.label_artist.setAlignment(Qt.AlignCenter)
        self.layout.addItem(self.label_artist)

        # cover image
        self.cover = Plasma.Frame(self.applet)
        self.cover.setMinimumSize(174, 174)
        self.layout.addItem(self.cover)

        # play/pause button
        self.play = Plasma.PushButton(self.applet)
        if self._get_is_paused():
            self.play.setText("Play")
            self.play.setIcon(KIcon("media-playback-start"))
        else:
            self.play.setText("Pause")
            self.play.setIcon(KIcon("media-playback-pause"))
        QObject.connect(self.play, SIGNAL("clicked()"), self._play_clicked)
        self.layout.addItem(self.play)

        # next/pause buttons
        self.next = Plasma.PushButton(self.applet)
        self.prev = Plasma.PushButton(self.applet)
        self.next.setText("Next")
        self.prev.setText("Previous")
        self.next.setIcon(KIcon("media-skip-forward"))
        self.prev.setIcon(KIcon("media-skip-backward"))
        QObject.connect(self.next, SIGNAL("clicked()"), self._next_clicked)
        QObject.connect(self.prev, SIGNAL("clicked()"), self._prev_clicked)
        self.layout.addItem(self.next)
        self.layout.addItem(self.prev)

        # stop button
        self.stop = Plasma.PushButton(self.applet)
        self.stop.setText("Stop")
        self.stop.setIcon(KIcon("media-playback-stop"))
        QObject.connect(self.stop, SIGNAL("clicked()"), self._stop_clicked)
        self.layout.addItem(self.stop)

        self.refresh()

    def refresh(self):
        self.current_track = self.clementine_iface.GetCurrentTrack()
        self.metadata = dict(self.clementine_iface.GetMetadata(self.current_track))
        self.track = Track(
                            self.metadata.get('album'),
                            self.metadata.get('artist'),
                            self.metadata.get('location'),
                            self.metadata.get('time'),
                            self.metadata.get('title'),
                            self.metadata.get('tracknumber', 0),
                          )
        self.label_album.setText(self.track.album)
        self.label_artist.setText(self.track.artist)
        self.label_title.setText("<b style='font-size:18px;'>"+self.track.title+"</b>")

        self.cover.setImage(self.get_artwork())

    def get_tracklist_object(self):
        self.bus = dbus.SessionBus()
        try:
            return  self.bus.get_object(CLEMENTINE_IFACE, CLEMENTINE_PATH)
        except dbus.exceptions.DBusException:
            return None

    def get_player_object(self):
        self.bus = dbus.SessionBus()
        try:
            return  self.bus.get_object(CLEMENTINE_IFACE, PLAYER_PATH)
        except dbus.exceptions.DBusException:
            return None

    def get_artwork(self):
        """
            Hashes album data to check if clementine has the coverart.
            If no, downloads it and saves to clementine's directory.
        """
        try:
            hash = QCryptographicHash(QCryptographicHash.Sha1) 
            hash.addData(self.track.artist.lower())
            hash.addData(self.track.album.lower())
            filename = IMG_CACHE_DIR + str(hash.result()).encode('hex') + '.jpg'
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
