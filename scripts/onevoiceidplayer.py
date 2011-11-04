#!/usr/bin/env python
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

dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')


class Controller:
    def __init__(self, app):
        self.model = Model()
        self.frame = MainFrame()
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.center_panel = None
        self.frame.SetSizer(self.sizer)
        self.frame.Layout()
        
        self.frame.Bind(wx.EVT_MENU, lambda event: self.create_center_panel(event, False), self.frame.training_rec_menu_item)
        self.frame.Bind(wx.EVT_MENU, lambda event: self.create_center_panel(event, True), self.frame.start_rec_menu_item)
        Publisher().subscribe(self.update_status, "update_status")

    def create_center_panel(self,event,test_mode):
        if not self.center_panel == None:
            self.sizer.Detach(self.center_panel) 
            
        self.model.set_test_mode(test_mode) 
        
        if test_mode == False:
             wx.CallAfter(Publisher().sendMessage, "update_status", "Read the following paragraph ")
        else:
             wx.CallAfter(Publisher().sendMessage, "update_status", "Speak in a natural way chanting the words properly ")
        
        self.center_panel = MainPanel(self.frame, test_mode)
        
        self.sizer.Insert(1,self.center_panel, 5, wx.EXPAND)

        self.center_panel.recordButton.Bind(wx.EVT_BUTTON, self.on_rec)
        self.center_panel.pauseButton.Bind(wx.EVT_BUTTON, self.on_pause)
        
        self.sizer.Layout()
        self.frame.Layout()
        
    def on_rec(self,event):   
        self.center_panel.timer.Start(1000)
        self.center_panel.toggle_record_button()
        self.model.start_record(self.on_pause)
        wx.CallAfter(Publisher().sendMessage, "update_status", "Recording ... ")
        
        
    def on_pause(self,event=None):  
        print "pause training"
        if self.model.get_test_mode():
            self.model.stop_record()
        self.center_panel.timer.Stop()
        wx.CallAfter(Publisher().sendMessage, "update_status", "Record stopped")
        self.center_panel.toggle_stop_button()


    def update_status(self, msg):
        """
        Receives data from thread and updates the status bar
        """
        t = msg.data
        
        self.frame.set_status_text(t)

class Record():
    def __init__(self, total_seconds, partial_seconds, mode_partial, stop_callback=None, save_callback=None):
        self.chunk = 1024
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
        self._stop_signal = False
        self.thread_logger = threading.Thread(target=self._rec)
        self.thread_logger.start()
        
    def _rec(self):
        print "Record"
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
    
               current = i*self.chunk / self.rate
    
    
               if self.mode == True and (current%self.partial_seconds) == 0:
                   self.thread_rec = threading.Thread(target=self.save_wave, args =(all,str(current)))
                   self.thread_rec.start()
                   
               if not self.mode  and self.record_seconds != None :
                   if  current >= self.record_seconds:
                       self.thread_rec = threading.Thread(target=self.save_wave, args =(all,self.wave_output_filename))
                       self.thread_rec.start()
                       self.stop()
               i += 1
           except IOError:
                print "warning: dropped frame"
               
         
           #self.stop()
    def get_thread_status(self):  
          
        return not self._stop_signal 
    
    def stop(self):
        print "stop"
        if self.stop_callback != None:
            self.stop_callback()
        self._stop_signal = True
        time.sleep(1)
        self.stream.close()
        self.p.terminate()
    
    def save_wave(self, all, name):
        # write data to WAVE file
        
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
        #TODO: set status text
        self.sb.SetStatusText(text)

    
        
class MainPanel(wx.Panel):
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
        self.time = self.time+1
        secsPlayed = time.strftime('     %S', time.gmtime(self.time))
        self.trackCounter.SetLabel(secsPlayed)
      
    def toggle_record_button(self):
        self.pauseButton.Enable()
        self.recordButton.Disable()    
         
        
    def toggle_stop_button(self): 
        self.time = 0
        self.trackCounter.SetLabel("     00")
        self.pauseButton.Disable()
        self.recordButton.Enable()
        
    def add_speaker(speaker, score):
        try:
            self.textList.Append(speaker + " - " + str(score))    
        except IOError:
            print "MainPanel is not in testing mode"
            
class Model:
    def __init__(self):
        self.voiceid = None
        self.db = GMMVoiceDB('/home/michela/SpeakerRecognition/voiceid/scripts/test_db')
        self._clusters = None
        self._max_record_time = 6
        self._partial_record_time = 5
        self.test_mode = None
       
    def get_max_record_time(self):
        return self._max_record_time

    def start_record(self, stop_callback=None, temp=None):
        if self.test_mode: #self.frame.set_status_text("Stop recording")
            self.record = Record(None, self._partial_record_time,True)
        else:
            print temp
            print callback
            self.record = Record(self._max_record_time, 0, False, stop_callback, self.save_callback)
        self.record.start()
        
    
    def save_callback(self, file=None):
        print file
        
    def set_test_mode(self, mode):
        self.test_mode = mode  
        
    def get_test_mode(self):
        return self.test_mode
    
    def stop_record(self):
        self.record.stop()
    
    def load_wave(self, wave_path):        
        self.voiceid = Voiceid(self.db, wave_path, single = True)
        
    def extract_speakers(self):
        self.voiceid.extract_speakers(False, False, 4)
        self._clusters = self.voiceid.get_clusters()

    def get_status(self):
        return self.voiceid.get_status()
    
    def get_working_status(self):
        return self.voiceid.get_working_status()
    
    def get_best_five(self):
        return self.voiceid.get_cluster('S0').get_best_five()
    
    def get_clusters(self):
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