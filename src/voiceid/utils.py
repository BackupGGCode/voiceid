#############################################################################
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
#############################################################################

import os
import shlex
import subprocess
from __init__ import output_redirect, lium_jar, db_dir, ubm_path


def alive_threads(t):
    """Check how much threads are running and alive in a thread dictionary

    :type t: dictionary
    :param t: thread dictionary like  { key : thread_obj, ... }
    """ 
    num = 0
    for thr in t:
        if t[thr].is_alive():
            num += 1
    return num

def start_subprocess(commandline):
    """Start a subprocess using the given commandline and check for correct
    termination.

    :type commandline: string
    :param commandline: the command to run in a subprocess 
    """
    args = shlex.split(commandline)
#    try:
    p = subprocess.Popen(args, stdin=output_redirect, stdout=output_redirect, 
                         stderr=output_redirect)
    retval = p.wait()
#    except:
#        print "except 1327"
#        args = commandline.split(' ')
#        p = subprocess.Popen(args, stdin=output_redirect, stdout=output_redirect, 
#                             stderr=output_redirect)
#        retval = p.wait()        
        
        
    if retval != 0:
        e = OSError("Subprocess %s closed unexpectedly [%s]" % (str(p), 
                                                                    commandline))
        e.errno = retval
        raise e

def ensure_file_exists(filename):
    """Ensure file exists and is not empty, otherwise raise an IOError.
    
    :type filename: string
    :param filename: file to check 
    """
    if not os.path.exists(filename):
        raise IOError("File %s doesn't exist or not correctly created" % filename)
    if not (os.path.getsize(filename) > 0):
        raise IOError("File %s empty"  % filename)

def check_deps():
    """Check for dependencies."""
    ensure_file_exists(lium_jar)

    dir_m = os.path.join(db_dir, "M")
    dir_f = os.path.join(db_dir, "F")
    dir_u = os.path.join(db_dir, "U")
    ensure_file_exists(ubm_path)
    if not os.path.exists(db_dir):
        raise IOError("No gmm db directory found in %s (take a look to the configuration, db_dir parameter)" % db_dir )
    if os.listdir(db_dir) == []:
        print "WARNING: Gmm db directory found in %s is empty" % db_dir
    if not os.path.exists(dir_m):
        os.makedirs(dir_m)
    if not os.path.exists(dir_f):
        os.makedirs(dir_f)
    if not os.path.exists(dir_u):
        os.makedirs(dir_u)

def humanize_time(secs):
    """Convert seconds into time format.
    
    :type secs: integer
    :param secs: the time in seconds to represent in human readable format 
           (hh:mm:ss) 
    """
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d,%s' % (hours, mins, int(secs), str(("%0.3f" % secs ))[-3:] )
