#!/usr/bin/env python
#########################################################################
#
# VoiceID, Copyright (C) 2011, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it, michela.fancello@crs4.it, 
#        mauro.mereu@crs4.it
# Web: http://code.google.com/p/voiceid
# Authors: Michela Fancello, Mauro Mereu
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################
#
# VoiceID is a speaker recognition/identification system written in Python,
# based on the LIUM Speaker Diarization framework.
#
# VoiceID can process video or audio files to identify in which slices of 
# time there is a person speaking (diarization); then it examines all those
# segments to identify who is speaking. To do so you must have a voice models
# database. To create the database you have to do a "train phase", in
# interactive mode, by assigning a label to the unknown speakers.
# You can also build yourself the speaker models and put those in the db
# using the scripts to create the gmm files.

from multiprocessing import Process, cpu_count, active_children
from pyinotify import Color
from voiceid import *
import MplayerCtrl as mpc
import os
import sched
import thread
import threading
import time
import wx
import wx.lib.buttons as buttons
from wx.lib.pubsub import Publisher
import pyaudio
import wave
from multiprocessing import synchronize 
from threading import Lock
from wx.lib.pubsub import Publisher

#-------------------------------------
# initializations and global variables
#-------------------------------------
dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')


class Controller:
    """A class that represents a controller between the views (CentralPanel and MainFrame) and model data management (Models) """
    
    def __init__(self, app):
        self.model = Model()
        self.model.attach(self)
        self.frame = MainFrame()
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.central_panel = None
        self.frame.SetSizer(self.sizer)
        self.frame.Layout()
        
        self.frame.Bind(wx.EVT_MENU, lambda event: self.create_central_panel(event, False), self.frame.training_rec_menu_item)
        self.frame.Bind(wx.EVT_MENU, lambda event: self.create_central_panel(event, True), self.frame.start_rec_menu_item)
        Publisher().subscribe(self.update_status, "update_status")


    def create_central_panel(self,event,test_mode):
        """ Create a central panel for displaying data """
        if not self.central_panel == None:
            self.sizer.Detach(self.central_panel) 
            
        self.model.set_test_mode(test_mode) 
        
        if test_mode == False:
             wx.CallAfter(Publisher().sendMessage, "update_status", "Read the following paragraph ")
        else:
             wx.CallAfter(Publisher().sendMessage, "update_status", "Speak in a natural way chanting the words properly ")
        
        self.central_panel = MainPanel(self.frame, test_mode)
        
        self.sizer.Insert(1,self.central_panel, 5, wx.EXPAND)

        self.central_panel.recordButton.Bind(wx.EVT_BUTTON, self.on_rec)
        self.central_panel.pauseButton.Bind(wx.EVT_BUTTON, self.on_pause)
        
        self.sizer.Layout()
        self.frame.Layout()
        
    def on_rec(self,event):  
        """ Start record process """ 
        
        self.central_panel.timer.Start(1000)
        self.central_panel.toggle_record_button()
        self.model.start_record(self.on_pause)
        wx.CallAfter(Publisher().sendMessage, "update_status", "Recording ... ")
        
        
    def on_pause(self,event=None):  
        """ Stop record process """  
        
        if self.model.get_test_mode():
            self.model.stop_record()
        self.central_panel.timer.Stop()
        wx.CallAfter(Publisher().sendMessage, "update_status", "Record stopped")
        self.central_panel.toggle_stop_button()


    def update_status(self, msg):
        """
        Receives data from thread and updates the status bar
        """
        t = msg.data
        
        self.frame.set_status_text(t)

    def update(self):
        """ Update speaker's list  """
        
        result = self.model.get_last_result()
        print "result", result
        i = 0
        self.central_panel.textList.Clear()
        for r in result:
            i+=1
            self.central_panel.textList.Append(str(i) +"  "+r[0])

class Record():
    """
    A class that represents the management and the creation of a recording
    """
    def __init__(self, total_seconds, partial_seconds, mode_partial, stop_callback=None, save_callback=None):
        self.chunk = 1600
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.partial_seconds = partial_seconds
        self.record_seconds = total_seconds
        self.wave_output_filename = "training.wav"
        self.data = None
        self.stream = None
        self.p = pyaudio.PyAudio()
        self.mode = mode_partial
        self._stop_signal = True
        self.stop_callback = stop_callback
        self.save_callback = save_callback
        
    def start(self):
        """ Start a thread to recording """
        self._stop_signal = False
        self.thread_logger = threading.Thread(target=self._rec)
        self.thread_logger.start()
        
    def _rec(self):
        print "Record"
        """ Record the incoming audio """
        self.stream = self.p.open(format = self.format,
               channels = self.channels,
               rate = self.rate,
               input = True,
               frames_per_buffer = self.chunk)
        all = []
        i=0
        while  self.get_thread_status():
           try:
               self.data = self.stream.read(self.chunk)
               all.append(self.data)
    
               current = float(i) * float(self.chunk) / float(self.rate)
               #test mode
               if self.mode == True and current>0 and ( current % self.partial_seconds ) == 0:
                   print "test mode"
                   self.thread_rec = threading.Thread(target=self.save_wave, args =(all,str(current)))
                   self.thread_rec.start()
                   
               #train mode    
               if not self.mode  and self.record_seconds != None :
                   print "train mode"
                   if  current >= self.record_seconds:
                       self.thread_rec = threading.Thread(target=self.save_wave, args =(all,self.wave_output_filename))
                       self.thread_rec.start()
                       self.stop()
               i += 1
           except IOError:
                print "warning: dropped frame"
               
         
    def get_thread_status(self):  
        """ Return true if the recording is stopped """ 
         
        return not self._stop_signal 
    
    def stop(self):
        print "stop"
        """ Stop the record"""
        
        if self.stop_callback != None:
            self.stop_callback()
        self._stop_signal = True
        time.sleep(1)
        self.stream.close()
        self.p.terminate()
    
    def save_wave(self, all, name):
        """ Write record data to WAVE file """
        
        print "save_wave ", name
        data = ''.join(all)
        file = "test_"+name+".wav"
        wf = wave.open(file, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(data)
        wf.close()
        self.save_callback(file)
    

class MainFrame(wx.Frame):
    """ Frame containing all GUI components """
    def __init__(self):
        wx.Frame.__init__(self, None, title="Voiceid", size=(500, 400))
        self._create_menu()
        self.sb = self.CreateStatusBar()
        self.Show()

    def _create_menu(self):
        """
        Creates a menu
        """
        menubar = wx.MenuBar()
        trainingMenu = wx.Menu()
        srMenu = wx.Menu()
        srSettings = wx.Menu()
        self.training_rec_menu_item = trainingMenu.Append(wx.NewId(), "&New", "New")
        self.start_rec_menu_item = srMenu.Append(wx.NewId(), "&Start", "Start")
        menubar.Append(trainingMenu, '&Training')
        menubar.Append(srMenu, '&Speaker Recognition')
        self.SetMenuBar(menubar)
        
    def set_status_text(self, text):
        """ Update the status-bar text """
        #TODO: set status text
        self.sb.SetStatusText(text)

    
        
class MainPanel(wx.Panel):
    """ A panel containing a window to write input/output info and control's buttons """
    
    def __init__(self, parent, test_mode):
        wx.Panel.__init__(self, parent, -1,size=(300, 550))
        
        self.parent = parent
        
        self.test_mode = test_mode
        
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.textRead = None
        
        self.textList = None
        
        self.staticText = None
        
        self.font = wx.Font(15, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        if not self.test_mode:
             
             
             self.staticText = wx.StaticText(self, wx.ID_ANY, label="TRAINING MODE", style=wx.ALIGN_CENTER)
             
             self.textRead = wx.TextCtrl(self, size=(250, 120))
              
             text = """La Sardegna, la seconda isola piu estesa del mar Mediterraneo dopo la Sicilia (ottava in Europa e la quarantottesima
             nel mondo) e una regione italiana a statuto speciale denominata Regione Autonoma della Sardegna.
             Lo Statuto Speciale, sancito nella Costituzione del 1948, garantisce l'autonomia amministrativa delle istituzioni
             locali a tutela delle peculiarita etno-linguistiche e geografiche.
             Nonostante l insularita attenuata solo alla vincinanza della Corsica, la posizione strategica al centro del mar
             Mediterraneo occidentale, ha favorito sin dall'antichita i rapporti commerciali e culturali, come gli interessi economici,
             militari e strategici. In epoca moderna molti viaggiatori e scrittori hanno esaltato la bellezza della Sardegna,
             immersa in un ambiente ancora incontaminato con diversi endemismi e in un paesaggio che ospita le vestigia della civilta nuragica."""
             
             
             self.textRead.AppendText(text)
             
             hbox.Add(self.textRead,5, wx.EXPAND | wx.ALL)
             hbox.Layout()
        else:
             print "list"
             self.staticText = wx.StaticText(self, wx.ID_ANY, label="TEST MODE", style=wx.ALIGN_CENTER)
             self.textList = wx.ListBox(self, size=(250, 120))
             hbox.Add(self.textList,5, wx.EXPAND | wx.ALL)
             hbox.Layout()
        
        self.staticText.SetFont(self.font)
        
        self.staticText.CenterOnParent()
        
        self.recordButton =wx.lib.buttons.GenBitmapTextButton(self,1, wx.Bitmap(os.path.join(bitmapDir, "record.png")))
        
        self.pauseButton =wx.lib.buttons.GenBitmapTextButton(self,1, wx.Bitmap(os.path.join(bitmapDir, "stopred.png")))
        
        self.pauseButton.Disable()
        
        self.timer = wx.Timer(self)
        
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        
        font = wx.Font(40, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        
        self.trackCounter = wx.StaticText(self, label="     00",style=wx.EXPAND | wx.ALL)
        
        self.trackCounter.SetFont(font)
        
        self.time = 0
        
        buttonbox.Add(self.recordButton,0, wx.CENTER)
        
        buttonbox.Add(self.pauseButton,0, wx.CENTER)
        
        buttonbox.Add(self.trackCounter,0, flag=wx.CENTER|wx.RIGHT, border=20)
        
        vbox.Add(self.staticText,1, wx.CENTER | wx.ALL, 15)
        
        vbox.Add(hbox,5, wx.EXPAND | wx.ALL, 2)
    
        vbox.Add(buttonbox,1, wx.CENTER| wx.ALL, 2)
        
        self.SetSizer(vbox)
        vbox.Layout()
        
    def OnTimer(self, event):
        """ Manage a GUI timer """
        
        self.time = self.time+1
        secsPlayed = time.strftime('     %M:%S', time.gmtime(self.time))
        self.trackCounter.SetLabel(secsPlayed)
      
    def toggle_record_button(self):
        """ Enable stop button """
        
        self.pauseButton.Enable()
        self.recordButton.Disable()    
         
        
    def toggle_stop_button(self): 
        """ Enable record button """
        
        self.time = 0
        self.trackCounter.SetLabel("     00:00")
        self.pauseButton.Disable()
        self.recordButton.Enable()
        
    def add_speaker(speaker, score):
        try:
            self.textList.Append(speaker + " - " + str(score))    
        except IOError:
            print "MainPanel is not in testing mode"
            
class Model:
    """ Represents and manages all data model """
    
    def __init__(self):
        self.voiceid = None
        self.db = GMMVoiceDB('/home/michela/SpeakerRecognition/voiceid/scripts/test_db')
        self._clusters = None
        self._max_record_time = 6
        self._partial_record_time = 5
        self.test_mode = None
        self.queue_processes = []
        self._observers = []
        self._processing_thread = None
        
    def attach(self, observer):
        """ Attach a new observer """
        
        if not observer in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        """ Deatach a new observer """
        
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, modifier=None):
        """ Notify an update """
        
        for observer in self._observers:
            if modifier != observer:
                observer.update()
                
    def get_max_record_time(self):
        """ Return max time to record in training mode """
        
        return self._max_record_time

    def save_callback(self, file=None):
        """ Adds a file to the queue after it's been saved """
        
        self.queue_processes.append((file,None))
    
    def on_process(self):
        """ Extract speakers from each partial recording file """
        
        while self.record.get_thread_status():
            index = 0
            #print self.queue_processes
            for file, result in self.queue_processes:
                if result == None:
                    self.load_wave(file)
                    self.extract_speakers()
                    self.queue_processes[index] = ( file, self.get_best_five() )
                    self.notify()
                index += 1
            time.sleep(.1)
    
    def get_last_result(self):
        """ Return last result """
        
        p = self.queue_processes[:]
        p.reverse()
        for file, result in p:
            if result != None:
                return result
        return None
        
    def start_record(self, stop_callback=None):
        """ start a new record process """
        
        if self.test_mode: #self.frame.set_status_text("Stop recording")
            self.record = Record(None, self._partial_record_time,True, None,self.save_callback)
        else:
            self.record = Record(self._max_record_time, 0, False, stop_callback,self.save_callback)
        self._processing_thread = threading.Thread(target=self.on_process)
        self._processing_thread.start()
        self.record.start()
        
    def set_test_mode(self, mode):
        """ Set mode to record - True for test mode False otherwise """
        
        self.test_mode = mode  
        
    def get_test_mode(self):
        """ Return mode to record - True for test mode False otherwise """
        
        return self.test_mode
    
    def stop_record(self):
        """ Stop record process """
        
        self.record.stop()
    
    def load_wave(self, wave_path):  
        """  """
              
        self.voiceid = Voiceid(self.db, wave_path, single = True)
        
    def extract_speakers(self):
        """ Extract speakers from a wave """
        
        self.voiceid.extract_speakers(False, False, 4)
        self._clusters = self.voiceid.get_clusters()

    def get_status(self):
        """ Return voiceid status """
        
        return self.voiceid.get_status()
    
    def get_working_status(self):
        """ Return voiceid working status """
        
        return self.voiceid.get_working_status()
    
    def get_best_five(self):
        """ Return best five speakers """
        
        return self.voiceid.get_cluster('S0').get_best_five()
    
    def get_clusters(self):
        """ Return all voiceid clusters """
        
        return self.voiceid.get_clusters()
    
class App(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        self.controller = Controller(self)
        
    def OnExit(self):
        pass
        #self.controller.exit()
       
if __name__ == "__main__":
    app = App(redirect=False)
    app.MainLoop()