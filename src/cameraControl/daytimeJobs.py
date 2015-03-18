#!/usr/bin/python
# daytimeJobs.py
# Meteor Pi, Cambridge Science Centre
# Dominic Ford

# This script is a very generic file processor. It looks for files in
# directories with given extensions, works out the time associated with each
# file from its filename, and performs predefined shell-commands on them if
# they are newer than a given high-water mark. The list of tasks to be
# performed is defined in <module_daytimejobs>.

import os,time,sys,glob,datetime,operator

import module_log
from module_log import logTxt,getUTC
from module_settings import *
from module_daytimejobs import *

pid = os.getpid()

# User should supply unix time on commandline at which we are to stop work
if len(sys.argv)!=3:
  print "Need to call daytimeJobs.py with clock offset, and an end time to tell it when it needs to quit by."
  sys.exit(1)

utcOffset = float(sys.argv[1])
quitTime  = float(sys.argv[2])
module_log.toffset = utcOffset

logTxt("Running daytimeJobs. Need to quit at %s."%(datetime.datetime.fromtimestamp(quitTime).strftime('%Y-%m-%d %H:%M:%S')))

# Cleaning up any output files which are ahead of high water marks
logTxt("Cleaning up any output files which are ahead of high water marks")
import daytimeJobsClean

# Read our high water mark, and only analyse more recently-created data
os.chdir (DATA_PATH)
highWaterMarks = fetchHWM()

# We raise this exception if we pass the time when we've been told we need to hand execution back
class TimeOut(Exception): pass

try:
  for taskGroup in dayTimeTasks:
    [HWMout, taskList] = taskGroup;
    if HWMout not in highWaterMarks: highWaterMarks[HWMout]=0
    logtxt("Working on task group <%s>"%HWMout)
    jobList = []
    for task in taskList:
      [inDir,outDirs,inExt,cmd] = tasks

      # Operate on any input files which are newer than HWM
      for dirName, subdirList, fileList in os.walk(inDir):
        for f in fileList:
          if quitTime and (getUTC()>quitTime): raise TimeOut
          if f.endsWith(".%s"%inExt):
            utc = module_hwm.filenameToUTC(f)
            if (utc > highWaterMarks[HWMout]):
              params = {'binary_path':BINARY_PATH ,
                        'input':os.path.join(dirName,f) ,
                        'outdir':outDirs[0] ,
                        'filename':f[:-len(inExt+1)] ,
                        'date':fetchDayNameFromFilename(f) ,
                        'pid':pid ,
                        'opm': ('_openmax' if I_AM_A_RPI else '') ,
                       }
              for outDir in outDirs: os.system("mkdir -p %s"%(os.path.join(outDir,params['date'])))
              jobs.append( [utc, cmd % params] )

    # Do jobs in order of timestamp; raise high level water mark as we do each job
    jobList.sort(key=operator.itemgetter(0))
    for job in jobList:
      if quitTime and (getUTC()>quitTime): raise TimeOut
      os.system(job[1])
      highWaterMarks[HWMout] = job[0]
    logtxt("Completed %d jobs"%len(jobList))

except TimeOut:
      logTxt("Interrupting processing as we've run out of time")

# Write new list of high water marks
module_hwm.writeHWM(highWaterMarks)

# Twiddle our thumbs
if quitTime:
  logTxt("Finished daytimeJobs. Now twiddling our thumbs for a bit.")
  timeLeft = quitTime - getUTC()
  if (timeLeft>0): time.sleep(timeLeft)
  logTxt("Finished daytimeJobs and also finished twiddling thumbs.")

