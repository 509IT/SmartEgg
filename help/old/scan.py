from bluepy.btle import *
import time;

TIME_SERVICE_UUID = "0000da7a-1212-efde-1523-785fef13d123"
TIME_CHARACTERISTIC_UUID = "0000c2a5-1212-efde-1523-785fef13d123"

# Devices register
regDevNames = {"f5:cd:27:15:a8:85" : "SmartEgg 1","f3:d4:33:fb:fc:51" : "SmartEgg 2"}
regDevices  = {"f5:cd:27:15:a8:85" : None,"f3:d4:33:fb:fc:51" : None}
# Add all devices that need to be controled here

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    #def handleDiscovery(self, dev, isNewDev, isNewData):
       # if isNewDev:
            ##print ("Discovered device", dev.addr, )
       # elif isNewData:
            ##print "Received new data from", dev.addr

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
            
def calibrateTime():
    for k,v in regDevices.items():
        if v is not None:
            device = Peripheral(regDevices[k])
            timeChar = connectAndGetCharacteristic(device, TIME_CHARACTERISTIC_UUID)
            #year = (localtime.tm_year-1900)
            #month = (localtime.tm_mon-1)
            #print "Formated Local current time: %s-%s-%s %s:%s:%s" % (str(year), str(month), str(localtime.tm_mday), str(localtime.tm_hour),str(localtime.tm_min),str(localtime.tm_sec))
            #print "Hex Local current time: %s-%s-%s-%s-%s-%s" % (format(year, '02X'), format(month, '02X'), format(localtime.tm_mday, '02X'), format(localtime.tm_hour, '02X'), format(localtime.tm_min, '02X'), format(localtime.tm_sec , '02X'))
            if timeChar is not None:
                localtime = time.localtime(time.time())
                timeChar.write(chr(localtime.tm_year-1900)+chr(localtime.tm_mon-1)+chr(localtime.tm_mday)+chr(localtime.tm_hour)+chr(localtime.tm_min)+chr(localtime.tm_sec))
                print ""
                print "%s-%s-%s %s:%s:%s  ->  %s time set to = %s-%s-%s-%s-%s-%s" % (localtime.tm_year, localtime.tm_mon, localtime.tm_mday, localtime.tm_hour, localtime.tm_min, localtime.tm_sec, regDevNames[k],
                                                                                     format(localtime.tm_year-1900, 'x'), format(localtime.tm_mon-1, 'x'), format(localtime.tm_mday, 'x'), format(localtime.tm_hour, 'x'), format(localtime.tm_min, 'x'), format(localtime.tm_sec , 'x'))
            device.disconnect()

############################## MAIN ####################################
            
# Scan for devices in range
while True:
    print ".",
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(10.0)

    # Check which registered devices are in range and update register
    areRegDevicesInRange(devices)

    # Calibrate time of all registered devices in range
    calibrateTime()

    

# 
#for dev in devices:
#    if dev.addr in regDevices:
#    #if dev.addr in zip(*regDevices)[0]:
#        print "Device from the REGISTERED Devices LIST was found!"
#        device = Peripheral(dev)
#        characteristic = device.getCharacteristics(1, int('0xFFFF',16), TIME_CHARACTERISTIC_UUID)
#        if (characteristic[0].uuid == TIME_CHARACTERISTIC_UUID):
#            regDevices[dev.addr]= characteristic[0]
#            characteristic[0].write(chr(255)) # writes 0xFF to buffer
#            print "TIME Service found and Characteristic add to the list!"
        #services = device.getServices()
        #for service in services:
        #    if ( service.uuid == TIME_SERVICE_UUID):
        #        characteristics = service.getCharacteristics()
        #        for character in characteristics:
        #            if ( character.uuid == TIME_CHARACTERISTIC_UUID):
        #                zip(*regDevices)[2] = character
        #                print "TIME Service found and Characteristic add to the list!"

 #   print "Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi)
 #   for (adtype, desc, value) in dev.getScanData():
 #      print "  %s = %s" % (desc, value)

#device = Peripheral(regDevices[0][0],regDevices[0][1],0)
#services = device.getServices()
#for service in services:
#    if ( service.uuid == TIME_SERVICE_UUID):
#        print "TIME Service:"
#        characteristics = service.getCharacteristics()
#        for character in characteristics:
#             print "    Characteristic UUID = %s" % (character.uuid)
#    else:
#        print "Service = %s" % (service.uuid)

#while(True):
#    action = raw_input("Update time (y/n):")

#    if action == "y" :
#        calibrateTime()
#    elif action =="n":
#        print "Bye Bye!"
#        break
    
