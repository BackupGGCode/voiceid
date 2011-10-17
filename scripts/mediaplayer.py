#!/usr/bin/env python
from multiprocessing import Process, cpu_count, active_children
from pyinotify import Color
from voiceid import *
import MplayerCtrl as mpc
import os
import time
import wx
import wx.lib.buttons as buttons
import thread
import threading
import sched


dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')
    

class MainFrame(wx.Frame):
    #----------------------------------------------------------------------
    def __init__(self, parent, title, mplayer):
        wx.Frame.__init__(self, parent, title=title, size=(800,600) )
       
        # init panels
        self.panel = wx.Panel(self, 1)
        self.panelLogger = None
        self.panelTrain  = None
        sp = wx.StandardPaths.Get()
        self.currentFolder = sp.GetDocumentsDir()
        self.scheduler = None
        self.trainer = None 
        # init menu
        self.create_menu()
 
        # create sizers
        self.mainSizer = wx.BoxSizer(wx.VERTICAL) 
        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)
        controlSizer = self.build_player_controls()
        sliderSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # init player objects
        self.mpc = mpc.MplayerCtrl(self.panel, 0, u'mplayer')
        self.playbackSlider = wx.Slider(self.panel, size=wx.DefaultSize)
        sliderSizer.Add(self.playbackSlider, 1, wx.ALL|wx.EXPAND, 5)
 
        # create track counter
        self.trackCounter = wx.StaticText(self.panel, label="00:00")
        sliderSizer.Add(self.trackCounter, 0, wx.ALL|wx.CENTER, 5)
 
        # set up playback timer
        self.playbackTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_playback)
        
        # add components to sizers
        self.topSizer.Add(self.mpc, 1, wx.EXPAND| wx.ALL, 5)
        self.mainSizer.Add(self.topSizer, 1,wx.ALL|wx.EXPAND, 5)
        self.mainSizer.Add(sliderSizer, 0, wx.ALL|wx.EXPAND, 5)
        self.mainSizer.Add(controlSizer, 0, wx.ALL|wx.CENTER, 5)
       
        self.panel.SetSizer(self.mainSizer)
        self.panel.SetBackgroundColour("#000")
 
        # bind buttons to function control
        self.panel.Bind(mpc.EVT_MEDIA_STARTED, self.on_media_started)
        self.panel.Bind(mpc.EVT_MEDIA_FINISHED, self.on_media_finished)
        self.panel.Bind(mpc.EVT_PROCESS_STARTED, self.on_process_started)
        self.panel.Bind(mpc.EVT_PROCESS_STOPPED, self.on_process_stopped)
        
 
        self.Show()
        self.panel.Layout()
 
        self.clusters = None
 
    #----------------------------------------------------------------------
    def build_btn(self, btnDict, sizer):
        """"""
        bmp = btnDict['bitmap']
        handler = btnDict['handler']
 
        img = wx.Bitmap(os.path.join(bitmapDir, bmp))
        btn = buttons.GenBitmapButton(self.panel, bitmap=img,
                                      name=btnDict['name'])
        btn.SetInitialSize()
        btn.Bind(wx.EVT_BUTTON, handler)
        sizer.Add(btn, 0, wx.LEFT, 3)
 
    #----------------------------------------------------------------------
    def build_player_controls(self):
        """
        Builds the player bar controls
        """
        controlSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btnData = [{'bitmap':'pause.png',
                    'handler':self.on_pause, 'name':'pause'},
                   {'bitmap':'play.png',
                    'handler':self.on_play, 'name':'play'},
                   {'bitmap':'backward.png',
                    'handler':self.on_prev, 'name':'prev'},
                    {'bitmap':'forward.png',
                    'handler':self.on_next, 'name':'next'} 
                    ]
        for btn in btnData:
            self.build_btn(btn, controlSizer)
 
        return controlSizer
 
    #----------------------------------------------------------------------
    def create_menu(self):
        """
        Creates a menu
        """
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        srMenu = wx.Menu()
        add_file_menu_item = fileMenu.Append(wx.NewId(), "&New video", "Add Media File")
        self.run_menu_item = srMenu.Append(wx.NewId(), "&Run ")
        self.train_menu_item = srMenu.Append(wx.NewId(), "&Train ")
        self.train_menu_item.Enable(False)
        menubar.Append(fileMenu, '&File')
        menubar.Append(srMenu, '&Speaker Recognition')
 
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_add_file, add_file_menu_item)
        self.Bind(wx.EVT_MENU, self.on_run, self.run_menu_item)
        self.Bind(wx.EVT_MENU, self.on_train, self.train_menu_item)
 
    #----------------------------------------------------------------------
    
    def create_training_panel(self):
        
        """Return a custom Panel to train speakers"""
        
        self.panelTrain  = wx.Panel(self, -1,style=wx.BORDER_SUNKEN )
        
        fieldsetText = wx.StaticText(self.panelTrain,0, ' Train space')
        #sizer 
        sizer = wx.BoxSizer(wx.VERTICAL)
        buttonsizer =wx.BoxSizer(wx.HORIZONTAL)
        speakersizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #buttons
        self.panelTrain.listen = wx.Button(self.panelTrain, label='Listen')
        buttonsizer.Add(self.panelTrain.listen, 1, wx.ALL|wx.CENTER, 5)

        self.panelTrain.rename = wx.Button(self.panelTrain, label="Rename")
        buttonsizer.Add(self.panelTrain.rename, 1, wx.ALL|wx.CENTER, 5)
        
        
        self.panelTrain.skip = wx.Button(self.panelTrain,label="Skip")
        buttonsizer.Add(self.panelTrain.skip, 1, wx.ALL|wx.CENTER, 5)
        
        self.panelTrain.prev = wx.BitmapButton(self.panelTrain, 0, wx.Bitmap(os.path.join(bitmapDir, 'prev.png')))
        self.panelTrain.next = wx.BitmapButton(self.panelTrain, 0, wx.Bitmap(os.path.join(bitmapDir, 'next.png')))

        #speaker name
        self.panelTrain.speaker = wx.StaticText(self.panelTrain, 1, 'Speaker Name')
        font3 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.BOLD)
        self.panelTrain.speaker.SetFont(font3)

        #build speaker name sizer
        speakersizer.Add(self.panelTrain.prev,0, wx.ALL|wx.CENTER, 5)
        speakersizer.Add(self.panelTrain.speaker,1, wx.ALL|wx.CENTER, 5)
        speakersizer.Add(self.panelTrain.next,0, wx.ALL|wx.CENTER, 5)
        
        #build panel train
        sizer.Add(speakersizer,1, wx.ALL|wx.CENTER, 5)
        sizer.Add(buttonsizer,1, wx.ALL|wx.CENTER, 5)
        self.panelTrain.SetSizer(sizer)
        self.panelTrain.SetBackgroundColour("#fff")
        
        self.panelTrain.next.Bind(wx.EVT_BUTTON,self.on_next_speaker)
        self.panelTrain.prev.Bind(wx.EVT_BUTTON,self.on_prev_speaker)  
        
    def create_logger_panel(self):
        self.panelLogger  = wx.Panel(self, -1,style=wx.SIMPLE_BORDER )
        self.panelLogger.SetBackgroundColour("#fff")
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panelLogger.textBox = wx.TextCtrl(self.panelLogger, style=wx.TE_CENTRE|wx.TE_MULTILINE,size=(150,400) )
        self.panelLogger.textBox.SetEditable(False)
        sizer.Add(self.panelLogger.textBox,1, wx.ALL|wx.EXPAND, 5)
        self.panelLogger.SetSizer(sizer) 
    
    def on_add_file(self, event):
        """
        Add a Movie and start playing it
        """
        wildcard = "Media Files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=self.currentFolder,
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.currentFolder = os.path.dirname(path[0])
            trackPath = '"%s"' % path.replace("\\", "/")
            self.mpc.Loadfile(trackPath)
        self.run_menu_item.Enable(True)    
    #----------------------------------------------------------------------
    def on_run(self, event):
        """
        Run Speaker Recognition
        """
        self.run_menu_item.Enable(False)
        if not self.panelLogger:
            self.create_logger_panel()
            self.topSizer.Add(self.panelLogger, 0, wx.ALL|wx.EXPAND, 5)
            self.Show()
            self.panel.Layout()
            self.panelLogger.textBox.AppendText("\n*Start process*\n\n")
        else:
            self.panelLogger.textBox.Clear()
            
        def print_logger(voiceid):
            old_status = voiceid.get_status()
            self.panelLogger.textBox.AppendText("-- "+voiceid.get_working_status() +" --\n")
            while voiceid.get_status()!=5:
               status = voiceid.get_status()
               try:
                   if status != old_status:
                       old_status = voiceid.get_status()
                       input = voiceid.get_working_status()
                       self.panelLogger.textBox.AppendText("-- "+input +" --\n")
                   
               except StandardError:
                    sys.exit()
            self.panelLogger.textBox.AppendText("\n*End process*\n")
            self.train_menu_item.Enable(True)
        self.voiceid = Voiceid(GMMVoiceDB('/home/michela/SpeakerRecognition/voiceid/scripts/smalldb'),self.mpc.GetProperty('path'))
        
        thread = threading.Thread(target=print_logger,args=(self.voiceid,))
        thread.start()
        thread2 = threading.Thread(target=self.voiceid.extract_speakers, args=(False, False, 2))
        thread2.start()
                    
    #----------------------------------------------------------------------
    def on_train(self, event):
        """
        Train Speaker Recognition
        """      
        
        
        self.train_menu_item.Enable(False)
        
        
        if not self.panelTrain:
            self.create_training_panel() 
            self.mainSizer.Add(self.panelTrain,  0, wx.ALL|wx.EXPAND, 5)
            self.Show()
            self.panel.Layout()
        
        clusters = self.voiceid.get_clusters()
        self.trainer = Trainer(clusters,self.mpc)
        self.trainer.play_cluster()
    #----------------------------------------------------------------------
    def on_media_started(self, event):
        print 'Media started!'
        t_len = self.mpc.GetTimeLength()
        self.mpc.SetProperty("loop",0)
        self.playbackSlider.SetRange(0, t_len)
        self.playbackTimer.Start(100) 
    #----------------------------------------------------------------------
    def on_media_finished(self, event):
        print 'Media finished!'
        self.playbackTimer.Start()
 
    #----------------------------------------------------------------------
    def on_pause(self, event):
        """"""
        if self.playbackTimer.IsRunning():
            print "pausing..."
            self.mpc.Pause()
            self.playbackTimer.Stop()
 
    #----------------------------------------------------------------------
    def on_process_started(self, event):
        print 'Process started!'
 
    #----------------------------------------------------------------------
    def on_process_stopped(self, event):
        print 'Process stopped!'
 
    #----------------------------------------------------------------------
    def on_set_volume(self, event):
        """
        Sets the volume of the music player
        """
        self.currentVolume = self.volumeCtrl.GetValue()
        self.mpc.SetProperty("volume", self.currentVolume)
 
    #----------------------------------------------------------------------
    def on_play(self, event):
        """"""
        print "playing..."
        self.mpc.Pause()
        self.playbackTimer.Start()
    #----------------------------------------------------------------------
    def on_next(self, event):
        """"""
        print "forwarding..."
        self.mpc.Seek(5)
       
    #----------------------------------------------------------------------
    def on_prev(self, event):
        """"""
        print "backwarding..."
        self.mpc.Seek(-5)
        
    def on_prev_speaker(self, event):
        """"""
        print "backwarding speaker..."
        self.trainer.play_prev_cluster()
        
    #----------------------------------------------------------------------
    
    def on_next_speaker(self, event):
        """"""
        print "forwarding speaker ..."
        self.trainer.play_next_cluster()
    #----------------------------------------------------------------------
    
    def on_listen_speaker(self, event):
        """"""
        print "listen speaker ..."
        
    #----------------------------------------------------------------------
    
    def on_skip_speaker(self, event):
        """"""
        print "skip speaker ..."
        
    #----------------------------------------------------------------------
    
    def on_rename_speaker(self, event):
        """"""
        print "rename speaker ..."
        #current_cluster = self.trainer.get_current_cluster()
        #current_cluster.set_speaker()
        
    def pause(self):
        if self.playbackTimer.IsRunning():
            self.mpc.Pause()
            self.playbackTimer.Stop()
            print "pause playing"    
            
    def start(self):
        if not self.playbackTimer.IsRunning():
            print "start playing"
            self.mpc.Pause()
            self.playbackTimer.Start()  
    
    def play_seek(self,seconds):
        print float(seconds)/100
        self.mpc.Seek(float(seconds)/100,2)
            
    def on_update_playback(self, event):
        """
        Updates playback slider and track counter
        """
        try:
            offset = self.mpc.GetTimePos()
        except:
            return
        mod_off = str(offset)[-1]
        if mod_off == '0':
            offset = int(offset)
            self.playbackSlider.SetValue(offset)
            secsPlayed = time.strftime('%M:%S', time.gmtime(offset))
            
            self.trackCounter.SetLabel(secsPlayed)
            self.trackCounter.SetForegroundColour("WHITE")
            
class Trainer:
    def __init__(self,clusters,mediaplayer):
        self._clusters = clusters
        self._scheduler = Scheduler()
        self._keys = self._clusters.keys()
        self._current_index_cluster = 0
        self._mediaplayer = mediaplayer
        self._current_cluster = self.get_current_cluster()
        
    def get_current_cluster(self):
        return self._clusters[self._keys[self._current_index_cluster]]
    
    
    def set_current_cluster(self,cluster):
        self._current_cluster = cluster
        
    def play_prev_cluster(self):
        if self._current_index_cluster > 0:
             self._current_index_cluster =-1
        c = self._keys[self._current_index_cluster] 
        set_current_cluster(c)    
        self.play_cluster(c)
    
    def play_next_cluster(self):
        if self._current_index_cluster < len(self._clusters):
             self._current_index_cluster =+1
        c = self._keys[self._current_index_cluster]
        set_current_cluster(c)
        self.play_cluster(c)    
    
    def get_segments(self,cluster):
        return cluster._segments
        
    def play_seek(self,seconds):
        print float(seconds)/100
        self._mediaplayer.Seek(float(seconds)/100,2)   
        
    def play_cluster(self,cluster=None):
        delay = 0
        self._scheduler.StopAllTasks()
        segments = []
        
        if not cluster:
            segments = self.get_current_cluster()._segments
        else:
            segments = cluster._segments
            
        for segment in range(len(segments)):
            s = segments[segment]
            duration = s.get_duration()
            if not segment == 0:
                delay = delay + (segments[segment-1].get_duration()/100)
            self._scheduler.AddTask(delay, 1, self.play_seek, (s.get_start(),))
            
        last_segment = segments[-1]    
        #self._scheduler.AddTask(delay + float(last_segment.get_duration())/100, 1, self._mediaplayer.pause, ())   
        thread = threading.Thread(target=self._scheduler.StartAllTasks)  
        thread.start()      
        #self._mediaplayer.start()
        
class Scheduler:
    def __init__( self ):
        self._tasks = []
        self._scheduler = sched.scheduler(time.time, time.sleep)
    def __repr__( self ):
        rep = ''
        for task in self._tasks:
            rep += '%s\n' % `task`
        return rep
        
    def AddTask( self, delay, priority, action, argument ):
        task = self._scheduler.enter(delay, priority, action, argument)
        print 'add task'
        self._tasks.append( task )
    
    def StartAllTasks( self ):
        print 'scheduler run'
        self._scheduler.run()
    
    def StopAllTasks( self ):
        map(self._scheduler.cancel, self._scheduler.queue)
        print 'Stopped'  
                 
if __name__ == "__main__":
    import os, sys
   
    app = wx.App(redirect=False)
    frame = MainFrame(None, 'VOICEID',  u'mplayer')
    app.MainLoop()