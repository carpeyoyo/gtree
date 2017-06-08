#!/usr/bin/python3

'''
Joshua Mazur
April 27, 2017
GUI Interface for viewing a git repository's commit and branch graph
Licensed under the GNU General Public License v3.0, see included license file.
'''

import gi
gi.require_version("Gtk","3.0")
from gi.repository import Gtk,Gdk
import cairo
import os
import pygit2
import sys
from graphviz import Digraph
import math
import time

def rgb_from_string(color_string):
    # Creates tuple with colors between 0 and 1
    # Pre: The color string as #xxxxxx where x is a hexademical number
    # Post: Returns (red,green,blue) tuple with each element a number between 0 and 1
    red = (float(int(color_string[1],16) * 16) + float(int(color_string[2],16))) / 255.0
    green = (float(int(color_string[3],16) * 16) + float(int(color_string[4],16))) / 255.0
    blue = (float(int(color_string[5],16) * 16) + float(int(color_string[6],16))) / 255.0
    return (red,green,blue)

class CustomCheckButton(Gtk.CheckButton):
    def __init__(self,button_label):
        Gtk.CheckButton.__init__(self,label=button_label)
        self.button_label = button_label

class Graph: # Graph Properties
    def __init__(self):
        self.scale = 1.0
        self.width = 1.0
        self.height = 1.0
        
class Node: # Node Properties
    def __init__(self):
        self.name = None
        self.x = 1.0
        self.y = 1.0
        self.width = 1.0
        self.height = 1.0
        self.label = None
        self.style = None
        self.shape = None
        self.red = 1.0
        self.green = 1.0
        self.blue = 1.0
        self.fillcolor = None

class Edge: # Edge Properties
    def __init__(self):
        self.tail = ""
        self.head = ""
        self.path_list = []
        self.style = None
        self.red = 1.0
        self.green = 1.0
        self.blue = 1.0
        
class App:
    def __init__(self,builder,repository):
        self.window = builder.get_object("main_window")

        # Draw Area Initial Size Request
        self.draw_frame = builder.get_object("drawing_area_frame")
        self.width = 500;
        self.height = 500;
        self.draw_frame.set_size_request(self.width+4,self.height+4)
        self.draw_frame.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        # Draw Area
        self.draw_area = builder.get_object("drawing_area")
        self.draw_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        # Button Box
        self.button_box = builder.get_object("button_box")

        # Reload button
        self.reload_button = builder.get_object("reload_button")
        
        # Message Textview Initial Size Request
        self.message_textview_frame = builder.get_object("message_textview_frame")
        self.message_textview_frame.set_size_request(500,100)

        # Message Textview
        self.message_textview = builder.get_object("message_textview")
        self.message_textview_buffer = self.message_textview.get_buffer()

        # Reload Textview
        self.reload_textview = builder.get_object("reload_textview")
        self.reload_textview_buffer = self.reload_textview.get_buffer()

        # Repository
        self.repo = repository
        
        # Setup Branches and Checkbuttons
        self.branches_checkbuttons = []
        self.branches = self.repo.listall_branches()
        self.SetupBranchesCheckButtons()
        self.graph = None
        self.node_list = []
        self.edge_list = []
        self.current = ""
        self.visited = {}

    def CreateGraph(self):
        # Creates graph to be drawn
        # Pre: Uses the contents of self.branches_checkbuttons to decide what to display
        # Post: Creates structures the drawarea draw function can use to display graph
        branches_to_check = []
        for button in self.branches_checkbuttons:
            if button.get_active():
                branches_to_check.append(button.button_label)
        if len(branches_to_check) > 0:
            # Creating graph
            self.visited = {}
            dot = Digraph(comment="git-tree graph")
            dot.node_attr.update(shape="circle")
            dot.edge_attr.update(arrowhead="none")
            dot.graph_attr.update(rankdir="LR",splines="ortho")
            current_branch = self.repo.lookup_reference('HEAD').resolve().shorthand
            for branch_name in branches_to_check:
                target = self.repo.lookup_branch(branch_name).target
                if (branch_name == "master"):
                    edge_color = "#00FF00"
                elif (branch_name == current_branch):
                    edge_color = "#0000FF"
                else:
                    edge_color = "#000000"
                parent = None
                walk = self.repo.walk(target,pygit2.GIT_SORT_TIME)
                for commit in walk:
                    oid_string = str(commit.oid)
                    if oid_string not in self.visited:
                        self.visited[oid_string] = commit
                        dot.node(oid_string,label="",color="#000000")
                    if parent != None:
                        dot.edge(oid_string,parent,color=edge_color)
                    parent = oid_string
            # Retrieving graph data
            graph_size = str(self.width - 4) + "," + str(self.height - 4) + "!"
            dot.graph_attr.update(size=graph_size)
            ratio_string = str((self.height/self.width))
            dot.graph_attr.update(ratio=ratio_string)
            dot.format = "plain-ext"
            contents = dot.pipe()
            contents_string = contents.decode("utf-8")
            # Parsing graph data
            data = contents_string.split()
            i = 0
            success = False
            self.graph = None
            self.edge_list = []
            self.node_list = []
            while (i < len(data)):
                if data[i] == "graph":
                    i += 1
                    self.graph = Graph()
                    self.graph.scale = float(data[i])
                    i += 1
                    self.graph.width = float(data[i])
                    i += 1
                    self.graph.height = float(data[i])
                    i += 1
                elif data[i] == "node":
                    i += 1
                    node = Node()
                    node.name = data[i]
                    if (node.name[0] == "\""): # Removing troublesome extra quotes from graphviz output
                        node.name = node.name[1:(len(node.name)-1)]
                    i += 1
                    node.x = float(data[i])
                    i += 1
                    node.y = float(data[i])
                    i += 1
                    node.width = float(data[i])
                    i += 1
                    node.height = float(data[i])
                    i += 1
                    node.label = data[i]
                    i += 1
                    node.style = data[i]
                    i += 1
                    node.shape = data[i]
                    i += 1
                    if (len(data[i]) == 7):
                        (node.red,node.green,node.blue) = rgb_from_string(data[i])
                    i += 1
                    node.fillcolor = data[i]
                    i += 1
                    self.node_list.append(node)
                elif data[i] == "edge":
                    i += 1
                    edge = Edge()
                    edge.tail = data[i]
                    i += 1
                    edge.head = data[i]
                    i += 1
                    n = int(data[i])
                    i += 1
                    for j in range(0,n,1):
                        x = float(data[i])
                        i += 1
                        y = float(data[i])
                        i += 1
                        edge.path_list.append((x,y))
                    edge.style = data[i]
                    i += 1
                    if (len(data[i]) == 7):
                        (edge.red,edge.green,edge.blue) = rgb_from_string(data[i])
                    i += 1
                    self.edge_list.append(edge)
                elif data[i] == "stop":
                    success = True
                    break
            if success == False:
                self.graph = None
                self.edge_list = []
                self.node_list = []
                self.visited = {}
            else:
                self.draw_area.queue_draw()
                reload_message = "Last Updated:\n" + time.ctime()
                self.reload_textview_buffer.set_text(reload_message)

    def SetupBranchesCheckButtons(self):
        # Sets up the CheckButton for branches
        # Pre: Uses the branches currently listed in self.branches, and removes all all buttons in
        #      self.branches_checkbuttons, and packs the buttons in self.button_box
        # Post: Buttons on GUI will corespond to branches
        for branch in self.branches:
            temp = CustomCheckButton(branch)
            temp.set_active(True)
            temp.connect("toggled",self.checkbutton_draw_objects_toggled_method)
            self.button_box.pack_start(temp,False,False,0)
            self.branches_checkbuttons.append(temp)
       
    def onDeleteWindow(self, *args):
        # Window Delete Method
        Gtk.main_quit(*args)

    def reload_button_method(self, button):
        # Reloads buttons and graph
        temp_branches = self.repo.listall_branches()

        # Checking and removing any removed branches
        for branch in self.branches:
            if branch not in temp_branches:
                i = 0;
                while (i < len(self.branches_checkbuttons)):
                    if (self.branches_checkbuttons[i].button_label == branch):
                        temp = self.branches_checkbuttons.pop(i)
                        self.button_box.remove(temp)
                        break
                    else:
                        i += 1
                self.branches.remove(branch)

        # Checking and adding any new branches
        for branch in temp_branches:
            if branch not in self.branches:
                self.branches.append(branch)
                temp = CustomCheckButton(branch)
                temp.set_active(True)
                temp.connect("toggled",self.checkbutton_draw_objects_toggled_method)
                self.button_box.pack_start(temp,False,False,0)
                temp.show()
                self.branches_checkbuttons.append(temp)
                
        # Drawing Graph
        self.CreateGraph()
        
        
    def on_drawing_area_button_press_event(self, widget, event):
        # Called when draw area is clicked.
        # Will determine if a node has been pressed and change the message textview accordingly 
        if (len(self.node_list) > 0):
            scale = self.graph.scale
            for node in self.node_list:
                x = (scale * node.x) + 2
                y = self.height - (scale * node.y) - 2
                radius = scale * node.width * 0.5
                distance = math.sqrt(math.pow((x - event.x),2) + math.pow((y - event.y),2))
                if (distance <= radius):
                    self.current = node.name
                    self.draw_area.queue_draw()
                    message = "commit " + str(self.current) + "\n"
                    if self.current in self.visited:
                        commit = self.visited[self.current]
                        message += "Author: " + commit.committer.name + " <" + commit.committer.email + ">"  + "\n"
                        message += "Date: " + time.ctime(commit.committer.time) + "\n"
                        message += "\n\t" + commit.message
                    else:
                        message += "Current Key not in Visited Dictionary"
                    self.message_textview_buffer.set_text(message)
                    break
                
    def drawing_area_size_allocate_method(self, widget, rectangle):
        # Draw area size allocation method
        # Retrieves width, height information when drawingarea is resized and calls for graph to be created.
        self.width = widget.get_allocated_width()
        self.height = widget.get_allocated_height()
        self.CreateGraph()
        
    def drawing_area_draw_method(self, widget, cr):
        # Draw area Draw Method
        # Draws graph described by self.graph = None, self.edge_list = [], and self.node_list = []
        # Will also highlight node that shares its name with self.current, and 

        # Backgroud
        cr.set_source_rgb(1,1,1)
        cr.rectangle(0,0,self.width,self.height)
        cr.fill()

        if (self.graph != None):
            scale = self.graph.scale
            for edge in self.edge_list:
                cr.set_source_rgb(edge.red,edge.green,edge.blue)
                if (len(edge.path_list) > 0):
                    (x,y) = edge.path_list[0]
                    x = (x * scale) + 2 
                    y = self.height - (y * scale) - 2
                    cr.move_to(x,y)
                    for i in range(1,len(edge.path_list),1):
                        (x,y) = edge.path_list[i]
                        x = (x * scale) + 2
                        y = self.height - (y * scale) - 2
                        cr.line_to(x,y)
                    cr.stroke()

            highlight = False
            for node in self.node_list:
                x = (scale * node.x) + 2
                y = self.height - (scale * node.y) - 2
                radius = scale * node.width * 0.5
                # Select Fill
                if (self.current == node.name):
                    cr.set_source_rgb(1.0,1.0,0.0)
                    cr.arc(x,y,radius,0,(math.pi * 2.0))
                    cr.fill()
                    highlight = True
                # Outline stroke
                cr.set_source_rgb(node.red,node.green,node.blue)
                cr.arc(x,y,radius,0,(math.pi * 2.0))
                cr.stroke()
            # Removes Node info if no node was highlighted this time
            if self.current != "" and highlight == False:  
                self.message_textview_buffer.set_text("")
                self.current = ""
                
    def checkbutton_draw_objects_toggled_method(self,data):
        # Called when branch checkbutton is toggled
        # Calls for graph to be created each time
        self.CreateGraph()
                
def main():
    # Will not display window if no git repository exists in working directories
    if os.path.exists("./.git") == False:
        sys.stderr.write("No git repository found in this directory.\n")
        exit()
        
    repo = pygit2.Repository("./.git")
    
    builder = Gtk.Builder()

    glade_file_path = os.path.dirname(os.path.realpath(__file__)) + "/main_window.glade"    
    builder.add_from_file(glade_file_path)

    app = App(builder,repo)

    builder.connect_signals(app)
    
    app.window.show_all()

    Gtk.main()

main()
