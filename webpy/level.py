#!/usr/bin/python

import pygame
import Tkinter as tk
from Tkinter import *
import Tkconstants, tkFileDialog

import os

import urllib
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from math import radians
import math
import csv
from pygame.locals import *
#from OpenGLContext.arrays import array
import collections
import argparse
#from termcolor import colored
from tkintertable import TableCanvas, TableModel, RowHeader

SCREEN_SIZE = (700, 600)
SCALAR = .5
SCALAR2 = 0.2

# parse arguments, get date from file name, open csv file and initiate reader
'''parser = argparse.ArgumentParser(description='3D Smart Egg Visualisation')
parser.add_argument('file', nargs=1, help='file to be displayed')
args = parser.parse_args()
day = args.file[0][6:8]
month = args.file[0][4:6]
year = args.file[0][2:4]
csvfile = open(args.file[0], 'rb')
reader = csv.reader(csvfile, delimiter=',')
'''
lines = []
file_pointer = -1
reader = 0
time = ''
x_angle = 0
y_angle = 0
day = ''
month = ''
year = ''
table = None
model = None
data = {}

# tk init
#root = tk.Tk()
#root.title('Smart Egg 3D Visualisation')
#root.geometry("800x600")    #Set the size of the app to be 800x600
#root.resizable(0, 0)        #Don't allow resizing in the x or y direction

def resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(width) / height, 0.001, 10.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(-7.0, 3.0, 0.0,
              0.0, 0.0, 0.0,
              0.0, 1.0, 0.0)

def keyPressed(*args):
    if args[0] == ESCAPE:
      glutDestroyWindow(window)
      sys.exit()

def dist(a,b):
    return math.sqrt((a*a)+(b*b))

def get_roll(x,y,z):
    radians = math.atan2(x, y)
    return math.degrees(radians)

def get_pitch(x,y,z):
    radians = math.atan2((-z) , dist(x,y))
    return math.degrees(radians)


def init():
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_BLEND)
    glEnable(GL_POLYGON_SMOOTH)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    #glDisable(GL_LIGHT0)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.6, 0.6, 0.6, 1.0));

    glEnable(GL_NORMALIZE)

def load_data(filename):
    global data, day, month, year

    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in reader:
            # get values from file
            time    = day+"-"+month+"-"+year+"/"+row[0]
            x       = float(row[1])
            y       = float(row[2])
            z       = float(row[3])
            # add tuple to a dictionary
            data.update( { i : dict(zip(['time', 'x', 'y', 'z'], [time, x, y, z]))} )
            i += 1

def get_record(index):
    return data.get(index)

def read_previous_values():
    global reader
    global file_pointer
    if file_pointer <= 0:
        return

    file_pointer = file_pointer-1
    line = lines[file_pointer]
    
    print "Rekord nr:"+ str(file_pointer)
    print str(line)
    
    time              = day+"-"+month+"-"+year+"/"+line[0]
    accel_xout_scaled = float(line[1])
    accel_yout_scaled = float(line[2])
    accel_zout_scaled = float(line[3])

    result = str(time)+" "+str(get_roll(accel_xout_scaled,accel_yout_scaled,accel_zout_scaled))+" "+str(get_pitch(accel_xout_scaled,accel_yout_scaled,accel_zout_scaled))
    return result.split(" ")

def read_next_values():
    global reader
    global file_pointer

    if file_pointer >= len(lines)-1:
        line = next(reader, None)
        if line == None:
            return
        lines.append(line)

    file_pointer = file_pointer+1
    line = lines[file_pointer]
    
    print "Rekord nr:"+ str(file_pointer)
    print str(line)
    
    time              = day+"-"+month+"-"+year+"/"+line[0]
    accel_xout_scaled = float(line[1])
    accel_yout_scaled = float(line[2])
    accel_zout_scaled = float(line[3])

    result = str(time)+" "+str(get_roll(accel_xout_scaled,accel_yout_scaled,accel_zout_scaled))+" "+str(get_pitch(accel_xout_scaled,accel_yout_scaled,accel_zout_scaled))
    return result.split(" ")

def drawText(x, y, text):                                                
    position = (x, y, -3)                                                       
    font = pygame.font.Font(None, 30)                                          
    textSurface = font.render(text, True, (255,255,255,255),(0,0,0,255))                                     
    textData = pygame.image.tostring(textSurface, "RGBA", True)                
    glRasterPos3d(*position)                                                
    glDrawPixels(textSurface.get_width(), textSurface.get_height(),         
                    GL_RGBA, GL_UNSIGNED_BYTE, textData)   
def donothing():
    filewin = Toplevel(root)
    button = Button(filewin, text="Do nothing button")
    button.pack()

def openfile():
    global reader, time, x_angle, y_angle,day, month, year, table, model, data
    name = tkFileDialog.askopenfilename(initialdir = ".",title = "Select file", filetypes =(("Text File", "*.txt"),("All Files","*.*")))

    print (name)
    
    #Using try in case user types in unknown file or closes without choosing a file.
    try:

        path = name.split('/')
        date = path[len(path)-1]
        print date
        day = date[6:8]
        month = date[4:6]
        year = date[2:4]

        # load data
        load_data(name)
        model = table.model
        model.importDict(data)
        # arrange columns width and order
        model.moveColumn(model.getColumnIndex('time'),1)
        model.moveColumn(model.getColumnIndex('x'),2)
        model.moveColumn(model.getColumnIndex('y'),3)
        model.moveColumn(model.getColumnIndex('z'),4)
        model.columnwidths['time'] = 150
        
        table.redrawTable()
        
        csvfile = open(name, 'rb')
        reader = csv.reader(csvfile, delimiter=',')

        # read first element
        values = read_next_values()
        if values != None:
            time = values[0]
            x_angle = values[1]
            y_angle = values[2]

    except:
        print("No file exists")

def closefile():
    global reader, time, x_angle, y_angle,day, month, year, file_pointer, data, model, table
    name = ''
    reader = 0
    time = ''
    x_angle = 0
    y_angle = 0
    day = ''
    month = ''
    year = ''
    file_pointer = -1
    # clear dataset
    data = {}
    model = table.model
    model.createEmptyModel()
    table.redrawTable()
    
def clicked(event):  #Click event callback function.
    global table

    #print table.isInsideTable(event.x,event.y)
    if isinstance(event.widget, (TableCanvas, RowHeader)):
         print "Cliked record "

    # TODO - record selection handling

    #Probably needs better exception handling, but w/e.
    '''try:
        rclicked = table.get_row_clicked(event)
        cclicked = table.get_col_clicked(event)
        clicks = (rclicked, cclicked)
        print 'clicks:', clicks
    except: 
        print 'Error'
    if clicks:
        #Now we try to get the value of the row+col that was clicked.
        try: print 'single cell:', table.model.getValueAt(clicks[0], clicks[1])
        except: print 'No record at:', clicks

        #This is how you can get the entire contents of a row.
        try: print 'entire record:', table.model.getRecordAtRow(clicks[0])
        except: print 'No record at:', clicks
    '''        
def run():
    global reader, time, x_angle, y_angle, day, month, year, table, model
    
    # tk init
    root = tk.Tk()
    root.title('Smart Egg 3D Visualisation')
    root.geometry("1100x650")    #Set the size of the app to be 800x600
    #root.resizable(0, 0)        #Don't allow resizing in the x or y direction

    # Initializa Menubar
    menubar = Menu(root)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open file", command=openfile)
    filemenu.add_command(label="Close file", command=closefile)
    #filemenu.add_separator()
    #filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)
    
    # Create embed frame for pygame window
    embed = tk.Frame(root, width=700, height=600) 
    embed.grid(row=0,column=0)
    # Create embed frame for records preview console
    records = tk.Frame(root, width=300, height=600)
    records.grid(row=0,column=1)
    records.pack_propagate(0)
    # Create Table for records preview
    model = TableModel()
    table = TableCanvas(records,name="tablica",model=model, width=300, height=600, cols=0, rows=0,  cellwidth=50, editable=False, showkeynamesinheader=True, reverseorder=0)
    table.grid(row=0,sticky=W+N+S)
    table.createTableFrame()

    root.bind('<ButtonRelease-1>', clicked)   #Bind the click release event
    
    #data = {"age":25}#dict((k,2) for k in a)
    #data = {'rec1': {'time': '12:04:44', 'x': 99.88, 'y': 108.79, 'z': 108.79},
    #        'rec2': {'time': '12:04:45','x': 99.88, 'y': 108.79, 'z': 108.79}}
    #model = table.model
    #model.importDict(data) #can import from a dictionary to populate model
    #model.moveColumn(model.getColumnIndex('time'),0)
    #model.moveColumn(model.getColumnIndex('x'),1)
    #model.moveColumn(model.getColumnIndex('y'),2)
    #model.moveColumn(model.getColumnIndex('z'),3)
    #table.autoResizeColumns()
    #table.redrawTable()
    #button1 = Button(records,text = 'Draw',  command=donothing)
    #button1.pack(side=LEFT)
    #os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
    #os.environ['SDL_VIDEODRIVER'] = 'windib'

    #os.environ["SDL_VIDEODRIVER"] = "dummy"
    
    screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE | OPENGL | DOUBLEBUF)
    resize(*SCREEN_SIZE)
    #screen.fill(pygame.Color(255,255,255))
    pygame.init()
    pygame.display.init()
    #pygame.display.update()

    root.update()  

    init()
    clock = pygame.time.Clock()
    egg = Egg2((0.7, 0.0, 0.0), (1, .95, .8))
    #cube = Cube((0.0, 0.0, 0.0), (1, .95, .8))
    angle = 0
    
    # turn off autoplay
    play = False
    if file_pointer != -1:
        # read first element
        values = read_next_values()
        if values != None:
            time = values[0]
            x_angle = values[1]
            y_angle = values[2]
    
    while True:
        then = pygame.time.get_ticks()

        # TODO 1: Key control
        # TODO 2: Mark Temperature sensors are reference
        # TODO 3: Shading
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYUP:
                if event.key == K_UP:
                    print colored('Odtwarzanie automatyczne','green')
                    play = True
                if event.key == K_DOWN:
                    print colored('Pauza','red')
                    play = False
                if play or event.key == K_RIGHT:
                    values = read_next_values()
                    if values == None:
                        print colored('Koniec Pliku!','red')
                    else:
                        time = values[0]
                        x_angle = values[1]
                        y_angle = values[2]
                if event.key == K_LEFT:
                    values = read_previous_values()
                    if values == None:
                        print colored('Poczatek pliku!','green')
                    else:
                        time = values[0]
                        x_angle = values[1]
                        y_angle = values[2]
                if event.key == K_ESCAPE:
                    return

        # autoplay mode
        if play:
            values = read_next_values()
            if values == None:
                print colored('Koniec Pliku!','red')
            else:
                    time = values[0]
                    x_angle = values[1]
                    y_angle = values[2]
                   

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glColor((1.,1.,1.))
        glLineWidth(1)
        glBegin(GL_LINES)

        # uklad wspolrzedny (x, y, z)
        for x in range(-20, 22, 2):
            glVertex3f(x/10.,-1,-2)
            glVertex3f(x/10.,-1,2)
    
        '''for x in range(-20, 22, 2):
            glVertex3f(x/10.,-1, 1)
            glVertex3f(x/10., 1, 1)
        '''
        for z in range(-20, 22, 2):
            glVertex3f(-2, -1, z/10.)
            glVertex3f( 2, -1, z/10.)
        
        '''for z in range(-10, 12, 2):
            glVertex3f(-2, -1, z/10.)
            glVertex3f(-2,  1, z/10.)
        
        for z in range(-10, 12, 2):
            glVertex3f( 2, -1, z/10.)
            glVertex3f( 2,  1, z/10.)
        
        for y in range(-10, 12, 2):
            glVertex3f(-2, y/10., 1)
            glVertex3f( 2, y/10., 1)
        
        for y in range(-10, 12, 2):
            glVertex3f(-2, y/10., 1)
            glVertex3f(-2, y/10., -1)
        
        for y in range(-10, 12, 2):
            glVertex3f(2, y/10., 1)
            glVertex3f(2, y/10., -1)
        '''
        glEnd()

        # draw xyz axis
        glLineWidth(2)
        glBegin(GL_LINES)
        # draw line for x axis
        glColor3f(1.0, 0.0, 0.0)

        glVertex3f(-2.2, -1.0, -2.4);
        glVertex3f(-1.2, -1.0, -2.4);
        glVertex3f(-1.2, -1.0, -2.4);
        glVertex3f(-1.3, -0.98, -2.4);
        glVertex3f(-1.3, -0.98, -2.4);
        glVertex3f(-1.3, -1.02, -2.4);
        glVertex3f(-1.3, -1.02, -2.4);
        glVertex3f(-1.2, -1.0, -2.4);

        # draw line for y axis
        glColor3f(0.0, 1.0, 0.0)

        glVertex3f(-2.2, -1.0, -2.4);
        glVertex3f(-2.2, -0.6, -2.4);
        glVertex3f(-2.2, -0.6, -2.4);
        glVertex3f(-2.22, -0.7, -2.4);
        glVertex3f(-2.22, -0.7, -2.4);
        glVertex3f(-2.18, -0.7, -2.4);
        glVertex3f(-2.18, -0.7, -2.4);
        glVertex3f(-2.2, -0.6, -2.4);

        # draw line for z axis
        glColor3f(0.0, 0.0, 1.0)

        glVertex3f(-2.2, -1.0, -2.4);
        glVertex3f(-2.2, -1.0, -2.0);
        glVertex3f(-2.2, -1.0, -2.0);
        glVertex3f(-2.18, -1.0, -2.1);
        glVertex3f(-2.18, -1.0, -2.1);
        glVertex3f(-2.22, -1.0, -2.1);
        glVertex3f(-2.22, -1.0, -2.1);
        glVertex3f(-2.2, -1.0, -2.0);
        
        glEnd()
        
        if file_pointer != -1:
            glPushMatrix()
            # Correct
            glRotate(float(x_angle), 0, 0, 1)
            glRotate(float(y_angle), 1, 0, 0)
            #glRotate(float(x_angle), 1, 0, 0)
            #glRotate(-float(y_angle), 0, 0, 1)
            #cube.render()
            egg.render()
            glPopMatrix()

            drawText(0, 2, time)
            
        pygame.display.flip()
        root.update() 


class Cube(object):

    def __init__(self, position, color):
        self.position = position
        self.color = color

    # Cube information
    num_faces = 6

    vertices = [ (-1.0, -0.05, 0.5),
                 (1.0, -0.05, 0.5),
                 (1.0, 0.05, 0.5),
                 (-1.0, 0.05, 0.5),
                 (-1.0, -0.05, -0.5),
                 (1.0, -0.05, -0.5),
                 (1.0, 0.05, -0.5),
                 (-1.0, 0.05, -0.5) ]

    normals = [ (0.0, 0.0, +1.0),  # front
                (0.0, 0.0, -1.0),  # back
                (+1.0, 0.0, 0.0),  # right
                (-1.0, 0.0, 0.0),  # left
                (0.0, +1.0, 0.0),  # top
                (0.0, -1.0, 0.0) ]  # bottom

    vertex_indices = [ (0, 1, 2, 3),  # front
                       (4, 5, 6, 7),  # back
                       (1, 5, 6, 2),  # right
                       (0, 4, 7, 3),  # left
                       (3, 2, 6, 7),  # top
                       (0, 1, 5, 4) ]  # bottom

    '''vertices = [ (-0.5, -0.05, 2.0),
                 (0.5, -0.05, 2.0),
                 (0.5, 0.05, 2.0),
                 (-0.5, 0.05, 2.0),
                 (-0.5, -0.05, -2.0),
                 (0.5, -0.05, -2.0),
                 (0.5, 0.05, -2.0),
                 (-0.5, 0.05, -2.0) ]

    normals = [ (0.0, 0.0, +1.0),  # front
                (0.0, 0.0, -1.0),  # back
                (+1.0, 0.0, 0.0),  # right
                (-1.0, 0.0, 0.0),  # left
                (0.0, +1.0, 0.0),  # top
                (0.0, -1.0, 0.0) ]  # bottom

    vertex_indices = [ (0, 1, 2, 3),  # front
                       (4, 5, 6, 7),  # back
                       (1, 5, 6, 2),  # right
                       (0, 4, 7, 3),  # left
                       (3, 2, 6, 7),  # top
                       (0, 1, 5, 4) ]  # bottom
    '''
    
    def render(self):
        then = pygame.time.get_ticks()
        glColor(self.color)

        vertices = self.vertices

        # Draw all 6 faces of the cube
        glBegin(GL_QUADS)

        for face_no in xrange(self.num_faces):
            #if face_no == 1:
            #    glColor((.5, .1, .1))
            #elif face_no == 4:
            #    glColor((.1, .1, .8))
            #else:
            #glColor((.5, .5, .7))
            glNormal3dv(self.normals[face_no])
            v1, v2, v3, v4 = self.vertex_indices[face_no]
            glVertex(vertices[v1])
            glVertex(vertices[v2])
            glVertex(vertices[v3])
            glVertex(vertices[v4])
        glEnd()
        

class Egg2(object):
    # Egg information
    radius = -(math.pi/2)
    N = 8   

    vertices = [(0,0,-1.85)]
    vertex_indices = [(0,1,2),
                      (0,2,3),
                      (0,3,4),
                      (0,4,5),
                      (0,5,6),
                      (0,6,7),
                      (0,7,8),
                      (0,8,1)]
    
   
    
    normals = []
    
    vertexNorm = []


    Point3D = collections.namedtuple('Point3D', 'x y z')

    

    def __init__(self, position, color):
        self.position = position
        self.color = color
        
        #self.vertices = [(0,0,-2)]

        # calculate egg vertices
        for z in range(-18, 2, 2):
            i=0

            self.radius = self.radius - ((math.pi/2)/10)
            for j in xrange(self.N):
                i= i+math.pi/4
                self.vertices.append((math.cos(i) * math.cos(self.radius), math.sin(i) * math.cos(self.radius), float(z)/10))

        for z in range(2, 10, 2):
            i=0
            self.radius = self.radius + ((math.pi/2)/5)
            for j in xrange(self.N):
                i= i+math.pi/4
                self.vertices.append((math.cos(i) * math.cos(self.radius), math.sin(i) * math.cos(self.radius), float(z)/10))

        self.vertices.append((0,0,0.85))

        print len(self.vertices)
                                     
        # calculate egg faces through vertex indices
        for i in range(0, ((len(self.vertices)-1)/self.N)-1, 1):
            for j in range(1,self.N,1):
                self.vertex_indices.append(((i*8)+j, (i*8)+(j+1), (i*8)+(j+9), (i*8)+(j+8)))
            self.vertex_indices.append(((i*8)+(j+1), (i*8)+1, (i*8)+(j+2), (i*8)+(j+9)))  

        #vertices = [(0,0,-2)]

        self.vertex_indices.append((113,105,106))
        self.vertex_indices.append((113,106,107))
        self.vertex_indices.append((113,106,108))
        self.vertex_indices.append((113,107,109))
        self.vertex_indices.append((113,108,110))
        self.vertex_indices.append((113,109,111))
        self.vertex_indices.append((113,110,112))
        self.vertex_indices.append((113,112,110))
        
        '''self.vertex_indices.append((121,113,114))
        self.vertex_indices.append((121,114,115))
        self.vertex_indices.append((121,115,116))
        self.vertex_indices.append((121,116,117))
        self.vertex_indices.append((121,117,118))
        self.vertex_indices.append((121,118,119))
        self.vertex_indices.append((121,119,120))
        self.vertex_indices.append((121,120,113))
        '''

        #print self.vertices
        #print len(self.vertices)
        
        #print self.vertex_indices    
        #print len(self.vertex_indices)

        print "Surface normals"

        for face_no in range(0,8,1):
            v1, v2, v3 = self.vertex_indices[face_no]
            poly = [self.Point3D(self.vertices[v1][0], self.vertices[v1][1], self.vertices[v1][2]),
                    self.Point3D(self.vertices[v2][0], self.vertices[v2][1], self.vertices[v2][2]),
                    self.Point3D(self.vertices[v3][0], self.vertices[v3][1], self.vertices[v3][2])]
            self.normals.append(self.surface_normal(poly))

        for face_no in range(8,112,1):
            v1, v2, v3, v4 = self.vertex_indices[face_no]
            poly = [self.Point3D(self.vertices[v1][0], self.vertices[v1][1], self.vertices[v1][2]),
                    self.Point3D(self.vertices[v2][0], self.vertices[v2][1], self.vertices[v2][2]),
                    self.Point3D(self.vertices[v3][0], self.vertices[v3][1], self.vertices[v3][2]),
                    self.Point3D(self.vertices[v4][0], self.vertices[v4][1], self.vertices[v4][2])]
            self.normals.append(self.surface_normal(poly))

        for face_no in range(112,120,1):
            v1, v2, v3 = self.vertex_indices[face_no]
            poly = [self.Point3D(self.vertices[v1][0], self.vertices[v1][1], self.vertices[v1][2]),
                    self.Point3D(self.vertices[v2][0], self.vertices[v2][1], self.vertices[v2][2]),
                    self.Point3D(self.vertices[v3][0], self.vertices[v3][1], self.vertices[v3][2])]
            self.normals.append(self.surface_normal(poly))

        print len(self.normals)

        self.vertex_normal()
        
        print len(self.vertexNorm)
        
    def surface_normal(self, poly):
        n = [0.0, 0.0, 0.0]

        for i, v_curr in enumerate(poly):
            v_next = poly[(i+1) % len(poly)]
            n[0] += (v_curr.y - v_next.y) * (v_curr.z + v_next.z)
            n[1] += (v_curr.z - v_next.z) * (v_curr.x + v_next.x)
            n[2] += (v_curr.x - v_next.x) * (v_curr.y + v_next.y)
        print "before normal:"
        print n
        normalised = [i/sum(n) for i in n]
        print "after normal:"
        print normalised
        
        return n#ormalised

    def test_surface_normal(self):
        poly = [self.Point3D(0.0, 0.0, 0.0),
                self.Point3D(0.0, 1.0, 0.0),
                self.Point3D(1.0, 1.0, 0.0),
                self.Point3D(1.0, 0.0, 0.0)]

        assert self.surface_normal(poly) == [0.0, 0.0, 1.0]



    def vertex_normal(self):
        for i in xrange(len(self.vertices)):
            tempNorm = [0.0, 0.0, 0.0]
            numFaces = 0
            for idx, face in enumerate(self.vertex_indices):
                if i in face:
                    tempNorm[0] += self.normals[idx][0]
                    tempNorm[1] += self.normals[idx][1]
                    tempNorm[2] += self.normals[idx][2]
                    numFaces += 1
            newList = [x / numFaces for x in tempNorm]
            self.vertexNorm.append(newList)
            #print newList
  

    def render(self):
        then = pygame.time.get_ticks()
        glColor(self.color)

        vertices = self.vertices

        #self.test_surface_normal()
        
        glBegin(GL_TRIANGLES)
    
        for face_no in range(0,8,1):
            v1, v2, v3 = self.vertex_indices[face_no]
            glNormal3dv(self.vertexNorm[v1])
            glVertex(vertices[v1])
            glNormal3dv(self.vertexNorm[v2])
            glVertex(vertices[v2])
            glNormal3dv(self.vertexNorm[v3])
            glVertex(vertices[v3])

        for face_no in range(112,120,1):
            v1, v2, v3 = self.vertex_indices[face_no]
            glNormal3dv(self.vertexNorm[v1])
            glVertex(vertices[v1])
            glNormal3dv(self.vertexNorm[v2])
            glVertex(vertices[v2])
            glNormal3dv(self.vertexNorm[v3])
            glVertex(vertices[v3])
            
        glEnd()
        
        
        # Draw all main faces of the egg
        glBegin(GL_QUADS)
        
        '''for face_no in xrange(self.num_faces):
            glNormal3dv(self.normals[face_no])
        '''
        for face_no in range(8,112,1):
           # if face_no == 1:
           #     glColor((.5, .1, .1))
           # elif face_no == 4:
           #     glColor((.1, .1, .8))
           # else:
           #     glColor((.5, .5, .7))
            v1, v2, v3, v4 = self.vertex_indices[face_no]
            glNormal3dv(self.vertexNorm[v1])
            glVertex(vertices[v1])
            glNormal3dv(self.vertexNorm[v2])
            glVertex(vertices[v2])
            glNormal3dv(self.vertexNorm[v3])
            glVertex(vertices[v3])
            glNormal3dv(self.vertexNorm[v4])
            glVertex(vertices[v4])
            
        glEnd()

if __name__ == "__main__":
    run()
