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
dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')



class LoggerPanel(wx.Panel):
    """Return a custom Panel to print logs"""
    def __init__(self,parent,id):
        wx.Panel.__init__(self,parent,id,style=wx.SIMPLE_BORDER )
        self.SetBackgroundColour("#fff")
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.textBox = wx.TextCtrl(self, style=wx.TE_CENTRE|wx.TE_MULTILINE,size=(150,400) )
        self.textBox.SetEditable(False)
        self.sizer.Add(self.textBox,1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(self.sizer) 
 
    def get_text_box(self):
        return self.textBox
 
class TrainingPanel(wx.Panel):
    """Return a custom Panel to train speakers"""
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,style=wx.BORDER_SUNKEN)
        fieldsetText = wx.StaticText(self,0, ' Train space')
        #sizer 
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.buttonsizer =wx.BoxSizer(wx.HORIZONTAL)
        self.speakersizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #buttons
        self.listen = wx.Button(self, label='Listen')
        self.buttonsizer.Add(self.listen, 1, wx.ALL|wx.CENTER, 5)

        self.rename = wx.Button(self, label="Rename")
        self.buttonsizer.Add(self.rename, 1, wx.ALL|wx.CENTER, 5)
        
        
        self.skip = wx.Button(self,label="Skip")
        self.buttonsizer.Add(self.skip, 1, wx.ALL|wx.CENTER, 5)
        
        self.prev = wx.BitmapButton(self, 0, wx.Bitmap(os.path.join(bitmapDir, 'prev.png')))
        self.next = wx.BitmapButton(self, 0, wx.Bitmap(os.path.join(bitmapDir, 'next.png')))

        #speaker name
        self.speaker = wx.StaticText(self, 1, 'Speaker Name')
        font3 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.BOLD)
        self.speaker.SetFont(font3)

        #build speaker name sizer
        self.speakersizer.Add(self.prev,0, wx.ALL|wx.CENTER, 5)
        self.speakersizer.Add(self.speaker,1, wx.ALL|wx.CENTER, 5)
        self.speakersizer.Add(self.next,0, wx.ALL|wx.CENTER, 5)
        
        #build panel train
        self.sizer.Add(self.speakersizer,1, wx.ALL|wx.CENTER, 5)
        self.sizer.Add(self.buttonsizer,1, wx.ALL|wx.CENTER, 5)
        self.SetSizer(self.sizer)
        self.SetBackgroundColour("#fff")
        
        self.next.Bind(wx.EVT_BUTTON,parent.on_next_speaker)
        self.prev.Bind(wx.EVT_BUTTON,parent.on_prev_speaker)
        
    def set_speaker_label(self, name):
        return self.speaker.SetLabel(name)
 
        #----------------------------------------------------------------------
    
class Frame(wx.Frame):
    #----------------------------------------------------------------------
    def __init__(self, parent, id, title, mplayer):
        wx.Frame.__init__(self, parent, id, title,size=(800,600) )
       
        self.panel = wx.Panel(self, 1)
        self.panelLogger = None
        self.panelTrain = None
      
        sp = wx.StandardPaths.Get()
        self.currentFolder = sp.GetDocumentsDir()
        self.currentVolume = 50
 
        self.create_menu()
 
        self.clusters = None
        # create sizers
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)
        controlSizer = self.build_player_controls()
        sliderSizer = wx.BoxSizer(wx.HORIZONTAL)
 
        self.mpc = mpc.MplayerCtrl(self.panel, 0, u'mplayer')
        self.playbackSlider = wx.Slider(self.panel, size=wx.DefaultSize)
        sliderSizer.Add(self.playbackSlider, 1, wx.ALL|wx.EXPAND, 5)
 
        # create track counter
        self.trackCounter = wx.StaticText(self.panel, label="00:00")
        sliderSizer.Add(self.trackCounter, 0, wx.ALL|wx.CENTER, 5)
 
        # set up playback timer
        self.playbackTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_playback)
        self.topSizer.Add(self.mpc, 1, wx.EXPAND| wx.ALL, 5)
        self.mainSizer.Add(self.topSizer, 1,wx.ALL|wx.EXPAND, 5)
        self.mainSizer.Add(sliderSizer, 0, wx.ALL|wx.EXPAND, 5)
        self.mainSizer.Add(controlSizer, 0, wx.ALL|wx.CENTER, 5)
       
        self.panel.SetSizer(self.mainSizer)
        self.panel.SetBackgroundColour("#000")
 
        self.panel.Bind(mpc.EVT_MEDIA_STARTED, self.on_media_started)
        self.panel.Bind(mpc.EVT_MEDIA_FINISHED, self.on_media_finished)
        self.panel.Bind(mpc.EVT_PROCESS_STARTED, self.on_process_started)
        self.panel.Bind(mpc.EVT_PROCESS_STOPPED, self.on_process_stopped)
        
 
        self.Show()
        self.panel.Layout()
 
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
        runid = wx.NewId()
        trainid = wx.NewId()
        self.run_menu_item = srMenu.Append(runid, "&Run ")
        self.train_menu_item = srMenu.Append(trainid, "&Train ")
        self.train_menu_item.Enable(False)
        menubar.Append(fileMenu, '&File')
        menubar.Append(srMenu, '&Speaker Recognition')
 
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_add_file, add_file_menu_item)
        self.Bind(wx.EVT_MENU, self.on_run, self.run_menu_item)
        self.Bind(wx.EVT_MENU, self.on_train, self.train_menu_item)
 
    #----------------------------------------------------------------------
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
            self.panelLogger = LoggerPanel(self.panel, -1 )
            self.topSizer.Add(self.panelLogger, 0, wx.ALL|wx.EXPAND, 5)
            self.Show()
            self.panel.Layout()
            textBox = self.panelLogger.get_text_box()
            textBox.AppendText("\n*Start process*\n\n")
        else:
            textBox.Clear()
            
        def print_logger(voiceid):
            old_status = voiceid.get_status()
            textBox.AppendText("-- "+voiceid.get_working_status() +" --\n")
            while voiceid.get_status()!=5:
               status = voiceid.get_status()
               try:
                   if status != old_status:
                       old_status = voiceid.get_status()
                       input = voiceid.get_working_status()
                       textBox.AppendText("-- "+input +" --\n")
                   
               except StandardError:
                    sys.exit()
            textBox.AppendText("\n*End process*\n")
            self.train_menu_item.Enable(True)
        self.voiceid = Voiceid(GMMVoiceDB('/home/michela/SpeakerRecognition/voiceid/scripts/test_db'),self.mpc.GetProperty('path'))
        thread.start_new_thread(print_logger, (self.voiceid,))
        thread.start_new_thread(self.voiceid.extract_speakers, (False, False, 2))
        
                    
                    
    #----------------------------------------------------------------------
    def on_train(self, event):
        """
        Train Speaker Recognition
        """      
        self.train_menu_item.Enable(False)
        if not self.panelTrain:
            self.panelTrain = TrainingPanel(self) 
            self.mainSizer.Add(self.panelTrain,  0, wx.ALL|wx.EXPAND, 5)
            self.Show()
            self.panel.Layout()
        
        self.clusters = self.voiceid.get_clusters()
        self.current_index_cluster = 0
        current_cluster = self.clusters.keys()[self.current_index_cluster]
        self.panelTrain.set_speaker_label(self.clusters[current_cluster].get_speaker())
        info_cluster = self.clusters[current_cluster].to_dict()
        self.play_training(info_cluster)
        #self.mpc.Pause()
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
            #self.SetIcon(wx.Icon('pause.png',wx.BITMAP_TYPE_PNG))
            
            #self.SetIcon(wx.Icon('play.png',wx.BITMAP_TYPE_PNG))
 
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
        if self.current_index_cluster != 0:
             self.current_index_cluster = self.current_index_cluster -1
             self.on_update_training()
    #----------------------------------------------------------------------
    
    def on_next_speaker(self, event):
        """"""
        print "forwarding speaker ..."
        if self.current_index_cluster != len(self.clusters):
             self.current_index_cluster = self.current_index_cluster +1
             self.on_update_training()
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
        
    def on_update_training(self):
        current_cluster = self.clusters.keys()[self.current_index_cluster]
        self.panelTrain.set_speaker_label(self.clusters[current_cluster].get_speaker())
        info_cluster = self.clusters[current_cluster].to_dict()
        self.play_training(info_cluster)
                
    def play_training(self,info_cluster):
        def next_seg(start_time):
            #print "start_time %s" % float(start_time)/100
            print float(start_time)/100
            self.mpc.Seek(float(start_time)/100,2)
            
#        if not self.playbackTimer.IsRunning():
#            self.mpc.Pause()
#            self.playbackTimer.Start()
            
        for segment in range(len(info_cluster)):
            duration = info_cluster[segment][1]
            #print "duration %s" % float(duration)/100
            print "time start %s" %   info_cluster[segment][0]
            timer = threading.Timer(float(duration)/100, next_seg, args=(info_cluster[segment][0], )) 
            timer.start()   
#        if self.playbackTimer.IsRunning():
#            self.mpc.Pause()
#            self.playbackTimer.Stop()
        
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
       
        
                 
if __name__ == "__main__":
    import os, sys
   
    app = wx.App(redirect=False)
    frame = Frame(None, -1, 'VOICEID',  u'mplayer')
    app.MainLoop()