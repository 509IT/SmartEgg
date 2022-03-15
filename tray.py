#!/usr/bin/env python
# -*- coding: utf-8 -*-
from glob import glob
import gtk
from gtk import gdk
import glib
import gobject
import os
import os.path
from string import rstrip
import sys

from bluepy.btle import *
import time
import math
import io
import threading 

REFRESH_INTERVAL = 1000

IMAGE_LOC = os.path.join(os.path.dirname(sys.argv[0]), "img/")
icon_resume = IMAGE_LOC + "egg_green.png"
icon_pause = IMAGE_LOC + "egg_red.png"

# TODO Get this from file
eggs = [('SmartEgg 3', 'e3:39:56:08:34:fc', '-','-','-','-'), ('SmartEgg 509IT', 'f5:cd:27:15:a8:85', '-','-','-','-')]


loop_continue = True
buffer = None

class SmartEggTray(object):

    pauseResume = gtk.MenuItem("Pause")
    icon_file = icon_resume
    blinking = False

    console_window = None
    list_window = None
    statusbar = None
    #buffer = None
    t = None
    
    def __init__(self):
        self.tray = gtk.StatusIcon()
        self.tray.connect('activate', self.refresh)

        # Create menu
        menu = gtk.Menu()

        self.pauseResume = gtk.MenuItem("Pause")
        self.pauseResume.show()
        self.pauseResume.connect("activate", self.pause_or_resume)
        menu.append(self.pauseResume)

        i = gtk.SeparatorMenuItem()
        i.show()
        menu.append(i)
        
        i = gtk.MenuItem("SmartEgg List...")
        i.show()
        i.connect("activate", self.show_list)
        menu.append(i)

        i = gtk.MenuItem("Log")
        i.show()
        i.connect("activate", self.show_consol)
        menu.append(i)
        
        i = gtk.SeparatorMenuItem()
        i.show()
        menu.append(i)
        
        i = gtk.MenuItem("Quit")
        i.show()
        i.connect("activate", self.quit)
        menu.append(i)
        
        self.tray.connect('popup-menu', self.show_menu, menu)

        # Create console view
        self.create_console_view()

        # Create list view
        self.create_list_view()
        
        # Initalise and start SmartEgg display
        self.refresh()
        self.tray.set_visible(True)
        # Constant check for refresh (Use when needed)
        #gobject.timeout_add(REFRESH_INTERVAL, self.refresh)

        threading.Thread(target=loop).start()



    def show_menu(self, widget, event_button, event_time, menu):
        menu.popup(None, None,
            gtk.status_icon_position_menu,
            event_button,
            event_time,
            self.tray
        )

    def create_list_view(self):
        self.list_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.list_window.set_size_request(750, 250)
        self.list_window.set_position(gtk.WIN_POS_CENTER)
        self.list_window.set_border_width(10)
        self.list_window.set_title("SmartEggs List")

        self.list_window.connect('delete-event', lambda w, e: self.list_window.hide() or True)

        vbox = gtk.VBox(False, 8)
        
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        vbox.pack_start(sw, True, True, 0)

        store = self.create_model()

        treeView = gtk.TreeView(store)
        treeView.connect("row-activated", self.on_activated)
        treeView.set_rules_hint(True)
        sw.add(treeView)

        self.create_columns(treeView)
        self.statusbar = gtk.Statusbar()
        
        vbox.pack_start(self.statusbar, False, False, 0)

        self.list_window.add(vbox)
        self.list_window.show_all()
        self.list_window.hide()

    def create_model(self):
        store = gtk.ListStore(str, str, str, str, str, str)

        for egg in eggs:
            store.append([egg[0], egg[1], egg[2], egg[3], egg[4], egg[5]])

        return store

    def create_columns(self, treeView):
    
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Name", rendererText, text=0)
        column.set_sort_column_id(0)    
        treeView.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Address", rendererText, text=1)
        column.set_sort_column_id(1)
        treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Last Connected", rendererText, text=2)
        column.set_sort_column_id(2)
        treeView.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Status", rendererText, text=3)
        column.set_sort_column_id(3)
        treeView.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Next Connection", rendererText, text=4)
        column.set_sort_column_id(4)
        treeView.append_column(column)

        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Connect In", rendererText, text=5)
        column.set_sort_column_id(5)
        treeView.append_column(column)
        

    def on_activated(self, widget, row, col):
        
        model = widget.get_model()
        text = model[row][0] + ", " + model[row][1] + ", " + model[row][2]
        self.statusbar.push(0, text)

    def create_console_view(self):
        self.console_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.console_window.set_size_request(500, 350)
        self.console_window.set_position(gtk.WIN_POS_CENTER)
        self.console_window.set_border_width(10)
        self.console_window.set_title("SmartEgg Hub")

        # Assemble App Window
        table = gtk.Table(8, 4, False)
        table.set_col_spacings(3)

        title = gtk.Label("Log")

        halign = gtk.Alignment(0, 0, 0, 0)
        halign.add(title)
        
        table.attach(halign, 0, 1, 0, 1, gtk.FILL, 
            gtk.FILL, 0, 0);

        log_scroller = gtk.ScrolledWindow()
        log_scroller.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        terminal = gtk.TextView()
        log_scroller.add(terminal)
        global buffer
        buffer = terminal.get_buffer()
        terminal.set_editable(False)
        terminal.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(5140, 5140, 5140))
        terminal.set_cursor_visible(False)
        table.attach(log_scroller, 0, 2, 1, 3, gtk.FILL | gtk.EXPAND,
            gtk.FILL | gtk.EXPAND, 1, 1)

        self.startButton = gtk.Button("Start")
        self.startButton.set_size_request(50, 30)
        table.attach(self.startButton, 3, 4, 1, 2, gtk.FILL, 
            gtk.SHRINK, 1, 1)
        
        valign = gtk.Alignment(0, 0, 0, 0)
        self.stopButton = gtk.Button("Stop")
        self.stopButton.set_size_request(70, 30)
        valign.add(self.stopButton)
        table.set_row_spacing(1, 3)
        table.attach(valign, 3, 4, 2, 3, gtk.FILL,
            gtk.FILL | gtk.EXPAND, 1, 1)
            
        halign2 = gtk.Alignment(0, 1, 0, 0)
        clearLog = gtk.Button("Clear Log")
        clearLog.set_size_request(70, 30)
        halign2.add(clearLog)
        table.set_row_spacing(3, 6)
        table.attach(halign2, 0, 1, 4, 5, gtk.FILL, 
            gtk.FILL, 0, 0)
        
        ok = gtk.Button("OK")
        ok.set_size_request(70, 30)
        table.attach(ok, 3, 4, 4, 5, gtk.FILL, 
            gtk.FILL, 0, 0);
        self.console_window.add(table)

        # Events handling
        self.console_window.connect('delete-event', lambda w, e: self.console_window.hide() or True)
        clearLog.connect("clicked", self.clear_log)
        
        #self.app_window.connect('delete-event', self.on_destroy)
        self.console_window.show_all()
        self.console_window.hide()

    def clear_log(self, widget):
        print("TODO Clear Log")
        
    def show_consol(self, widget):
       
        
        #self.connect("destroy", gtk.main_quit)
        #self.app_window.show_all()
 
        isVisible = self.console_window.get_property("visible")
        if (isVisible):
            print("isVisible")
            #w.hide()
        else:
            print("notVisible")
            self.console_window.show_all()

        #self.app_window.show()
        #print("Keypress")
        #textbox
        #read the contents of the file
        #text = open("yourfile").read()
        #get the underlying TextBuffer object of the TextView and set its text
        #textbox.get_buffer().set_text(text)


        # Program goes here  ...

        #app_window.show()
        
        # TODO 1
        
    def show_list(self, widget):
       
        
        #self.connect("destroy", gtk.main_quit)
        #self.app_window.show_all()
 
        isVisible = self.list_window.get_property("visible")
        if (isVisible):
            print("isVisible")
            #w.hide()
        else:
            print("notVisible")
            self.list_window.show_all()

        #self.app_window.show()
        #print("Keypress")
        #textbox
        #read the contents of the file
        #text = open("yourfile").read()
        #get the underlying TextBuffer object of the TextView and set its text
        #textbox.get_buffer().set_text(text)


        # Program goes here  ...

        #app_window.show()
        
        # TODO 1
        
    def on_destroy(self, widget=None, *data):
        print("tried to destroy")
        self.console_window.hide_all()
        return False
    
    # TODO 2 link with hub
    def pause_or_resume(self, widget):
        if self.pauseResume.get_label() == "Pause":
            self.icon_file = icon_pause
            self.blinking = True
            self.pauseResume.set_label("Resume")
        elif self.pauseResume.get_label() == "Resume":
            self.icon_file = icon_resume
            self.blinking = False
            self.pauseResume.set_label("Pause")
        self.refresh()

    def quit(self, widget):
        global loop_continue
        dialog = gtk.MessageDialog(None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_WARNING,
            gtk.BUTTONS_OK_CANCEL, "Are you sure you want to close the SmartEgg Hub?")
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            loop_continue = False
            gtk.main_quit()
        #else :
        #    self.buffer.insert_at_cursor("\nNew text ")
    
    def refresh(self):
        if self.blinking:
            self.tray.set_tooltip("SmartEgg Hub Stopped!!!")
        else:
            self.tray.set_tooltip("SmartEgg Hub Running")
        
        if os.path.exists(self.icon_file):
            self.tray.set_from_file(self.icon_file)
        self.tray.set_blinking(self.blinking)
        
        return True


####################### HUB PART ##############################

# data service
DATA_SERVICE_UUID = "00001234-1212-efbe-1523-785fef13d123"
DATA_CHARACTERISTIC_UUID  = "0000abcd-1212-efbe-1523-785fef13d123"
DATA_STOP_CHARACTERISTIC_UUID = "0000bbbb-1212-efbe-1523-785fef13d123"
DATA_FILE_CHARACTERISTIC_UUID = "0000ffff-1212-efbe-1523-785fef13d123"

# time service
TIME_SERVICE_UUID = "0000da7a-1212-efde-1523-785fef13d123"
TIME_CHARACTERISTIC_UUID = "0000c2a5-1212-efde-1523-785fef13d123"

ERROR_CHARACTERISTIC_UUID = "0000e440-1212-efde-1523-785fef13d123"
ACCEL_CHARACTERISTIC_UUID = "00005e5e-1212-efde-1523-785fef13d123"

# devices register
regDevNames = {"e3:39:56:08:34:fc" : "SmartEgg 3", "f5:cd:27:15:a8:85" : "SmartEgg 509IT"}
regDevices  = {"e3:39:56:08:34:fc" : None, "f5:cd:27:15:a8:85" : None}

#regDevNames = {"f5:cd:27:15:a8:85" : "SmartEgg 1","f3:d4:33:fb:fc:51" : "SmartEgg 2","e3:39:56:08:34:fc" : "SmartEgg 3"}
#regDevices  = {"f5:cd:27:15:a8:85" : None,"f3:d4:33:fb:fc:51" : None, "e3:39:56:08:34:fc" : None}

# Accel Threshold & Duration
accel_threshold = 16
accel_duration = 1

# notifiers
data_notify = 0
stop_notify = 0
file_notify = 0

class MyDelegate(DefaultDelegate):
    
    stop = False
    f = None
    
    def __init__(self,name):
        DefaultDelegate.__init__(self)
        self.stop = False
        self.filename = " "
        self.device = name
        # ... initialise here

    def handleNotification(self, cHandle, data):
        global buffer
        
        if cHandle == data_notify.getHandle():
            if self.filename.startswith('H'):
                #TODO add to the temp list
                s =  '%d:%d:%d,%s,%s,%s,%s,%d,%d,%d\n' % (ord(data[0]), ord(data[1]), ord(data[2]), self.get_temperature(self.bytes_to_int(data[3:5])), self.get_temperature(self.bytes_to_int(data[5:7])), self.get_temperature(self.bytes_to_int(data[7:9])), self.get_temperature(self.bytes_to_int(data[9:11])), ord(data[11]), self.bytes_to_int(data[12:14]), self.bytes_to_int(data[14:16]))
                self.f.write(s)
            elif self.filename.startswith('A'):
                s =  '%d:%d:%d,%.2f,%.2f,%.2f\n' % (ord(data[0]), ord(data[1]), ord(data[2]), self.int_to_double(self.s32(self.bytes_to_int(data[3:7]))), self.int_to_double(self.s32(self.bytes_to_int(data[7:11]))), self.int_to_double(self.s32(self.bytes_to_int(data[11:15]))))
                #print ""
                self.f.write(s)
        elif cHandle == stop_notify.getHandle():
            self.f.close()
            self.stop = True
        elif cHandle == file_notify.getHandle():
            self.filename = data.decode('utf-8')
            buffer.insert(buffer.get_end_iter(), "\n%s %s " % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()), self.filename))
            print "%s %s " % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()), self.filename)
            file_path = "/home/pi/SmartEgg/data/"+ self.device+"/"+self.filename
            self.ensure_dir(file_path)
            self.f = open(file_path,"a")

    def ensure_dir(self, file_path):
        directory = os.path.dirname(file_path)
        #print "directory = %s" % directory
        #print os.path.exists(directory)
        if not os.path.exists(directory):
            #print "create dir %s" % directory
            os.makedirs(directory)

    def bytes_to_int(self, bytes):
        result = 0
        for b in reversed(bytes):
            result = result * 256 + ord(b)
        return result

    def s32(self, value):
        return -(value & 0x80000000) | (value & 0x7fffffff)
    
    
    def int_to_double(self, integer):
        result = float(integer)
        result = result/(1<<16)
        #print "%.2f %d" % (result,integer),
        # for b in reversed(bytes):
        #     result = result * 256 + ord(b)
        return result

    def get_temperature(self, adc):
        # read thermistor voltage drop and convert it to degrees of Celsius
        #value = self.read_adc(adc)               #read the adc
        volts = (adc * 3.3) / 4095        #calculate the voltage

        # check if the thermistor is connected to this channel
        if volts > 3.2:
            return ""
    
        ohms = (volts*10000)/(3.3-volts)    #calculate thermistor resistance
        lnohm = math.log1p(ohms)            #take ln(ohms)

        # a, b, & c values from www.rusefi.com/Steinhart-Hart.html
        # 0-50 C
        a =  0.001125256672
        b =  0.0002347204473
        c =  0.00000008563052732

        # Steinhart Hart Equation
        # T = 1/(a + b[ln(ohm)] + c[ln(ohm)]^3)
        t1 = (b*lnohm)                      #b[ln(ohm)]
        c2 = lnohm                          #c[ln(ohm)]
        t2 = c*math.pow(c2,3)               #c[ln(ohm)]^3
        temp = 1/(a + t1 + t2)              #calcualte temperature in K
        tempc = temp - 273.15               #K to C

        #print out info
    # print ("%4d/4095 => %5.4f V => %6.1f ? => %5.2f °K => %3.1f °C from adc %d" % (adc, volts, ohms, temp, tempc, adc))
        #log.write("%4d,%5.4fV,%6.1f,%5.2f,%3.1f,adc %d" % (value, volts, ohms, temp, tempc, adc))
        #self.temperature.append("%3.1f" % tempc)
        return "%3.1f" % tempc        

    def enable_notify(self, chara_uuid):
        setup_data = b"\x01\x00"
        notify = self.ble_conn.getCharacteristics(uuid=chara_uuid)[0]
        notify_handle = notify.getHandle() + 1
        self.ble_conn.writeCharacteristic(notify_handle, setup_data, withResponse=True)

def connectAndGetCharacteristic(d, characteristics):
    ch = d.getCharacteristics(1, int('0xFFFF',16), characteristics)
    if (ch[0].uuid == characteristics):
        return ch[0]
    else:
        return None

def areRegDevicesInRange(devices):
    # reset register from previous check
    for k,v in regDevices.items():
        regDevices[k] = None
    for dev in devices:
        if dev.addr in regDevices:
            regDevices[dev.addr]= dev

def calibrateTimeAndGetData():
    global data_notify
    global stop_notify
    global file_notify
    global buffer
    for k,v in regDevices.items():
        if v is not None:
            device = Peripheral(regDevices[k])
            delegate = MyDelegate(regDevNames[regDevices[k].addr])
            device.setDelegate( delegate)

            # check for errors
            #errorChar = connectAndGetCharacteristic(device, ERROR_CHARACTERISTIC_UUID)
            #if errorChar is not None:
            #    error = ord(errorChar.read())
            #    if error != 0: 
            #        print '\r\n%s %s (%s) ERROR CODE = %d' % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()), regDevNames[regDevices[k].addr], regDevices[k].addr, error)
                    # TODO ADD exclusion so that the egg with error is not checked again and again
            #        break
                
            # calibrate time
            timeChar = connectAndGetCharacteristic(device, TIME_CHARACTERISTIC_UUID)
            if timeChar is not None:
                localtime = time.localtime(time.time())
                timeChar.write(chr(localtime.tm_year-1900)+chr(localtime.tm_mon-1)+chr(localtime.tm_mday)+chr(localtime.tm_hour)+chr(localtime.tm_min)+chr(localtime.tm_sec))

            # check accelerator sensitivity
            accelChar = connectAndGetCharacteristic(device, ACCEL_CHARACTERISTIC_UUID)
            if accelChar is not None:
                sensitivity = accelChar.read()
                threshold = ord(sensitivity[0])
                duration = ord(sensitivity[1])
                buffer.insert(buffer.get_end_iter(), "\r\nAccel Threshold = %d | duration = %d" % (threshold, duration))
                print "\r\nAccel Threshold = %d | duration = %d" % (threshold, duration)
                if accel_threshold == threshold and accel_duration == duration:
                    buffer.insert(buffer.get_end_iter(), "\r\nAccel Threshold not changed")
                    print "\r\nAccel Threshold not changed"
                else:
                    accelChar.write(chr(accel_threshold)+chr(accel_duration))
                    sensitivity = accelChar.read()
                    threshold = ord(sensitivity[0])
                    duration = ord(sensitivity[1])
                    buffer.insert(buffer.get_end_iter(), "\r\nAccel Threshold Set to = %d | duration set to = %d" % (threshold, duration))
                    print "\r\nAccel Threshold Set to = %d | duration set to = %d" % (threshold, duration)
            
            # get data
            svc = device.getServiceByUUID( DATA_SERVICE_UUID )

            # enable notification on data characteristic
            setup_data = b"\x01\x00"
            data_notify = svc.getCharacteristics(DATA_CHARACTERISTIC_UUID)[0]
            data_notify_handle = data_notify.getHandle() + 1
            device.writeCharacteristic(data_notify_handle, setup_data, withResponse=True)
            
            # enable notification on stop characteristic
            stop_notify = svc.getCharacteristics(DATA_STOP_CHARACTERISTIC_UUID)[0]
            stop_notify_handle = stop_notify.getHandle() + 1
            device.writeCharacteristic(stop_notify_handle, setup_data, withResponse=True)

            # enable notification on file characteristic
            file_notify = svc.getCharacteristics(DATA_FILE_CHARACTERISTIC_UUID)[0]
            file_notify_handle = file_notify.getHandle() + 1
            device.writeCharacteristic(file_notify_handle, setup_data, withResponse=True)

            print "Transfer:"
            buffer.insert(buffer.get_end_iter(), "\nTransfer:")
            # data transfer loop
            try:
                while not delegate.stop:
                    # TODO list empty                        
                    device.waitForNotifications(10.0)
            except BTLEException as e:
                buffer.insert(buffer.get_end_iter(), "\n%s BTLEException raised. Transfered data incomplete. Check SD card." % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())))
                print "%s BTLEException raised. Transfered data incomplete. Check SD card." % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()))

            # data transfer finish
            device.disconnect()
            # TODO Load to DB


                                             
            buffer.insert(buffer.get_end_iter(), "\nData transfer from %s (%s) finished!" % (regDevNames[regDevices[k].addr], regDevices[k].addr))
            print "Data transfer from %s (%s) finished!" % (regDevNames[regDevices[k].addr], regDevices[k].addr)


def loop():
    global buffer
    i="|"
    # Scan for devices in range
    while loop_continue:
        if i=="|":
            i="/"
        elif i=="/":
            i="-"
        elif i=="-":
            i="\\"    
        elif i=="\\":
            i="|"
        #index = buffer.get_end_iter()
        #index.backward_cursor_position()
        buffer.backspace(buffer.get_end_iter(), False, True)
        buffer.insert(buffer.get_end_iter(), i)
        #buffer.insert(buffer.get_end_iter(),"\ntest")
        #print ".",
        scanner = Scanner().withDelegate(MyDelegate(""))
        devices = scanner.scan(10.0)

        # Check which registered devices are in range and update register
        areRegDevicesInRange(devices)

        # Calibrate time of all registered devices in range and get their data
        try:
            calibrateTimeAndGetData()
        except BTLEException as e:
            buffer.insert(buffer.get_end_iter(), "\n%s BTLEException raised at Calibrate . Transfered data incomplete. Check SD card." % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())))
            print "%s BTLEException raised at Calibrate . Transfered data incomplete. Check SD card." % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()))



###############################################################################
if __name__ == '__main__':
    app = SmartEggTray()
    glib.threads_init()
    gdk.threads_init()
    gdk.threads_enter()
    gtk.main()
    gdk.threads_leave()
    
