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
from voiceid import VConf, utils, fm
import os
import shlex
import shutil
import subprocess
import sys
import threading
import time
"""Module containing high level classes relatives to the speaker recognition
task."""


CONFIGURATION = VConf()


class Segment(object):
    """A Segment taken from a segmentation file, representing the smallest
    recognized voice time slice.

    :type line: string
    :param line: the line taken from a seg file"""

    def __init__(self, line):
        """
        :type line: string
        :param line: the line taken from a seg file"""
        self._basename = str(line[0])
        self._one = int(line[1])
        self._start = int(line[2])
        self._duration = int(line[3])
        self._gender = str(line[4])
        self._environment = str(line[5])
        self._uuu = str(line[6])
        self._speaker = str(line[7])
        self._line = line[:]

    def __repr__(self):
        return str(self._line)

    def __cmp__(self, other):
        if self._start < other.get_start():
            return - 1
        if self._start > other.get_start():
            return 1
        return 0

    def merge(self, otr):
        """Merge two adjacent segments, the otr in to the original.
        Do not use for segments that are not adjacent, it can have
        odd behaviour.

        :type otr: Segment
        :param otr: the segment to be merged with"""
        self._duration = otr.get_start() - self.get_start()
        self._duration += otr.get_duration()
        self._line[3] = self._duration

    def rename(self, identifier):
        """Change the identifier of the segment.

        :type identifier: string
        :param identifier: the identifier of the speaker in the segment"""
        self._line[7] = self._speaker = identifier

    def get_basename(self):
        """Get the basename of the original file which belong the segment."""
        return self._basename

    def get_start(self):
        """Get the start frame index of the segment."""
        return self._start

    def get_end(self):
        """Get the end frame index of the segment."""
        return self._start + self._duration

    def get_duration(self):
        """Get the duration of the segment in frames."""
        return self._duration 

    def get_gender(self):
        """Get the gender of the segment."""
        return self._gender

    def get_environment(self):
        """Get the environment of the segment."""
        return self._environment

    def get_speaker(self):
        """Get the speaker identifier of the segment."""
        return self._speaker

    def get_line(self, cluster=None):
        """Get the line of the segment in the original seg file."""
#         print self._line
#         index = self._line.index(":")
#         half_left = self._line[:index]
#         r_index = self._line[index:].index(" ")
#         half_right = self._line[index+r_index:]
#         if cluster == None:
#             cluster = self._speaker 
#         self._line = half_left+":"+cluster+" "+half_right
        return self._line


class Cluster(object):
    """A Cluster object, representing a computed cluster for a single
    speaker, with gender, a number of frames and environment.

    :type identifier: string
    :param identifier: the cluster identifier

    :type gender: char F, M or U
    :param gender: the gender of the cluster

    :type frames: integer
    :param frames: total frames of the cluster

    :type dirname: string
    :param dirname: the directory where is the cluster wave file
    
    :type label: string
    :param label: the cluster identifier
    """

    def __init__(self, identifier, gender, frames, dirname, label=None):
        """
        :type identifier: string
        :param identifier: the cluster identifier

        :type gender: char F, M or U
        :param gender: the gender of the cluster

        :type frames: integer
        :param frames: total frames of the cluster

        :type dirname: string
        :param dirname: the directory where is the cluster wave file"""

        self.gender = gender
        self._frames = frames
        self._env = None  # environment (studio, telephone, unknown)
        self._label = label
        self._speaker = identifier
        self._segments = []
        self._seg_header = ";; cluster:%s [ score:FS = 0.0 ]" % label
        self._seg_header += " [ score:FT = 0.0 ] [ score:MS = 0.0 ]"
        self._seg_header += " [ score:MT = 0.0 ]\n"
        self.speakers = {}
        self.up_to_date = True
        self.wave = dirname + '.wav'
        self.dirname = dirname
        self.value = None
#        if identifier!= "unknown":
#            self.add_speaker(identifier, -32.5)

    def __str__(self):
        return "%s (%s)" % (self._label, self._speaker)
    
    def add_segment(self, segment):
        self._segments.append(segment)

    def get_seg_header(self):
        if not self._label:
            raise TypeError("no label defined for the Cluster")
        self._seg_header = ";; cluster:%s [ score:FS = 0.0 ]" % self._label
        self._seg_header += " [ score:FT = 0.0 ] [ score:MS = 0.0 ]"
        self._seg_header += " [ score:MT = 0.0 ]\n"
        return self._seg_header

    def get_segments(self):
        "Return segments in Cluster"
        return self._segments

    def get_segment(self, start_time):
        """Return segment by start_time"""
        for seg in self._segments:
            if seg.get_start() == start_time:
                return seg
        return None

    def remove_segment(self, start_time):
        """Remove segment by start_time"""
        for seg in self._segments:
            if seg.get_start() == start_time:
                self._segments.remove(seg)
                return True
        return False

    def add_speaker(self, identifier, score):
        """Add a speaker with a computed score for the cluster, if a better
        score is already present the new score will be ignored.

        :type identifier: string
        :param identifier: the speaker identifier

        :type score: float
        :param score: score computed between the cluster
                wave and speaker model"""
        val = float(score)
        if not identifier in self.speakers:
            self.speakers[identifier] = val
        else:
            if self.speakers[identifier] < val:
                self.speakers[identifier] = val

    def get_speaker(self):
        """Set the right speaker for the cluster if not set and returns
         its name."""
        if self._speaker == None:
            self._speaker = self.get_best_speaker()
        return self._speaker

    def set_speaker(self, identifier):
        """Set the cluster speaker identifier 'by hand'.

        :type identifier: string
        :param identifier: the speaker name or identifier"""
        self.up_to_date = False
        self._speaker = identifier

    def get_mean(self):
        """Get the mean of all the scores of all the tested speakers for
         the cluster."""
        try:
            return sum(self.speakers.values()) / len(self.speakers)
        except (ZeroDivisionError):
            return 0.0

    def get_name(self):
        """Get the cluster name assigned by the diarization process."""
        return self._label

    def get_best_speaker(self):
        """Get the best speaker for the cluster according to the scores.
         If the speaker'spk score is lower than a fixed threshold or is too
         close to the second best matching voice,
         then it is set as "unknown".

         :rtype: string
         :returns: the best speaker matching the cluster wav"""
        max_val = -33.0
        try:
            self.value = max(self.speakers.values())
        except ValueError:
            self.value = -100
        _speaker = 'unknown'
        distance = self.get_distance()
        
        if len(self.speakers.values()) >1:
            mean_distance = self.get_m_distance()
        else:
            mean_distance = .5
            
        thres = 0
        
        if distance > -1:
            thres = max_val - distance
        else: thres = max_val
        
        if self.value >= thres and mean_distance > .49:
            for spk in self.speakers:
                if self.speakers[spk] == self.value:
                    _speaker = spk
                    break
       
        if distance > -1 and distance < .07:
            _speaker = 'unknown'
            
        return _speaker

    def get_best_five(self):
        """Get the best five speakers in the db for the cluster.

        :rtype: array of tuple
        :returns: an array of five most probable speakers represented by
            ordered tuples of the form (speaker, score) ordered by score."""
        return sorted(self.speakers.iteritems(),
                      key=lambda (key, val): (val, key),
                      reverse=True)[:5]

    def get_gender(self):
        """Get the computed gender of the Cluster.

        :rtype: char
        :returns: the gender of the cluster"""
        gen = {'M': 0, 'F': 0, 'U': 0}
        differ = False
        for seg in self._segments:
            ggg = seg.get_gender()
            if ggg != self.gender:
                differ = True
                gen[ggg] += seg.get_duration()
        if differ:
            if gen['M'] > gen['F']:
                return 'M'
            else:
                return 'F'
        else:
            return self.gender

    def get_distance(self):
        """Get the distance between the best speaker score and the closest
        speaker score."""
        values = self.speakers.values()
        values.sort(reverse=True)
        try:
            return abs(values[1]) - abs(values[0])
        except (IndexError, ValueError):
            return -1

    def get_m_distance(self):
        """Get the distance between the best speaker score and the mean of
        all the speakers' scores."""
        value = max(self.speakers.values())
        return abs(abs(value) - abs(self.get_mean()))

    def generate_seg_file(self, filename):
        """Generate a segmentation file for the cluster.

        :type filename: string
        :param filename: the name of the seg file"""
        self._generate_a_seg_file(filename, self.wave[:-4])

    def _generate_a_seg_file(self, filename, first_col_name):
        """Generate a segmentation file for the given showname.

        :type filename: string
        :param filename: the name of the seg file

        :type first_col_name: string
        :param first_col_name: the name in the first column of the seg file,
               in fact the name and path of the corresponding wave file"""
        f_desc = open(filename, 'w')
        f_desc.write(self.get_seg_header())
        line = self._segments[0].get_line(self.get_name())[:]
        line[0] = first_col_name
        line[2] = 0
        line[3] = self._frames - 1
        #line[-1] = self._speaker
        f_desc.write("%s %s %s %s %s %s %s %s\n" % tuple(line))
        f_desc.close()

    def merge(self, other):
        """Merge the Cluster with another.

        :type other: Cluster
        :param other: the cluster to be merged with"""
        self._segments.extend(other._segments)
        self._segments.sort()

    def rename(self, label):
        """Rename the cluster and all the relative segments.

        :type label: string
        :param label: the new name of the cluster"""
        self._seg_header = self._seg_header.replace(self._label, label)
        self._label = label
        for seg in self._segments:
            seg.rename(label)

    def merge_waves(self):
        """Take all the wave of a cluster and build a single wave."""
        dirname = self.dirname
        name = self.get_name()
        videocluster = os.path.join(dirname, name)
        if sys.platform == 'win32':
            videocluster = dirname + '/' + name
        listwaves = os.listdir(videocluster)
        listwaves.sort()
        listw = [os.path.join(videocluster, fil) for fil in listwaves]
        #file_basename = os.path.join(dirname, name)
        if sys.platform == 'win32':
            listw = [videocluster + '/' + fil for fil in listwaves] 
        #    file_basename = dirname + '/' + name
        self.wave = os.path.join(dirname, name + ".wav")
        if sys.platform == 'win32':
            self.wave = dirname + '/' + name + ".wav"
        fm.merge_waves(listw, self.wave)

    def has_generated_waves(self):
        """Check if the wave files generated for the cluster are still
        present. In case you load a json file you shold not have those
        files."""
        dirname = self.dirname
        name = self.get_name()
        videocluster = os.path.join(dirname, name)
        try:
            listwaves = os.listdir(videocluster)
        except OSError:
            return False
        listw = [os.path.join(videocluster, fil) for fil in listwaves]
        for wav in listw:
            if os.path.isfile(wav) == True:
                continue
            else:
                return False
        return True

    def to_dict(self):
        """A dictionary representation of a Cluster."""
        speaker = self.get_speaker()
        segs = []
        for seg in self._segments:
            tmp = seg.get_line()[2:]
            tmp[-1] = speaker
            tmp[0] = int(seg.get_start())
            tmp[1] = int(seg.get_end())
            tmp.append(self.get_name())
            tmp[3] = self.speakers
            segs.append(tmp)
        return segs

    def print_segments(self):
        """Print cluster timing."""
        for seg in self._segments:
            print "%s to %s" % (
                        utils.humanize_time(float(seg.get_start()) / 100),
                        utils.humanize_time(float(seg.get_end()) / 100))

    def _get_seg_repr(self, set_speakers=True):
        """String representation of the segment"""
        result = str(self.get_seg_header())
        for seg in self._segments:
            line = seg.get_line()
            if set_speakers:
                line[-1] = self._speaker
            else:
                line[-1] = self._label
            result += "%s %s %s %s %s %s %s %s\n" % tuple(line)
        return result

    def get_duration(self):
        """Return cluster duration."""
        dur = 0
        for seg in self._segments:
            dur += seg.get_duration()
        return dur

    def _verify_duration(self):
        w_dur = fm.wave_duration(self.wave)
        return w_dur, self.get_duration()

class Voiceid(object):
    """The main object that represents the file audio/video to manage.

    :type db: object
    :param db: the VoiceDB database instance

    :type filename: string
    :param filename: the wave or video file to be processed

    :type single: boolean
    :param single: set to True to force to avoid diarization (a faster
           approach) only in case you have just a single speaker in the file"""

    @staticmethod
    def from_json_file(vdb, json_filename):
        """Build a Voiceid object from json file.

        :type json_filename: string
        :param json_filename: the file containing a json style python
                dictionary representing a Voiceid object instance"""
        opf = open(json_filename, 'r')
        jdict = eval(opf.read())
        opf.close()
        return Voiceid.from_dict(vdb, jdict)

    @staticmethod
    def from_dict(vdb, json_dict):
        """Build a Voiceid object from json dictionary.

        :type json_dict: dictionary
        :param json_dict: the json style python dictionary representing a
            Voiceid object instance"""
        vid = Voiceid(vdb, json_dict['url'])
        dirname = os.path.splitext(json_dict['url'])[0]
        try:
            for elm in json_dict['selections']:
                clu = vid.get_cluster(elm['speakerLabel'])
                if not clu:
                    clu = Cluster(elm['speaker'], elm['gender'], 0, dirname,
                                  elm['speakerLabel'])
                seg = Segment([dirname, 1, int(elm['startTime'] * 100),
                             int(100 * (elm['endTime'] - elm['startTime'])),
                             elm['gender'], 'U', 'U', elm['speaker']])
                clu.add_segment(seg)
                clu.speakers = elm['speakers']
                try:
                    clu.value = clu.speakers[elm['speaker']]
                except (KeyError):
                    print ('ERROR: For unknown speaker there is not a score')
                
                vid.add_update_cluster(elm['speakerLabel'], clu)
        except (ValueError):
            raise Exception('ERROR: Failed load dict, maybe in wrong format!')
        return vid

    def __init__(self, vdb, filename, single=False):
        """
        :type vdb: object
        :param vdb: the VoiceDB database instance

        :type filename: string
        :param filename: the wave or video file to be processed

        :type single: boolean
        :param single: set to True to force to avoid diarization (a faster
        approach) only in case you have just a single speaker in the file"""
        self.status_map = {0: 'file_loaded', 1: 'file_converted',
                           2: 'diarization_done', 3: 'trim_done',
                           4: 'speakers matched'}
        self.working_map = {0: 'converting_file', 1: 'diarization',
                            2: 'trimming', 3: 'voice matching', 4: 'extraction finished'}
        self._clusters = {}
        self._ext = ''
        self._time = 0
        self._interactive = False
        self._db = vdb
        utils.ensure_file_exists(filename)
        self._filename = self._basename = None
        self._set_filename(filename)
        self._status = 0
        self._single = single
        self._diar_conf = (3, 1.5)

    def __getitem__(self, key):
        return self._clusters.__getitem__(key)

    def __iter__(self):
        """Just iterate over the cluster's dictionary."""
        return self._clusters.__iter__()

    def get_status(self):
        """Get the status of the computation.
            0:'file_loaded',
            1:'file_converted',
            2:'diarization_done',
            3:'trim_done',
            4:'speakers matched'"""
        return self._status

    def get_working_status(self):
        """
        Get a string representation of the working status.
            0:'converting_file',
            1:'diarization',
            2:'trimming',
            3:'voice matching',
            4:'extraction finished'"""
        #TODO: fix some issue on restarting and so on about current status
        return self.working_map[self.get_status()]

    def get_db(self):
        """Get the VoiceDB instance used."""
        return self._db

    # setters and getters
    def _get_interactive(self):
        return self._interactive

    def _set_interactive(self, value):
        self._interactive = value

    def get_clusters(self):
        """Get the clusters recognized in the processed file."""
        return self._clusters

    def _set_clusters(self, value):
        self._clusters = value

    def _get_time(self):
        return self._time

    def _set_time(self, value):
        self._time = value

    def _set_filename(self, filename):
        """Set the filename of the current working file"""
        tmp_file = '_'.join(filename.split())
#        new_file = new_file.replace("'",
#                        '_').replace('-',
#                        '_').replace(' ',
#                        '_').replace('(', '_').replace(')', '_')
        new_file = ''
        pathsep = os.path.sep 
        if sys.platform == 'win32':
            pathsep = '/'
        for char in tmp_file:
            if char.isalnum() or char in  ['.', '_', ':', pathsep, '-']:
                new_file += char
        try:
            shutil.copy(filename, new_file)
        except shutil.Error, err:
            msg = "`%s` and `%s` are the same file" % (filename, new_file)
            if  str(err) == msg:
                pass
            else:
                raise err
        utils.ensure_file_exists(new_file)
        self._filename = new_file
        self._basename, self._ext = os.path.splitext(self._filename)

    def get_filename(self):
        """Get the name of the current working file."""
        return self._filename

    def get_file_basename(self):
        """Get the basename of the current working file."""
        return self._basename[:]

    def get_file_extension(self):
        """Get the extension of the current working file."""
        return self._ext[:]

    def get_cluster(self, label):
        """Get a the cluster by a given label.

        :type label: string
        :param label: the cluster label (i.e. S0, S12, S44...)"""
        try:
            return self._clusters[label]
        except KeyError:
            return None

    def add_update_cluster(self, label, cluster):
        """Add a cluster or update an existing cluster.

        :type label: string
        :param label: the cluster label (i.e. S0, S12, S44...)

        :type cluster: object
        :param cluster: a Cluster object"""
        self._clusters[label] = cluster

    def remove_cluster(self, label):
        """Remove and delete a cluster.

        :type label: string
        :param label: the cluster label (i.e. S0, S12, S44...)"""
        del self._clusters[label]

    def get_time_slices(self):
        """Return the time slices with all the information about start time,
        duration, speaker name or "unknown", gender and sound quality
        (studio/phone)."""
        tot = []
        for clu in self._clusters:
            tot.extend(self._clusters[clu].to_dict()[:])
        #tot.sort()
        return tot
    
    def get_duration(self):
        """Return the duration of all the time slices in the audio"""
        dur = 0
        for clu in self._clusters:
            dur += self._clusters[clu].get_duration()
        return dur
         
    def _verify_duration(self):
        for clu in self._clusters:
            print clu
            print self._clusters[clu]._verify_duration()
        

    def get_speakers_map(self):
        """A dictionary map between speaker label and speaker name."""
        speakers = {}
        for clu in self:
            speakers[clu] = self[clu].get_speaker()
        return speakers

    def _to_wav(self):
        """In case the input file is a video or the wave is in a wrong format,
         convert to wave."""
        self._status = 0
        fname = fm.file2wav(self.get_filename()) 
        if fname != self.get_filename():  # can change the name
            self._set_filename(fname)     # in case of wave transcoding
        self._status = 1

    def generate_seg_file(self, set_speakers=True):
        """Generate a seg file according to the information acquired about the
        speech clustering"""
        result = ''
        for clu in self._clusters:
            result += self._clusters[clu]._get_seg_repr(set_speakers)
        f_seg = open(self.get_file_basename() + '.seg', 'w')
        f_seg.write(result)
        f_seg.close()

    def diarization(self):
        """Run the diarization process. In case of single mode (single speaker
        in the input file) just create the seg file with silence and gender
        detection."""
        self._status = 1
        if self._single:
            try:
                os.mkdir(self.get_file_basename())
            except OSError, err:
                if err.errno != 17:
                    raise err
            fm._silence_segmentation(self._basename)
            fm._gender_detection(self._basename)
            segname = self._basename + '.seg'
            f_seg = open(segname, 'r')
            headers = []
            values = []
            differ = False
            basic = None
            gen = {'M': 0, 'F': 0, 'U': 0}
            for line in f_seg.readlines():
                if line.startswith(';;'):
                    headers.append(line[line.index('['):])
                else:
                    a_line = line.split(' ')
                    if basic == None:
                        basic = a_line[4]
                    if a_line[4] != basic:
                        differ = True
                    gen[a_line[4]] += int(a_line[3])
                    values.append(a_line)
            header = ";; cluster:S0 %s" % headers[0]
            from operator import itemgetter
            index = 0
            while index < len(values):
                values[index][2] = int(values[index][2])
                index += 1
            values = sorted(values, key=itemgetter(2))
            index = 0
            while index < len(values):
                values[index][2] = str(values[index][2])
                index += 1
            newfile = open(segname + '.tmp', 'w')
            newfile.write(header)
            if differ: #in case the gender of the single segments differ 
#                       then set the prevailing
#                print 'transgender :-D'
                if gen[ 'M' ] > gen[ 'F' ]:
                    basic = 'M'
                elif gen[ 'M' ] < gen[ 'F' ] :
                    basic = 'F'
                else:
                    basic = 'U'

            for line in values:
                line[4] = basic #same gender for all segs
                newfile.write(' '.join(line[:-1]) + ' S0\n')
            f_seg.close()
            newfile.close()
            shutil.copy(self.get_file_basename() + '.wav',
                        os.path.join(self.get_file_basename(), 'S0' + '.wav'))
            shutil.move(segname + '.tmp', segname)
            shutil.copy(self.get_file_basename() + '.seg',
                        os.path.join(self.get_file_basename(), 'S0' + '.seg'))
            utils.ensure_file_exists(segname)
        else:
#            print str(self._diar_conf[0])
#            print str(self._diar_conf[1])
            fm.diarization(self._basename, str(self._diar_conf[0]),
                            str(self._diar_conf[1]))
        self._status = 2

    def _to_trim(self):
        """Trim the wave input file according to the segmentation in the seg
        file. Run after diarization."""
        self._status = 2
        fm.seg2trim(self._basename)
        self._status = 3

    def _extract_clusters(self):
        extract_clusters(self._basename + '.seg', self._clusters)

    def _match_clusters(self, interactive=False, quiet=False):
        """Match for voices in the db"""
        basename = self.get_file_basename()
        #merging segments wave files for every cluster
        for cluster in self._clusters:
            self[cluster].merge_waves()
            self[cluster].generate_seg_file(os.path.join(basename,
                                                         cluster + ".seg"))
        wav_files = {}
        for cluster in self._clusters:
            filebasename = os.path.join(basename, cluster) + '.wav'
            wav_files[ filebasename ] = self[cluster].gender
        result = self.get_db().voices_lookup(wav_files)

        def wav_to_cluster(wav):
            return wav.split(os.path.sep)[-1].split(".")[0]

        for spk in result:
            cluster = wav_to_cluster(spk)
            for r in result[spk]:
                self[cluster].add_speaker(r, result[spk][r])
        if not quiet:
            print ""
        speakers = {}
        for clu in self._clusters:
            if not quiet:
                if interactive:
                    print "**********************************"
                    print "speaker ", clu
                    self[clu].print_segments()
            speakers[clu] = self[clu].get_best_speaker()
            self[clu].set_speaker(speakers[clu])
            """
            if not interactive:
                for speaker in self[clu].speakers:
                    if not quiet:
                        print "\t %s %s" % (speaker,
                            self[clu].speakers[speaker])
                if not quiet:
                    print '\t ------------------------'"""
            if interactive == True:
                self._set_interactive(True)
                speakers[clu] = best = _interactive_training(basename,
                                                          clu, speakers[clu])
                self[clu].set_speaker(best)

    def _rename_clusters(self):
        """Rename all clusters from S0 to Sn"""
        all_clusters = []
        temp_clusters = self._clusters.copy()
        for clu in temp_clusters:
            all_clusters.append(self._clusters.pop(clu))
        idx = 0
        for clu in all_clusters:
            label = 'S' + str(idx)
            clu.rename(label)
            self._clusters[label] = clu
            idx += 1

    def _merge_clusters(self, cl1, cl2):
        """Merge two clusers and delete the second"""
        label = ''
        to_delete = ''
        if cl1 < cl2:
            label = cl1
            to_delete = cl2
        else:
            label = cl2
            to_delete = cl1
        to_keep = self.get_cluster(label)
        to_remove = self._clusters.pop(to_delete)
        to_keep.merge(to_remove)

    def _automerge_segments(self):
        # copy all clusters to work on data, not reference
        clusters = self._clusters.copy()
        # prepare an array to store all the segments from all the clusters
        all_segs = []
        for clu in clusters:
            c_segs = clusters[clu].get_segments()
            for seg in c_segs:
                # for every segment put a tuple with segment and cluster label
                all_segs.append((seg, clu,))
        # sort all segs by start time (see __cmp__ in Segment)
        all_segs.sort()
        # set a struct (array of dictionaries) to put the segments to merge
        to_merge = []
        to_merge.append({})
        idx = 0  # index of to_merge, starting from 0
        prev = None
        for seg in all_segs:
            current = seg[:]  # a copy of the current seg to avoid reference
            # if is not the first for run (so we have two segments to compare)
            if prev:
                p_cluster = prev[1]   # the cluster of the previous segment
                cluster = current[1]  # the cluster of the current segment
                segment = current[0]  # a copy of the current segment
                # if previous and current segments belong to the same cluster
                if p_cluster == cluster:
                    # if the dictionary is still empty (has not key 'cluster')
                    if not cluster in to_merge[idx]:
                        to_merge[idx][cluster] = []  # initialize the dict
                        # the current and prev segment
                        to_merge[idx][cluster].extend([segment, prev[0]])
                    else:   # if the dictionary has already the key 'cluster'
                        try:
                            # if there is segment do not do nothing
                            to_merge[idx][cluster].index(segment)
                        except ValueError:
                            # if segment is not present, append segment
                            to_merge[idx][cluster].append(segment)
                # if prev and curr seg do not belong to the same cluster,
                # and current idx points to an already used dictionary
                elif len(to_merge[idx]) > 0:
                    idx += 1                # then increment idx and
                    # prepare a new empty dictionary for the next group
                    to_merge.append({})
            # update prev before ending the run
            prev = current[:]
        # cicle the array containing the groups to merge as dictionaries
        for groupdict in to_merge:
            # a dictionary containing just a key, the cluster label
            for cluster_key in groupdict:
                # reverse sort (by start_time) of the segments to merge
                groupdict[cluster_key].sort(reverse=True)
                prev = None    # initialize previous segment
                # cicle on the array of segments to merge
                for current_seg in groupdict[cluster_key]:
                    seg_start = current_seg.get_start()
                    # get the reference of current segment
                    segment = self.get_cluster(cluster_key).get_segment(
                                                                seg_start)
                    # if isn't first run (so we have at least two segs to merge
                    if prev:
                        # merge the previous segment into the current
                        segment.merge(prev)
                        # remove the previous segment from the cluster
                        self.get_cluster(cluster_key).remove_segment(
                                                        prev.get_start())
                    prev = segment            # update previous segment 

    def automerge_clusters(self):
        """Check for Clusters representing the same speaker and merge them."""
        all_clusters = self.get_clusters().copy()

        if not self._single:                # if not in single mode mode
            # initialize the variable to check if some change has happened 
            changed = False
            for cl_1 in all_clusters:         # cycle over clusters
                c_c1 = all_clusters[cl_1]
                for cl_2 in all_clusters:     # inner cycle over clusters
                    c_c2 = all_clusters[cl_2]
                    # if two clusters have the same speaker and have different 
                    # cluster identifiers
                    if cl_1 != cl_2 and c_c1.get_speaker() != 'unknown' and c_c1.get_speaker() == c_c2.get_speaker() and self._clusters.has_key(cl_1) and self._clusters.has_key(cl_2):
                        changed = True
                        # merge the clusters an record that something changed
                        self._merge_clusters(cl_1, cl_2)
            if changed:       #    if something has changed
                # rename all the clusters starting from S0
                self._rename_clusters()
                # remove also the old waves and seg files of the old clusters
                shutil.rmtree(self.get_file_basename())
                # rebuild all seg files
                self.generate_seg_file(set_speakers=False)
                # resplit the original wave file according to the new clusters
                self._to_trim()

    def extract_speakers(self, interactive=False, quiet=False, thrd_n=1):
        """Identify the speakers in the audio wav according to a speakers
        database. If a speaker doesn't match any speaker in the database then
        sets it as unknown. In interactive mode it asks the user to set
        speakers' names.

        :type interactive: boolean
        :param interactive: if True the user must interact to give feedback or
                train the computed clusters voices

        :type quiet: boolean
        :param quiet: silent mode, no prints in batch mode

        :type thrd_n: integer
        :param thrd_n: max number of concurrent threads for voice db matches"""

        if thrd_n < 1:
            thrd_n = 1
        # set the max number of threads the db can use to compare
        # in parallel the voices to the db models
        self.get_db().set_maxthreads(thrd_n)
        self._status = 0
        start_time = time.time()
        if not quiet:
            print self.get_working_status()
        # convert your input file to a Wave file having some tech requirements
        self._to_wav()
        if not quiet:
            print self.get_working_status()
        self.diarization()  # start diarization over your wave file
        diarization_time = time.time() - start_time
        if not quiet:
            print self.get_working_status()
        # trim the original wave file according to segs given by diarization
        self._to_trim()
        self._status = 3
        if not quiet:
            print self.get_working_status()
        # search for every identified cluster if there is 
        # a relative model voice in the db
        self._cluster_matching(diarization_time, interactive, quiet, thrd_n,
                               start_time)

    def _cluster_matching(self, diarization_time=None, interactive=False,
                          quiet=False, thrd_n=1, start_t=0):
        """Match for voices in the db"""
        basename = self.get_file_basename()
        self._extract_clusters()
        self._match_clusters(interactive, quiet)
#        if not interactive:
#            #merging
#            self.automerge_clusters()
        self._status = 4
        sec = fm.wave_duration(basename + '.wav')
        total_time = time.time() - start_t
        self._set_time(total_time)
        if not quiet:
            print self.get_working_status()
        if interactive:
            print "Updating db"
            self.update_db(thrd_n, automerge=True)
        if not interactive:
            if not quiet:
                for clu in self._clusters:
                    print "**********************************"
                    print "speaker ", clu
                    for speaker in self[clu].speakers:
                        print "\t %s %s" % (speaker, self[clu].speakers[speaker])
                    print '\t ------------------------'
                    distance = self[clu].get_distance()
                    try:
                        mean = self[clu].get_mean()
                        m_distance = self[clu].get_m_distance()
                    except (KeyError, ValueError):
                        mean = 0
                        m_distance = 0
                    print """\t best speaker: %s (distance from 2nd %f - mean %f - distance from mean %f ) """ % (self[clu],
                                                              distance, mean, m_distance)
                speakers_in_db = self.get_db().get_speakers()
                tot_voices = len(speakers_in_db['F']) + \
                    len(speakers_in_db['M']) + len(speakers_in_db['U'])

                if diarization_time != None:
                    voice_time = float(total_time - diarization_time)
                    t_f_s = voice_time / len(speakers_in_db)
                    print """\nwav duration: %s\nall done in %dsec (%s) (diarization %dsec time:%s )  with %s threads and %d voices in db (%f) """ % (utils.humanize_time(sec),
                                                                                                                                                  total_time,
                                                                                                                                                  utils.humanize_time(total_time),
                                                                                                                                                  diarization_time,
                                                                                                                                                  utils.humanize_time(diarization_time),
                                                                                                                                                  thrd_n,
                                                                                                                                                  tot_voices,
                                                                                                                                                  t_f_s)
                else:
                    print """\nwav duration: %s\nmatch clusters done in %dsec (%s)  with %s threads and %d voices in db """ % (utils.humanize_time(sec),
                                                                                                                                                  total_time,

                                                                                                                                                  utils.humanize_time(total_time),
                                                                                                                                                  thrd_n,
                                                                                                                                                  tot_voices
                                                                                                                                                )

    def _match_voice_wrapper(self, cluster, wav_name, db_entry, gender):
        """A wrapper to match the voices each in a different Thread."""
        results = self.get_db().match_voice(wav_name, db_entry, gender)
        for res in results:
            self[cluster].add_speaker(res, results[res])

    def set_noise_mode(self, mode):
        """Set a diarization configuration for noisy videos """
        if mode == 0:
            self._diar_conf = (3, 1.5)
        else:
            self._diar_conf = (7, 1.4)

    def update_db(self, t_num=4, automerge=False):
        """Update voice db after some changes, for example after a train
        session.

        :type t_num: integer
        :param t_num: number of contemporary threads processing the update_db

        :type automerge: boolean
        :param automerge: true to do the automerge or false to not do it"""

        def _get_available_wav_basename(label, basedir):
            """Find a non taken wave (base)name"""
            cont = 0
            label = os.path.join(basedir, label)
            wav_name = label + ".wav"
            if os.path.exists(wav_name):
                while True:  # search an inexistent name for new gmm
                    wav_name = label + "" + str(cont) + ".wav"
                    if not os.path.exists(wav_name):
                        break
                    cont = cont + 1
            else:
                open(label+".wav",'w').close()
                return label
            open(label+str(cont)+".wav",'w').close()
            return label + str(cont)
            #end _get_available_wav_basename

        def _build_model_wrapper(self, wave_b, cluster, wave_dir, new_speaker,
                                 old_speaker):
            """ A procedure to wrap the model building to run in a Thread 
            :type wave_b: string
            :param wave_b: path for the wave renamed with the current speaker name
            :type cluster: string
            :param cluster: the cluster label
            :type wave_dir: string
            :param wave_dir: basename for the wave
            :type new_speaker: string
            :param new_speaker: the current speaker name
            :type old_speaker: string
            :param old_speaker: the old speaker name
            
            """
            
            try:
                utils.ensure_file_exists(wave_b + '.seg')
            except IOError:
                self[cluster]._generate_a_seg_file(wave_b + '.seg', wave_b)
            utils.ensure_file_exists(wave_b + '.wav')

            old_cluster_value = self[cluster].value

            if new_speaker != "unknown": #add a new model
                self.get_db().add_model(wave_b, new_speaker,
                                        self[cluster].gender,self[cluster].value)
    
                #self[cluster]._generate_a_seg_file(wave_b + '.seg', wave_b)
                
                self._match_voice_wrapper(cluster, wave_b + '.wav', new_speaker,
                                          self[cluster].gender)

            #b_s = self[cluster].get_best_speaker()
            
            old_basename = self.get_file_basename()
            old_b_file = _get_available_wav_basename(old_s,
                                                 old_basename) #create a available wave name for the old speaker
            old_wav_name = old_b_file + '.wav'
            if old_speaker != new_speaker and old_speaker!='unknown':
                if not clu.has_generated_waves():
                    self._to_wav()
                    self._to_trim()
                clu.merge_waves()
                try:
                    shutil.move(clu.wave, old_wav_name)
                    utils.ensure_file_exists(old_wav_name)
                
                except OSError:
                    print 'WARNING: error renaming some wave files' 
                try:
                    utils.ensure_file_exists(old_b_file + '.seg')
                except IOError:
                    clu._generate_a_seg_file(old_b_file + '.seg', old_b_file)
                    
                #print " argument for remove model line 1154"
                #print (wave_b, old_speaker, old_cluster_value, self[cluster].gender)
                
                removed = self.get_db().remove_model(wave_b, old_speaker,
                                           old_cluster_value,
                                       self[cluster].gender)#remove the old speaker model from db if present
                if removed: 
                    a = self[cluster].speakers
                    a.pop(old_speaker) #update the cluster speaker's list
                    
                #print self[cluster].speakers
            if new_speaker != "unknown": self[cluster].set_speaker(new_speaker) #set new cluster's speaker name
            
            if not CONFIGURATION.KEEP_INTERMEDIATE_FILES:
                try:
                    os.remove("%s.seg" % wave_b)
#                    os.remove("%s.ident.seg" % wave_b )
                    os.remove("%s.init.gmm" % wave_b)
                    os.remove("%s.wav" % wave_b)
                    if os.path.exists(old_wav_name):
                        os.remove("%s" % old_wav_name)
                        os.remove(old_b_file + '.seg')
                except OSError:
                    print 'WARNING: error deleting some intermediate files'
            
            #end _build_model_wrapper

        thrds = {}
        if not os.path.exists(self.get_file_basename()+'.seg'): self.generate_seg_file(set_speakers=False)
           
            
        for clu in self._clusters.values():
            if clu.up_to_date == False:
                current_speaker = clu.get_speaker()
                old_s = clu.get_best_speaker()
                
                #If old speaker is unknown and current speaker is not unknown
                #set the old speaker score with the score closer to the current speaker 
                if old_s == 'unknown' and current_speaker!= "unknown":
                    try:
                        if current_speaker in clu.speakers:
                            c_s_score = clu.speakers[current_speaker] # current_speaker in db
                            for s in clu.speakers:
                                if s != current_speaker:
                                    s_score = clu.speakers[s]
                                    if abs(abs(s_score) - abs(c_s_score)) < 0.07:
                                        old_s = s
                    except:
                        print "updatedb "+str(clu.speakers)
#                print clu.speakers    
#                print "current_speaker out "+current_speaker
#                print "old_s  "+old_s
                
                basename = self.get_file_basename()
#                b_file = os.path.join(basename,current_speaker)
#                wav_name = os.path.join(basename,current_speaker)+'.wav'
#                if not os.path.exists(wav_name):
                        
                        
                        
                        
                b_file = _get_available_wav_basename(current_speaker,
                                                     basename) #search an available wave name for the current cluster starting from the current speaker
                wav_name = b_file + '.wav'
                if not clu.has_generated_waves():#
                    self._to_wav()
                    self._to_trim()
                clu.merge_waves()
                try:
                    shutil.move(clu.wave, wav_name)
                    utils.ensure_file_exists(wav_name)
               
                except OSError:
                    print 'WARNING: error renaming some wave files' 
                try:
                    utils.ensure_file_exists(b_file + '.seg')
                except IOError:
                    clu._generate_a_seg_file(b_file + '.seg', b_file) #generate a seg file for the current cluster
                     
                cluster_label = clu.get_name()
                thrds[cluster_label] = threading.Thread(
                                          target=_build_model_wrapper,
                                          args=(self, b_file,
                                                cluster_label,
                                                basename,
                                                current_speaker, old_s))
                thrds[cluster_label].start()
                
                clu.up_to_date = True
        for thr in thrds:
            if thrds[thr].is_alive():
                thrds[thr].join()
        if automerge:
            #merge all clusters relatives to the same speaker
            self.automerge_clusters()

    def to_xmp_string(self):
        """Return the Adobe XMP representation of the information about who is
        speaking and when. The tags used are Tracks and Markers, the ones used
        by Adobe Premiere for speech-to-text information."""
        """
        ...
        <xmpDM:Tracks>
            <rdf:Bag>
                <rdf:li>
                    <rdf:Description
                     xmpDM:trackName="Speaker identification">
                        <xmpDM:markers>
                            <rdf:Seq>
                                <rdf:li
                                 xmpDM:startTime="310"
                                 xmpDM:duration="140"
                                 xmpDM:speaker="Speaker0"
                                 />
                                <rdf:li
                                 xmpDM:startTime="450"
                                 xmpDM:duration="60"
                                 xmpDM:speaker="Speaker0"
                                 />
                            </rdf:Seq>
                        </xmpDM:markers>
                    </rdf:Description>
                </rdf:li>
            </rdf:Bag>
        </xmpDM:Tracks>
        ...
        """
        initial_tags = """<?xml version="1.0"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description  xmlns:xmpDM="http://ns.adobe.com/xmp/1.0/DynamicMedia/">
            <xmpDM:Tracks>
                <rdf:Bag>
                    <rdf:li>
                        <rdf:Description
                         xmpDM:trackName="Speaker identification">
                            <xmpDM:markers>
                                <rdf:Seq>"""
        inner_string = ''
        for seg in self.get_time_slices():
            inner_string += """
                                    <rdf:li
                                     xmpDM:startTime="%seg"
                                     xmpDM:duration="%seg"
                                     xmpDM:speaker="%seg"
                                     /> """ % (seg[0], seg[1], seg[-2])
        final_tags = """
                                </rdf:Seq>
                            </xmpDM:markers>
                        </rdf:Description>
                    </rdf:li>
                </rdf:Bag>
            </xmpDM:Tracks>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>
"""
        #TODO: extract previous XMP information from the media and merge 
        #      with speaker information
        return initial_tags + inner_string + final_tags

    def to_dict(self):
        """Return a JSON representation for the clustering information."""
#        """ The JSON model used is like:
#        <code>
#{
#    "duration": 15,
#    "url": "url1",
#    "selections": [{
#        "annotations": [{
#            "author": "",
#            "description": "speaker",
#            "keyword": "john",
#            "lang": "EN"
#        },
#        {
#            "author": "",
#            "description": "speakerLabel",
#            "keyword": "S0",
#            "lang": "EN"
#        }
#        , {
#            "author": "",
#            "description": "gender",
#            "keyword": "F",
#            "lang": "EN"        
#        }],
#        "resolution": "0x0",
#        "selW": 20,
#        "selH": 15,
#        "selY": 10,
#        "selX": 10,
#        "startTime" : 0,
#        "endTime" : 10
#        
#    }]
#}
#        </code>
#        
#        """

        dic = {"duration": self.get_duration(),
            "url": self._filename,
            "db":self.get_db().get_path(),
            "selections": [] }
        for seg in self.get_time_slices():
            dic['selections'].append({
                         "startTime": float(seg[0]) / 100.0,
                         "endTime": float(seg[1]) / 100.0,
                         'speaker': seg[-2],
                         'speakerLabel': seg[-1],
                         'gender': seg[2],
                         'speakers': seg[3]
                         })
        return dic

    def write_json(self, dictionary=None):
        """Write to file the json dictionary representation of the Clusters."""
        if not dictionary:
            dictionary = self.to_dict()
        prefix = ''
        if self._interactive:
            prefix = '.interactive'
        file_json = open(self.get_file_basename() + prefix + '.json', 'w')
        file_json.write(str(dictionary))
        file_json.close()

    def write_output(self, mode):
        """Write to file (basename.extension, for example: myfile.srt) the
        output of the recognition process.

        :type mode: string
        :param mode: the output format: srt, json or xmp"""
        if mode == 'srt':
            self.generate_seg_file()
            try:
                fm.seg2srt(self.get_file_basename() + '.seg')
            except:
                print "File seg do not exist!"            
            self.generate_seg_file(False)
#             if not CONFIGURATION.KEEP_INTERMEDIATE_FILES:
#                 os.remove(self.get_file_basename() + '.seg')
        if mode == 'json':
            self.write_json()
        if mode == 'xmp':
            file_xmp = open(self.get_file_basename() + '.xmp', 'w')
            file_xmp.write(str(self.to_xmp_string()))
            file_xmp.close()

def manage_ident(filebasename, gmm, clusters):
    """Take all the files created by the call of wav_vs_gmm() on the whole
    speakers db and put all the results in a bidimensional dictionary."""
    seg_f = open("%s.ident.%s.seg" % (filebasename, gmm), "r")
    for line in seg_f:
        if line.startswith(";;"):
#             print line
            splitted_line = line.split()[1].split(':')[1].split('_')
#             print splitted_line
            try:
                cluster, speaker = splitted_line
            except:
                speaker = splitted_line[0]
            idx = line.index('score:' + speaker) + len('score:' + speaker + " = ")
            iidx = line.index(']', idx) - 1
            value = line[idx:iidx]
            if not cluster in clusters:
                clusters[cluster] = Cluster(cluster, 'U', '0', '', cluster)
            clusters[cluster].add_speaker(speaker, value)
    seg_f.close()
    if not CONFIGURATION.KEEP_INTERMEDIATE_FILES:
        os.remove("%s.ident.%s.seg" % (filebasename, gmm))

def extract_clusters(segfilename, clusters):
    """Read _clusters from segmentation file."""
    f_seg = open(segfilename, "r")
    last_cluster = None
    rows = f_seg.readlines()
    f_seg.close()
    if ' '.join(rows).find(';;') != -1:
        for line in rows:
            if line.startswith(";;"):
                speaker_id = line.split()[1].split(':')[1]
                clusters[speaker_id] = Cluster(identifier='unknown',
                                                 gender='U',
                                                 frames=0,
                                                 dirname=os.path.splitext(
                                                        segfilename)[0],
                                                 label=speaker_id)
                last_cluster = clusters[ speaker_id ]
                last_cluster._seg_header = line
            else:
                line = line.split()
                last_cluster._segments.append(Segment(line))
                last_cluster._frames += int(line[3])
                last_cluster.gender = line[4]
                last_cluster._env = line[5]
    else:
        for line in rows:
            line = line.split()
            speaker_id = line[-1]
            if not speaker_id in clusters:
                clusters[speaker_id] = Cluster(identifier='unknown',
                                                 gender='U',
                                                 frames=0,
                                                 dirname=os.path.splitext(
                                                            segfilename)[0],
                                                 label=speaker_id)
            clusters[speaker_id]._segments.append(Segment(line))
            clusters[speaker_id]._frames += int(line[3])
            clusters[speaker_id].gender = line[4]
            clusters[speaker_id]._env = line[5]


def _interactive_training(filebasename, cluster, identifier):
    """A user interactive way to set the name to an unrecognized voice of a
    given cluster."""
    info = None
    prc = None
    if identifier == "unknown":
        info = """The system has not identified this speaker!"""
    else:
        info = "The system identified this speaker as '" + identifier + "'!"
    print info
    while True:
        try:
            char = raw_input("\n 1) Listen\n 2) Set " + 
            " name\n Press enter to skip\n> ")
        except EOFError:
            print ''
            continue
        print ''
        if prc != None and prc.poll() == None:
            prc.kill()
        if char == "1":
            videocluster = str(filebasename + "/" + cluster)
            listwaves = os.listdir(videocluster)
            listw = [os.path.join(videocluster, f) for f in listwaves]
            wrd = " ".join(listw)
            commandline = "play " + str(wrd)
            if sys.platform == 'win32':
                commandline = "vlc " + str(wrd)
                commandline = commandline.replace('\\', '\\\\')
            print "  Listening %s..." % cluster
            args = shlex.split(commandline)
            prc = subprocess.Popen(args, stdin=CONFIGURATION.output_redirect,
                                   stdout=CONFIGURATION.output_redirect,
                                   stderr=CONFIGURATION.output_redirect)
            time.sleep(1)
            continue
        if char == "2":
            menu = False
            while not menu:
                name = raw_input("Type speaker name "
                        + "or leave blank for unknown speaker: ")
                while True:
                    if len(name) == 0:
                        name = "unknown"
                    if not name.isalnum():
                        print 'No blank, dash or special chars allowed! Retry'
#                        menu = True
                        break
                    okk = raw_input("Save as '" + name + "'? [Y/n/m] ")
                    if okk in ('y', 'ye', 'yes', ''):
                        return name
                    if okk in ('n', 'no', 'nop', 'nope'):
                        break
                    if okk in ('m', "menu"):
                        menu = True
                        break
                if not menu:
                    print "Yes, no or menu, please!"
            continue
        if char == "":
            return identifier
        print "Type 1, 2 or enter to skip, please"

