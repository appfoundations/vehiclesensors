#!/usr/bin/python
# Copyright (c) 2017 Logicc Systems Ltd.
# Author: Andre Neto
# Bases on script by Alex Eames http://RasPi.tv  
# http://raspi.tv/?p=6791  
  
import RPi.GPIO as GPIO  
import settings
import sys
from time import sleep
import pickle
import subprocess
import datetime

try:
    verbose = settings.VERBOSE
    serial = settings.PI_KEY
    BUTTON_MIN_INTERVAL = settings.BUTTON_MIN_INTERVAL
    MAX_OPEN_TIME = settings.MAX_OPEN_TIME
except Exception, e:
    print __name__ + ": Could not read settings"
    print e
    sys.exit(1)

try:
    import putWarnAPI
except Exception, e:
    print __name__ + ": Could not perform imports"
    print e
    sys.exit(1)

GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering  

def setWarn( data ):
    try:
        f = open('buttonLastCall.pckl', 'rb')
        last = pickle.load(f)
        f.close()
        diff = (datetime.datetime.now() - last).total_seconds()
        if verbose:
            print 'read last button call time'
            print last
            print 'minutes since last button call'
            print diff
    except:
        diff = BUTTON_MIN_INTERVAL + 100
        if verbose:
            print 'no record from button call'

    if diff < BUTTON_MIN_INTERVAL:
        if verbose:
            print 'time since last button call not enough'
        sys.exit()

    try:
        f = open('limits.pckl', 'rb')
        limits = pickle.load(f)
        f.close()
        if verbose:
            print 'configured limits'
            print limits
    except:
        limits = None


    try:
        f = open('lastDoorStatus.pckl', 'rb')
        lastDoorStatus = pickle.load(f)
        f.close()
        if verbose:
            print 'last door status'
            print lastDoorStatus
    except:
        lastDoorStatus = None

    for item in data:
        print 'item'
        print item
        limit = None
        warn  = None
        if item[2] == 'temperature':
            if verbose:
                print 'temperature item:'
                print item
            try:
                limit = limits[item[0]]
                print limit
            except:
                limit = None

            limit = None

            if limit is not None and (item[1] > limit['max']):
                warn = 'tempAbove'
                msg = 'Warning! Temperature Above Acceptable Levels (' + str(item[1]) + ' > ' + str(limit['max']) + ')'
            elif limit is not None and (item[1] < limit['min']):    
                warn = 'tempBelow'
                msg = 'Warning! Temperature Below Acceptable Levels (' + str(item[1]) + ' < ' + str(limit['min']) + ')'
            else:
                warn = None

        elif item[2] == 'door':
            if verbose:
                print 'door item:'
                print item
            try:
                lastStatus = lastDoorStatus[item[0]]
                diff = (datetime.datetime.now() - lastStatus[3]).total_seconds()
                if verbose:
                    print 'limit: ' 
                    print MAX_OPEN_TIME
                    print 'seconds in current status'
                    print diff
                    print 'door current status:'
                    print item[1]
            except Exception,e:
                print e
                diff = 0

            if item[1] == 'OPEN' and diff > ( MAX_OPEN_TIME ) :
                warn = 'doorOpen'
                msg = 'Warning! Door open for more than acceptable time (' + str(int(diff)) + 'sec < ' + str(MAX_OPEN_TIME) + 'sec )'
            else:
                warn = None

        if warn is not None:
            if verbose:
                print 'setting warning'
            # check if sound play is ON
            cmd = "ps -ef | grep setSiren | grep -v grep"
            pp = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
            if pp.communicate()[0] == '':
                # if play is OFF - start play (backend/new thread)
                subprocess.Popen(['python', 'setSiren.py','-w', warn])
                # send warning email - inside play check to avoid high volume of mails
                putWarnAPI.postWarn(item[0], msg)

            return True
        
    return False
