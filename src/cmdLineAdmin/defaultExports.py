#!../../virtual-env/bin/python
# defaultExports.py
# Meteor Pi, Cambridge Science Centre
# Dominic Ford

# This script is used to set up a default export configuration

import datetime,sys

from mod_settings import *

import meteorpi_model as mp
import meteorpi_fdb
fdb_handle = meteorpi_fdb.MeteorDatabase( DBPATH , FDBFILESTORE )

# List all current user accounts
print "Current export configurations"
print "-----------------------------"
configs = fdb_handle.get_export_configurations()
for config in configs:
  print config.as_dict()
print "\n"

confirm = raw_input('Replace with default configuration? (Y/N) ')
if not confirm in 'Yy': sys.exit(0)

# Delete all export config
for config in configs:
  fdb_handle.delete_export_configuration(config.config_id)

# Fetch installation info (imported via mod_settings)
ii = installation_info

# Set up default file export configuration
search = mp.FileRecordSearch(limit=None)
config = mp.ExportConfiguration(target_url=ii.EXPORT_URL, user_id=ii.EXPORT_USERNAME, password=ii.EXPORT_PASSWORD, search=search, name="file_export", description="Export all image files to remote server", enabled=True)
fdb_handle.create_or_update_export_configuration(config)

# Set up default event export configuration
search = mp.EventSearch(limit=None)
config = mp.ExportConfiguration(target_url=ii.EXPORT_URL, user_id=ii.EXPORT_USERNAME, password=ii.EXPORT_PASSWORD, search=search, name="event_export", description="Export all object detections to remote server", enabled=True)
fdb_handle.create_or_update_export_configuration(config)

