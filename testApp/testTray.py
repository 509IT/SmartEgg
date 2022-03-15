import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import os
import sys

# print('Gtk %d.%d.%d' % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()))
# output: Gtk 3.22.11

#============================== GLOBAL ================================#

IMAGE_PATH = os.path.join(os.path.dirname(sys.argv[0]), 'img/')
IMAGE_GREEN = IMAGE_PATH + 'egg_gree.png'
IMAGE_RED = IMAGE_PATH + 'egg_red.png'

#============================== SYSTEM TRAY ==========================#


class SmartEggTray(object):

    tray_image = IMAGE_RED
    blinking = False
    
    def __init__(self):
        self.tray_icon = Gtk.StatusIcon()
        
        self.menu = self.createMenu()
        
        self.tray_icon.connect('activate', self.refresh)
        self.tray_icon.connect('button-press-event', self.do_nothing)
        self.tray_icon.connect('popup-menu', self.expand_menu, self.menu)

        # display StatusIcon image (without would be displayed only after first SystemIcon activate event)
        self.refresh(self.tray_icon)
        self.tray_icon.set_visible(True)

    def createMenu(self):
        menu = Gtk.Menu()

        item = Gtk.MenuItem('Run')
        #item.show()
        menu.append(item)

        # add rest menu items
        return menu
    
    def refresh(self, status_icon):
        if os.path.exists(self.tray_image):
            self.tray_icon.set_from_file(self.tray_image)
    
    def do_nothing(self, event, widget):
        pass

    def expand_menu(self, tray_icon, event_button, event_time, menu):
        print('menu') # remove

        menu.popup(None, None, None, tray_icon, event_button, event_time)

#============================== MAIN FLOW ============================#

if __name__ == '__main__':
    app = SmartEggTray()
    Gtk.main()

