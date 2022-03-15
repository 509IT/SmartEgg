#!/usr/bin/python
# -*- coding: utf-8 -*-
from bluepy.btle import *
import time
import math
import io
import os

# data service
DATA_SERVICE_UUID = "00001234-1212-efbe-1523-785fef13d123"
DATA_CHARACTERISTIC_UUID  = "0000abcd-1212-efbe-1523-785fef13d123"
DATA_STOP_CHARACTERISTIC_UUID = "0000bbbb-1212-efbe-1523-785fef13d123"
DATA_FILE_CHARACTERISTIC_UUID = "0000ffff-1212-efbe-1523-785fef13d123"

# time service
TIME_SERVICE_UUID = "0000da7a-1212-efde-1523-785fef13d123"
TIME_CHARACTERISTIC_UUID = "0000c2a5-1212-efde-1523-785fef13d123"

ERROR_CHARACTERISTIC_UUID = "0000e440-1212-efde-1523-785fef13d123"

# devices register
regDevNames = {"f5:cd:27:15:a8:85" : "SmartEgg 1","f3:d4:33:fb:fc:51" : "SmartEgg 2"}
regDevices  = {"f5:cd:27:15:a8:85" : None,"f3:d4:33:fb:fc:51" : None}

# notifiers
data_notify = 0
stop_notify = 0
file_notify = 0

#filee = open(“testfile.txt”,”w”)

class MyDelegate(DefaultDelegate):
    
    stop = False
    f = None
    
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.stop = False
        self.filename = " "
        # ... initialise here

    def handleNotification(self, cHandle, data):
        if cHandle == data_notify.getHandle():
            if self.filename.startswith('H'):
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
            print "%s %s " % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()), self.filename)
            self.f = open(self.filename,"a")

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
    for k,v in regDevices.items():
        if v is not None:
            device = Peripheral(regDevices[k])
            delegate = MyDelegate()
            device.setDelegate( delegate)

            # check for errors
            errorChar = connectAndGetCharacteristic(device, ERROR_CHARACTERISTIC_UUID)
            if errorChar is not None:
                error = ord(errorChar.read())
                if error != 0: 
                    print '\r\n%s %s (%s) ERROR CODE = %d' % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()), regDevNames[regDevices[k].addr], regDevices[k].addr, error)
                    # TODO ADD exclusion so that the egg with error is not checked again and again
                    break
                
            # calibrate time
            timeChar = connectAndGetCharacteristic(device, TIME_CHARACTERISTIC_UUID)
            if timeChar is not None:
                localtime = time.localtime(time.time())
                timeChar.write(chr(localtime.tm_year-1900)+chr(localtime.tm_mon-1)+chr(localtime.tm_mday)+chr(localtime.tm_hour)+chr(localtime.tm_min)+chr(localtime.tm_sec))

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

            print "\r\nTransfer:"
            
            # data transfer loop
            try:
                while not delegate.stop:
                    device.waitForNotifications(5.0)
            except BTLEException as e:
                print "%s BTLEException raised. Transfered data incomplete. Check SD card." % (time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()))

            # data transfer finish
            device.disconnect()
            print "Data transfer from %s (%s) finished!" % (regDevNames[regDevices[k].addr], regDevices[k].addr)
            
############################## MAIN ####################################      
# Scan for devices in range
while True:
    print ".",
    scanner = Scanner().withDelegate(MyDelegate())
    devices = scanner.scan(10.0)

    # Check which registered devices are in range and update register
    areRegDevicesInRange(devices)

    # Calibrate time of all registered devices in range and get their data
    calibrateTimeAndGetData()
