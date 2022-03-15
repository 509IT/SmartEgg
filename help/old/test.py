from bluepy.btle import *
import time;

DATA_SERVICE_UUID = "00001234-1212-efbe-1523-785fef13d123"
DATA_CHARACTERISTIC_UUID  = "0000abcd-1212-efbe-1523-785fef13d123"
DATA_STOP_CHARACTERISTIC_UUID = "0000bbbb-1212-efbe-1523-785fef13d123"

TIME_SERVICE_UUID = "0000da7a-1212-efde-1523-785fef13d123"
TIME_CHARACTERISTIC_UUID = "0000c2a5-1212-efde-1523-785fef13d123"

d_notify = 0
s_notify = 0

class MyDelegate(DefaultDelegate):
    
    stop = False
    
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.stop = False
        # ... initialise here

    def handleNotification(self, cHandle, data):
        if cHandle == s_notify.getHandle():
            print "STOP NOTIFY"
            self.stop = True
        #print cHandle
        for i in data:
            print "%s " % (format(ord(i), '02X')),
        print ""
        #print "Notification = " data
        # ... perhaps check cHandle
        # ... process 'data'

    def enable_notify(self,  chara_uuid):
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

# Initialisation  -------
print ".",
scanner = Scanner().withDelegate(MyDelegate())
devices = scanner.scan(10.0)

for dev in devices:
    if dev.addr=="f5:cd:27:15:a8:85":
        print "Found device Connect"
        p = Peripheral(dev)
        delegate = MyDelegate()
        p.setDelegate( delegate )
        print "Connected and set delegate"

        timeChar = connectAndGetCharacteristic(p, TIME_CHARACTERISTIC_UUID)
            
        if timeChar is not None:
            localtime = time.localtime(time.time())
            timeChar.write(chr(localtime.tm_year-1900)+chr(localtime.tm_mon-1)+chr(localtime.tm_mday)+chr(localtime.tm_hour)+chr(localtime.tm_min)+chr(localtime.tm_sec))
            #print ""
            #print "%s-%s-%s %s:%s:%s  ->  %s time set to = %s-%s-%s-%s-%s-%s" % (localtime.tm_year, localtime.tm_mon, localtime.tm_mday, localtime.tm_hour, localtime.tm_min, localtime.tm_sec, regDevNames[k],
            #                                                                         format(localtime.tm_year-1900, 'x'), format(localtime.tm_mon-1, 'x'), format(localtime.tm_mday, 'x'), format(localtime.tm_hour, 'x'), format(localtime.tm_min, 'x'), format(localtime.tm_sec , 'x'))

        print "Time set"
        
        svc = p.getServiceByUUID( DATA_SERVICE_UUID )
     #   ch = svc.getCharacteristics( DATA_CHARACTERISTIC_UUID )[0]

        setup_data = b"\x01\x00"
        d_notify = svc.getCharacteristics(DATA_CHARACTERISTIC_UUID)[0]
        data_notify_handle = d_notify.getHandle() + 1
        p.writeCharacteristic(data_notify_handle, setup_data, withResponse=True)

        s_notify = svc.getCharacteristics(DATA_STOP_CHARACTERISTIC_UUID)[0]
        stop_notify_handle = s_notify.getHandle() + 1
        p.writeCharacteristic(stop_notify_handle, setup_data, withResponse=True)
      #  enable_notify(DATA_CHARACTERISTIC_UUID)

        while not delegate.stop:
            p.waitForNotifications(5.0)#
                #print "handleNotification() was called"
                #continue

            #print "Waiting..."
        print "Finished transfer"
    # Perhaps do something else here
# Setup to turn notifications on, e.g.
#   svc = p.getServiceByUUID( service_uuid )
#   ch = svc.getCharacteristics( char_uuid )[0]
#   ch.write( setup_data )

# Main loop --------

