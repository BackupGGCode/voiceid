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

dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')
LIST_ID = 26
PLAY_ID = 1
EDIT_ID = 0
OK_DIALOG =33
CANCEL_DIALOG =34
TRAIN_ON = 100
TRAIN_OFF = 101
class Controller:
    def __init__(self, app):
        self.model = Model()
        self.frame = MainFrame()
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.player = Player(self.frame)
        self.clusters_list = ClustersList(self.frame)
        sizer.Add(self.player, 5, wx.EXPAND)
        sizer.Add(self.clusters_list, 1, wx.EXPAND)
        self.frame.SetSizer(sizer)
        self.frame.Layout()
        self.mode = TRAIN_OFF
        sp = wx.StandardPaths.Get()
        self.currentFolder = sp.GetDocumentsDir()
        
        self.frame.Bind(wx.EVT_MENU, self.on_add_file, self.frame.add_file_menu_item)
        self.frame.Bind(wx.EVT_MENU, self.on_run, self.frame.run_menu_item)
        self.frame.Bind(wx.EVT_MENU, self.on_test, self.frame.train_menu_item) 
        
        self.player.Bind(wx.EVT_TIMER, self.on_update_playback)
        
        self.clusters_list.Bind(wx.EVT_LISTBOX, self.on_select_cluster, id=LIST_ID)
        
        self.clusters_list.Bind(wx.EVT_BUTTON, self.on_play_cluster, id=PLAY_ID)
        
        self.clusters_list.Bind(wx.EVT_BUTTON, self.on_edit_cluster, id=EDIT_ID)
        
        
        Publisher().subscribe(self.update_status, "update_status")
        Publisher().subscribe(self.update_list, "update_list")
        
        
    def on_add_file(self, event):
        """
        Add a Movie and start playing it
        """
        wildcard = "Media Files (*.*)|*.*"
        
        dlg = wx.FileDialog(
            self.frame, message="Choose a file",
            defaultDir=self.currentFolder,
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.currentFolder = os.path.dirname(path[0])
            trackPath = '"%s"' % path.replace("\\", "/")
            self.player.mpc.Loadfile(trackPath)
        self.frame.run_menu_item.Enable(True)
        
    def on_process(self):
        old_status = self.model.get_status()
        wx.CallAfter(Publisher().sendMessage, "update_status", self.model.get_working_status() + " ...")
        while self.model.get_status() < 5:
            time.sleep(2)
            status = self.model.get_status()
            try:
                if status != old_status:
                    old_status = self.model.get_status()
                    wx.CallAfter(Publisher().sendMessage, "update_status", self.model.get_working_status() + " ...")
            except StandardError:
                 print "Error in print_logger"
        self.on_finish_process()
        
    def on_finish_process(self):
        wx.CallAfter(Publisher().sendMessage, "update_status", self.model.get_working_status())
        self.frame.train_menu_item.Enable(True)
        wx.CallAfter(Publisher().sendMessage, "update_list", "Process finished")
        
        
    def get_current_cluster(self):
        
        index = self.clusters_list.list.GetSelection()
        cluster = self.clusters_list.list.GetString(index)
        name = cluster.split(' ')[0]
        
        c = self.model.get_cluster(name)
        return c
        
            
    def on_play_segment(self, event):
        if self.mode == TRAIN_ON:
            c = self.get_current_cluster()
            segments = c._segments[:]
            offset = self.player.mpc.GetTimePos()
            segments.reverse()
            n = 0
            for s in segments:
                end = float(s.get_end())/100
                print "offset = %s  end = %s " % (offset,end)
                if offset >= end :
                    print "n %s" %n
                    next = len(c._segments) - n + 1
                    if  n>1 :
                        print "successivo = %s" % next
                        start = float(c._segments[ next ].get_start())/100
                        print "play at = %s " %  start
                        self.player.mpc.Seek( start, 2 )
                        time.sleep(1)
                    else:
                        print 'pause'
                        self.toggle_pause()
                    break
                elif offset >= float(s.get_start())/100:
                    break
                n+=1
                        
                    
                    
            #self.player.
        
   #----------------------------------------------------------------------
    def update_status(self, msg):
        """
        Receives data from thread and updates the status bar
        """
        t = msg.data
        
        self.frame.set_status_text(t)
        
    def update_list(self, msg):
        """
        Receives data from thread and updates the status bar
        """
        t = msg.data
        self.frame.set_status_text(t)
        u, k = self.model.get_clusters_info()
        text = "Speakers info:\n " +  str(u) + " unknown \n "+  str(k)+" known" 
        self.clusters_list.set_info_clusters(text)
        clusters =  self.model.get_clusters()
        for c in clusters.values():
            self.clusters_list.add_cluster(c.get_name(),c.get_speaker())
            
            
    def on_update_playback(self, event):
        """
        Updates playback slider and track counter
        """
        
        try:
            offset = self.player.mpc.GetTimePos()
        except:
            return
        mod_off = str(offset)[-1]
        if mod_off == '0':
            offset = int(offset)
            self.player.playbackSlider.SetValue(offset)
            secsPlayed = time.strftime('%M:%S', time.gmtime(offset))
            self.player.trackCounter.SetLabel(secsPlayed)
        if self.mode == TRAIN_ON:
            self.on_play_segment(event)        
            
    def on_run(self, event):
        """
        Run Speaker Recognition
        """
        self.frame.run_menu_item.Enable(False)
        self.model.load_video(self.player.mpc.GetProperty('path'))
            
        self.thread_logger = threading.Thread(target=self.on_process)
        self.thread_logger.start()
        
            
        self.thread_extraction = threading.Thread(target=self.model.extract_speakers)
        self.thread_extraction.start()
    
    def on_select_cluster(self, event):
        print "select"
        self.toggle_pause()
        c = self.get_current_cluster()
        
        text = "Name %s\nSpeaker %s\nMean %s\nDistance %s" %(c.get_name(), c.get_speaker(), c.get_mean(), c.get_distance())
        
        self.clusters_list.set_info_clusters(text)
        
        self.clusters_list.buttons_sizer.ShowItems(True)
        self.clusters_list.Layout()
            
    def on_test(self, event):
        self.on_edit_cluster(event)
        
    def toggle_play(self):
        self.clusters_list.play_button.SetLabel("Pause")
        self.mode = TRAIN_ON
        print "play ",self.player.playbackTimer.IsRunning() 
        if not self.player.playbackTimer.IsRunning():
            self.player.mpc.Pause()
            self.player.playbackTimer.Start()
            
    def toggle_pause(self):
        self.clusters_list.play_button.SetLabel("Play")
        self.mode = TRAIN_OFF   
        print "pause ",self.player.playbackTimer.IsRunning()
        if self.player.playbackTimer.IsRunning():
               self.player.mpc.Pause()
               self.player.playbackTimer.Stop()       
                 
    def on_play_cluster(self, event):
        
        if self.mode == TRAIN_OFF:
            self.toggle_play()
            c = self.get_current_cluster()
            first_segments = c._segments[0]
           # print "on_play_cluster"
            print first_segments.get_start()
            c.print_segments()
            self.player.mpc.Seek( float(first_segments.get_start())/100 ,2)
            #self.player.mpc.
        else:
            self.toggle_pause()    
        
    def on_edit_cluster(self, event):
        
        self.cluster_form =ClusterForm(self.frame,"Edit cluster speaker")
        self.cluster_form.Bind(wx.EVT_BUTTON, self.set_speaker_name)
        self.cluster_form.Layout()
        self.cluster_form.ShowModal()
        print "on_edit"
        
    def set_speaker_name(self, event):
        if event.GetId() == CANCEL_DIALOG:
            self.cluster_form.Destroy()
            return
        
        if event.GetId() == OK_DIALOG:
            speaker = self.cluster_form.tc1.GetValue()
            if not len(speaker) == 0: 
                c = self.get_current_cluster()
                
                c.set_speaker(speaker)
                
                self.clusters_list.list.SetString(index,name + " ("+speaker+ ")")
                
                #self.clusters_list.list.SetSelection(index)
                
                cmd = wx.CommandEvent(wx.EVT_LISTBOX.evtType[0])
            #  (if your control is not a wx.ComboBox, obviously change the event name, and please write evtType exactly as I did)
                cmd.SetEventObject(self.clusters_list.list)
                cmd.SetId(self.clusters_list.list.GetId())
                self.clusters_list.list.GetEventHandler().ProcessEvent(cmd)
                
            
            
            self.cluster_form.Destroy()
            

    def exit(self):
        self.player.mpc.Quit()

class ClusterForm(wx.Dialog):
    def __init__(self, parent, title):
        wx.Dialog.__init__(self, parent, 20, title, wx.DefaultPosition, wx.Size(250, 100))
        
        #panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        
        fgs = wx.FlexGridSizer(3, 2, 9, 25)

        title = wx.StaticText(self, label="Speaker")

        self.tc1 = wx.TextCtrl(self,size=(150,25))

        fgs.AddMany([(title), (self.tc1, 1, wx.EXPAND)])

        fgs.AddGrowableRow(2, 1)
        fgs.AddGrowableCol(1, 1)

        hbox.Add(fgs, flag=wx.ALL|wx.EXPAND, border=15)
        self.b_ok = wx.Button(self, label='Ok', id=OK_DIALOG)
        self.b_cancel = wx.Button(self, label='Cancel', id=CANCEL_DIALOG)
#        self.Bind(wx.EVT_BUTTON, self.OnClose, id=1)
#        self.Bind(wx.EVT_BUTTON, self.OnRandomMove, id=2)
        
        buttonbox.Add(self.b_ok,1, border=15)
        buttonbox.Add(self.b_cancel,1, border=15)
        
        vbox.Add(hbox, flag= wx.ALIGN_CENTER|wx.ALL|wx.EXPAND)
        vbox.Add(buttonbox, flag= wx.ALIGN_CENTER)
        self.SetSizer(vbox)
        

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Voiceid Player", size=(800, 600))
        self._create_menu()
        self.sb = self.CreateStatusBar()
        #self.SetBackgroundColour("#000")
        self.Show()
        
    def _create_menu(self):
        """
        Creates a menu
        """
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        srMenu = wx.Menu()
        self.add_file_menu_item = fileMenu.Append(wx.NewId(), "&Open video", "Add Media File")
        self.run_menu_item = srMenu.Append(wx.NewId(), "&Run Recognition")
        self.train_menu_item = srMenu.Append(wx.NewId(), "&Test ")
        self.train_menu_item.Enable(True)
        menubar.Append(fileMenu, '&File')
        menubar.Append(srMenu, '&Speaker Recognition')
 
        self.SetMenuBar(menubar)
        
     
    def set_status_text(self, text):
        #TODO: set status text
        self.sb.SetStatusText(text)
        

class Player(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
#        self.SetBackgroundColour("#000")
        self.mpc = mpc.MplayerCtrl(self, 0, u'mplayer')
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.controlSizer = self.build_player_controls()
        self.sliderSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # create slider
        self.playbackSlider = wx.Slider(self, size=wx.DefaultSize)
        self.sliderSizer.Add(self.playbackSlider, 1, wx.ALL | wx.EXPAND, 5)
 
        # create track counter
        self.trackCounter = wx.StaticText(self, label="00:00")
        self.sliderSizer.Add(self.trackCounter, 0, wx.ALL | wx.CENTER, 5)
        
        # set up playback timer
        self.playbackTimer = wx.Timer(self)
        
        self.sizer.Add(self.mpc, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.sliderSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.controlSizer, 0, wx.ALL | wx.CENTER, 5)
        
        # bind buttons to function control
        self.Bind(mpc.EVT_MEDIA_STARTED, self.on_media_started)
        self.Bind(mpc.EVT_MEDIA_FINISHED, self.on_media_finished)
        self.Bind(mpc.EVT_PROCESS_STARTED, self.on_process_started)
        self.Bind(mpc.EVT_PROCESS_STOPPED, self.on_process_stopped)
        
        self.Bind(wx.EVT_SCROLL_CHANGED, self.update_slider, self.playbackSlider)
        
        self.SetSizerAndFit(self.sizer)
        self.sizer.Layout()
    
    
    def update_slider(self,event):
        
        self.mpc.Seek(self.playbackSlider.GetValue(), 2)
    
    def build_btn(self, btnDict, sizer):
        """"""
        bmp = btnDict['bitmap']
        handler = btnDict['handler']
 
        img = wx.Bitmap(os.path.join(bitmapDir, bmp))
        btn = buttons.GenBitmapButton(self, bitmap=img,
                                      name=btnDict['name'])
        btn.SetInitialSize()
        btn.Bind(wx.EVT_BUTTON, handler)
        sizer.Add(btn, 0, wx.LEFT, 3)
        
    
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

    def on_media_started(self, event):
        print 'Media started!'
        t_len = self.mpc.GetTimeLength()
        self.mpc.SetProperty("loop", 0)
        self.mpc.SetProperty("osdlevel",0) 
        self.playbackSlider.SetRange(0, t_len)
        self.playbackTimer.Start(100) 

    def on_media_finished(self, event):
        print 'Media finished!'
        self.playbackTimer.Start()
 
    def on_pause(self, event):
        """"""
        if self.playbackTimer.IsRunning():
            print "pausing..."
            self.mpc.Pause()
            self.playbackTimer.Stop()

    def on_process_started(self, event):
        print 'Process started!'
 
    def on_process_stopped(self, event):
        print 'Process stopped!'
 
    def on_play(self, event):
        """"""
        print "playing..."
        self.mpc.Pause()
        self.playbackTimer.Start()
        
    def on_next(self, event):
        """"""
        print "forwarding..."
        self.mpc.Seek(5)
       
    def on_prev(self, event):
        """"""
        print "backwarding..."
        self.mpc.Seek(-5)    

  
            #self.trackCounter.SetForegroundColour("WHITE")

class ClustersList(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, size=(250, 550))
        self.list = wx.ListBox(self, id=LIST_ID)
        self.info = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.play_button = wx.Button(self,label="Play",id = PLAY_ID)
        self.edit_button = wx.Button(self,label="Edit", id = EDIT_ID)
        self.buttons_sizer.Add(self.play_button,1,  wx.CENTER)
        self.buttons_sizer.Add(self.edit_button,1,  wx.CENTER)
        
        self.buttons_sizer.ShowItems(False)
        
        #self.SetBackgroundColour("#000")
        self.info.text_info = wx.StaticText(self.info, 1, "")
        
        sb_list = wx.StaticBox(self, label=" Speakers ")
        #sb_list.SetForegroundColour("#FFF")
        
        sb_info = wx.StaticBox(self, label=" Info ")
        #sb_info.SetForegroundColour("#FFF")
        
        self.boxsizer_list = wx.StaticBoxSizer(sb_list, wx.VERTICAL)
        self.boxsizer_list.Add(self.list,5, wx.EXPAND | wx.ALL, 2)
        
        self.boxsizer_info = wx.StaticBoxSizer(sb_info, wx.VERTICAL)
        self.boxsizer_info.Add(self.info,5, wx.EXPAND | wx.ALL, 2)
        self.boxsizer_info.Add(self.buttons_sizer,1, wx.ALL |wx.EXPAND)
        
        
        self.sizer.Add(self.boxsizer_info, 2, wx.EXPAND | wx.ALL,2)
        self.sizer.Add(self.boxsizer_list, 5, wx.EXPAND | wx.ALL,2)
        
        self.SetSizer(self.sizer)

    def add_cluster(self, cluster_label,cluster_speaker):
        self.list.Append(cluster_label+" ("+cluster_speaker+")")
        
        
    def set_info_clusters(self, text):

        self.info.text_info.SetLabel(text)
        
       
    
               
class ClusterInfo():
    pass
    

class Model:
    def __init__(self):
        self.voiceid = None
        self.db = GMMVoiceDB('/home/michela/SpeakerRecognition/voiceid/scripts/test_db')
        self._clusters = None
        
    def load_video(self, video_path):        
        self.voiceid = Voiceid(self.db, video_path)
        
    def extract_speakers(self):
        self.voiceid.extract_speakers(False, False, 4)
        self._clusters = self.voiceid.get_clusters()

    def get_status(self):
        return self.voiceid.get_status()
    
    def get_working_status(self):
        return self.voiceid.get_working_status()
    
    def get_clusters(self):
        return self.voiceid.get_clusters()
    
    def get_clusters_info(self):
        unknown = 0
        known = 0
        for c in self._clusters:
            if self._clusters[c].get_speaker() == 'unknown':
                unknown += 1
            else:
                known += 1
        return unknown, known
    
    def get_cluster(self, name):
        return self._clusters[name]
        
    
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
