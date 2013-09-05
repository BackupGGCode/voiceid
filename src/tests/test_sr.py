# -*- coding: utf-8 -*-
#############################################################################
#
# VoiceID, Copyright (C) 2011-2012, Sardegna Ricerche.
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
#############################################################################

from voiceid import sr
import unittest


class SegmentTest(unittest.TestCase):
    """voiceid.sr.Segment tests"""
    
    def test_merge_segments(self):
        s = sr.Segment("/home/mauro/dev/Lium-8.4/Intervista_a_Giuseppe_Tornatore 1 0 1657 M S U S0".split())
        s1 = sr.Segment("/home/mauro/dev/Lium-8.4/Intervista_a_Giuseppe_Tornatore 1 0 1657 M S U S0".split())
        s2 = sr.Segment("/home/mauro/dev/Lium-8.4/Intervista_a_Giuseppe_Tornatore 1 1657 2560  M S U S0".split())        
        s.merge(s2)
        self.assertEqual(s.get_duration(), s2.get_end() - s1.get_start())
    
    def test_null_segment(self):
        self.assertRaises(TypeError, sr.Segment)
        
    def test_seg_segment(self):
        s = sr.Segment("/home/mauro/dev/Lium-8.4/Intervista_a_Giuseppe_Tornatore 1 0 1657 M S U S0".split())
        self.assertEqual(s.get_basename(),"/home/mauro/dev/Lium-8.4/Intervista_a_Giuseppe_Tornatore" )
        self.assertEqual(s.get_duration(), 1657 )
        self.assertEqual(s.get_end(), 1657 )
        self.assertEqual(s.get_environment(), "S" )
        self.assertEqual(s.get_gender(), "M" )
        self.assertEqual(s.get_speaker(), "S0" )
        self.assertEqual(s.get_start(), 0 )
        
        
        
class ClusterTest(unittest.TestCase):
    """voiceid.sr.Cluster tests"""
    
    def test_null_cluster(self):
        self.assertRaises(TypeError,sr.Cluster)
        
    def test_cluster(self):
        c = sr.Cluster("ciccio", "M", 1000, "ffa")
        self.assertRaises(TypeError,  c.get_seg_header)
        
        c = sr.Cluster("ciccio", "M", 1000, "ffa", "S4")
        c.add_segment(sr.Segment("/home/mauro/dev/Lium-8.4/Intervista_a_Giuseppe_Tornatore 1 0 1657 M S U S0".split()))
        c.add_segment(sr.Segment("/home/mauro/dev/Lium-8.4/Intervista_a_Giuseppe_Tornatore 1 1657 2560  M S U S0".split()))
        