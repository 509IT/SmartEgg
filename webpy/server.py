#!/usr/bin/python
import web
#import smbus
import math
import csv

urls = (
    '/', 'index'
)

csvfile = open('A_180516.txt','rb')
reader = csv.reader(csvfile, delimiter=',')

def dist(a,b):
    return math.sqrt((a*a)+(b*b))

def get_roll(x,y,z):
    radians = math.atan2(x, y)
    return math.degrees(radians)

def get_pitch(x,y,z):
    radians = math.atan2((-z) , dist(x,y))
    return math.degrees(radians)

class index:
    def GET(self):
        global reader
        line = next(reader)

        time              = line[0]
        accel_xout_scaled = float(line[1])
        accel_yout_scaled = float(line[2])
        accel_zout_scaled = float(line[3])

        return str(time)+" "+str(get_roll(accel_xout_scaled,accel_yout_scaled,accel_zout_scaled))+" "+str(get_pitch(accel_xout_scaled,accel_yout_scaled,accel_zout_scaled))
    
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
