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

dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')

class LoggerPanel(wx.Panel):
    def __init__(self,parent,id):
        wx.Panel.__init__(self,parent,id,style=wx.SIMPLE_BORDER )
        self.SetBackgroundColour("#fff")
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.textBox = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.textBox.SetEditable(False)
        self.sizer.Add(self.textBox,1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(self.sizer) 
 
    def get_text_box(self):
        return self.textBox
 
class Frame(wx.Frame):
    #----------------------------------------------------------------------
    def __init__(self, parent, id, title, mplayer):
        wx.Frame.__init__(self, parent, id, title,size=(800,600) )
        self.panel = wx.Panel(self, 1)
        
        sp = wx.StandardPaths.Get()
        self.currentFolder = sp.GetDocumentsDir()
        self.currentVolume = 50
 
        self.create_menu()
 
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
        
        btnData = [{'bitmap':'play.png',
                    'handler':self.on_pause, 'name':'pause'},
                   {'bitmap':'stop.png',
                    'handler':self.on_stop, 'name':'stop'},
                   {'bitmap':'backward.png',
                    'handler':self.on_prev, 'name':'prev'},
                    {'bitmap':'forward.png',
                    'handler':self.on_next, 'name':'next'} 
                    ]
        for btn in btnData:
            self.build_btn(btn, controlSizer)
 
        return controlSizer
 
 
    #----------------------------------------------------------------------
    def build_training_controls(self):
        """
        Builds the player bar controls
        """
        panelTrain = wx.Panel(self.panel, style=wx.BORDER_SUNKEN)
        fieldsetText = wx.StaticText(panelTrain,0, ' Train space')
        
        #sizer 
        sizer = wx.BoxSizer(wx.VERTICAL)
        buttonsizer =wx.BoxSizer(wx.HORIZONTAL)
        speakersizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #buttons
        button1 = wx.Button(panelTrain, label='Listen')
        buttonsizer.Add(button1, 1, wx.ALL|wx.CENTER, 5)

        button2 = wx.Button(panelTrain, label="Rename")
        buttonsizer.Add(button2, 1, wx.ALL|wx.CENTER, 5)
        
        
        button3 = wx.Button(panelTrain,label="Skip")
        buttonsizer.Add(button3, 1, wx.ALL|wx.CENTER, 5)
        
        button4 = wx.BitmapButton(panelTrain, 0, wx.Bitmap('bitmaps/prev.png'))
        button5 = wx.BitmapButton(panelTrain, 0, wx.Bitmap('bitmaps/next.png'))

        #speaker name
        speaker = wx.StaticText(panelTrain, 1, 'Speaker Name')
        font3 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.BOLD)
        speaker.SetFont(font3)

        #build speaker name sizer
        speakersizer.Add(button4,0, wx.ALL|wx.CENTER, 5)
        speakersizer.Add(speaker,1, wx.ALL|wx.CENTER, 5)
        speakersizer.Add(button5,0, wx.ALL|wx.CENTER, 5)
        
        #build panel train
        sizer.Add(speakersizer,1, wx.ALL|wx.CENTER, 5)
        sizer.Add(buttonsizer,1, wx.ALL|wx.CENTER, 5)
        panelTrain.SetSizer(sizer)
        panelTrain.SetBackgroundColour("#fff")
        
        return panelTrain
 
 
    #----------------------------------------------------------------------
    def create_logger_panel(self):
        loggerPanel = LoggerPanel(self, -1, style=wx.SIMPLE_BORDER )
#        loggerPanel.SetBackgroundColour("#fff")
#        vbox1 = wx.BoxSizer(wx.VERTICAL)
#        #vbox1.Add(loggerPanel, 1, wx.EXPAND | wx.ALL, 3)
#        #vbox1.Add(wx.TextCtrl(loggerPanel, 1),0, wx.ALL|wx.EXPAND, 5)
#        #midPan = wx.Panel(loggerPanel)
#        #midPan.SetBackgroundColour('#ededed')
#        #vbox1.Add(midPan, 1, wx.EXPAND | wx.ALL, 5)
#        textBox = wx.TextCtrl(loggerPanel, style=wx.TE_MULTILINE)
#        textBox.SetEditable(False)
#        vbox1.Add(textBox,1, wx.ALL|wx.EXPAND, 5)
#        
#        loggerPanel.SetSizer(vbox1)
        return loggerPanel
    #----------------------------------------------------------------------
    def create_menu(self):
        """
        Creates a menu
        """
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        srMenu = wx.Menu()
        add_file_menu_item = fileMenu.Append(wx.NewId(), "&New video", "Add Media File")
        #add_file_menu_item = fileMenu.Append(wx.NewId(), "&", "Add Media File")
        run_menu_item = srMenu.Append(wx.NewId(), "&Run ")
        train_menu_item = srMenu.Append(wx.NewId(), "&Train ")
        menubar.Append(fileMenu, '&File')
        menubar.Append(srMenu, '&Speaker Recognition')
 
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_add_file, add_file_menu_item)
        self.Bind(wx.EVT_MENU, self.on_run, run_menu_item)
        self.Bind(wx.EVT_MENU, self.on_train, train_menu_item)
 
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
 
    #----------------------------------------------------------------------
    def on_run(self, event):
        """
        Run Speaker Recognition
        """
        self.panelLogger = LoggerPanel(self.panel, -1)
        self.topSizer.Add(self.panelLogger, 0, wx.ALL|wx.EXPAND, 5)
        self.Show()
        self.panel.Layout()
        textBox = self.panelLogger.get_text_box()
        
        def print_logger(voiceid):
            old_status = voiceid.get_status()
            textBox.AppendText(voiceid.get_working_status())
            while voiceid.get_status()!=5:
               status = voiceid.get_status()
               try:
                   if status != old_status:
                       old_status = voiceid.get_status()
                       input = voiceid.get_working_status()
                       textBox.AppendText(input +" \n")
                   
               except StandardError:
                    sys.exit()
        
        
        v = Voiceid(GMMVoiceDB('/home/michela/.voiceid/gmm_db'),self.mpc.GetProperty('path'))
        thread.start_new_thread(print_logger, (v,))
        thread.start_new_thread(v.extract_speakers, (False, False, 2))
        
                    
                    
    #----------------------------------------------------------------------
    def on_train(self, event):
        """
        Train Speaker Recognition
        """      
        self.panelTrain = self.build_training_controls()  
        self.mainSizer.Add(self.panelTrain,  0, wx.ALL|wx.EXPAND, 5)
        self.Show()
        self.panel.Layout()
    #----------------------------------------------------------------------
    def on_media_started(self, event):
        print 'Media started!'
        t_len = self.mpc.GetTimeLength()
        print t_len
        self.playbackSlider.SetRange(0, t_len)
        self.playbackTimer.Start(100) 
    #----------------------------------------------------------------------
    def on_media_finished(self, event):
        print 'Media finished!'
        self.playbackTimer.Stop()
 
    #----------------------------------------------------------------------
    def on_pause(self, event):
        """"""
        if self.playbackTimer.IsRunning():
            print "pausing..."
            self.mpc.Pause()
            self.playbackTimer.Stop()
            #self.SetIcon(wx.Icon('pause.png',wx.BITMAP_TYPE_PNG))
        else:
            print "unpausing..."
            self.mpc.Pause()
            self.playbackTimer.Start()
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
    def on_stop(self, event):
        """"""
        print "stopping..."
        self.mpc.Stop()
        self.playbackTimer.Stop()
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
        
    #----------------------------------------------------------------------
    
    def on_prev_speaker(self, event):
        """"""
        print "backwarding speaker..."
        
    #----------------------------------------------------------------------
    
    def on_next_speaker(self, event):
        """"""
        print "forwarding speaker ..."
        
    #----------------------------------------------------------------------
    
    def on_listen_speaker(self, event):
        """"""
        print "forwarding speaker ..."
        
    #----------------------------------------------------------------------
    
    def on_skip_speaker(self, event):
        """"""
        print "forwarding speaker ..."
        
    #----------------------------------------------------------------------
    
    def on_rename_speaker(self, event):
        """"""
        print "forwarding speaker ..."
        
    #----------------------------------------------------------------------
    
    
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