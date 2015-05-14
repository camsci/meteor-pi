#!/usr/bin/python
# listTimelapse.py
# Meteor Pi, Cambridge Science Centre
# Dominic Ford

import datetime,time,sys

from mod_settings import *
from mod_time import *

import meteorpi_model as mp
import meteorpi_fdb
fdb_handle = meteorpi_fdb.MeteorDatabase( DBPATH , FDBFILESTORE )

tmin=0
tmax=time.time()

argc = len(sys.argv)
if (argc>1): tmin=float(sys.argv[1])
if (argc>2): tmax=float(sys.argv[2])

tmin=UTC2datetime(tmin)
tmax=UTC2datetime(tmax)

def metadata2dict(metadata):
  output={}
  for i in metadata:
    if (i.key.ns=="meteorpi"):
      output[i.key.s] = i.string_value
  return output

cameraList = fdb_handle.get_cameras()
for cameraId in cameraList:
  title = "Camera <%s>"%cameraId
  print "\n\n%s\n%s"%(title,"-"*len(title))
  print "%s\n  * %s\n  * High water mark: %s"%(cameraId,fdb_handle.get_camera_status(camera_id=cameraId),fdb_handle.get_high_water_mark(camera_id=cameraId))
  search = mp.FileRecordSearch(camera_ids=[cameraId],semantic_type=mp.NSString("timelapse/frame/bgrdSub/lensCorr"),exclude_events=True,before=tmax,after=tmin)
  files  = fdb_handle.search_files(search)
  files.sort(key=lambda x: x.file_time)
  print "  * %d matching files in time range %s --> %s"%(len(files),tmin,tmax)
  for fileObj in files:
    metadata = metadata2dict(fileObj.meta)
    print "  * %16s %s"%(fileObj.file_time , metadata['skyClarity'])

