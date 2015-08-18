activate_this = '/home/pi/meteor-pi/virtual-env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import logging, sys
logging.basicConfig(stream=sys.stderr)

from meteorpi_fdb import MeteorDatabase
from meteorpi_server import MeteorApp, admin_api, importer_api, query_api

# Configure and create database and server objects
db_path = 'localhost:/var/lib/firebird/2.5/data/meteorpi.fdb'
file_store_path = '/home/pi/meteor-pi/datadir/firebird_files'
db = MeteorDatabase(db_path=db_path, file_store_path=file_store_path)
meteor_app = MeteorApp(db=db)

# Add routes
admin_api.add_routes(meteor_app=meteor_app)
importer_api.add_routes(meteor_app=meteor_app)
query_api.add_routes(meteor_app=meteor_app)

# Expose WSGI application as 'application'
application = meteor_app.app
