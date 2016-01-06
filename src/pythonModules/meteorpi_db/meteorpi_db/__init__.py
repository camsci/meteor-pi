# meteorpi_db

# Classes which interact with the MeteorPi database

import os
import sys
import MySQLdb
import shutil
import uuid
from contextlib import closing
import json
import numbers

from passlib.hash import pbkdf2_sha256
import meteorpi_model as mp
from meteorpi_db.generators import first_from_generator, first_non_null, MeteorDatabaseGenerators
from meteorpi_db.sql_builder import search_observations_sql_builder, search_files_sql_builder, \
    search_metadata_sql_builder
from meteorpi_db.exporter import FileExportTask, EventExportTask

SOFTWARE_VERSION = 2


class MeteorDatabase(object):
    """
    Class representing a single MeteorPi database and file store.

    :ivar con:
        Database connection used to access the db
    :ivar db_host:
        Host of the database
    :ivar db_user:
        User login to the database
    :ivar db_password:
        Password for the database
    :ivar db_name:
        Database name
    :ivar file_store_path:
        Path to the file store on disk
    :ivar string camera_id:
        The local camera ID
    :ivar object generator:
        Object generator class
    """

    def __init__(self, file_store_path, db_host='localhost', db_user='meteorpi', db_password='meteorpi',
                 db_name='meteorpi', camera_name='Undefined'):
        """
        Create a new db instance. This connects to the specified firebird database and retains a connection which is
        then used by methods in this class when querying or updating the database.

        :param file_store_path:
            Path to the file store on disk
        :param db_host:
            Host of the database
        :param db_user:
            User login to the database
        :param db_password:
            Password for the database
        :param db_name:
            Database name
        :param string camera_name:
            The local camera ID
        """
        self.db = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        self.con = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        if not os.path.exists(file_store_path):
            os.makedirs(file_store_path)
        if not os.path.isdir(file_store_path):
            raise ValueError('File store path already exists but is not a directory!')
        self.file_store_path = file_store_path
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.camera_name = camera_name
        self.generators = MeteorDatabaseGenerators(self.db, self.con)

    def __str__(self):
        """Simple string representation of this db object

        :return:
            info about the db path and file store location
        """
        return ('MeteorDatabase(file_store_path={0}, db_path={1}, db_host={2}, db_user={3}, db_password={4}, '
                'db_name={5}, camera_name={6})'.format(
                self.file_store_path,
                self.db_host,
                self.db_user,
                self.db_password,
                self.db_name,
                self.camera_name))

    # Functions relating to observatories
    def has_camera_id(self, camera_id):
        self.con.execute('SELECT 1 FROM archive_observatories WHERE publicId=%s;', (camera_id,))
        return len(self.con.fetchall()) > 0

    def has_camera_name(self, camera_name):
        self.con.execute('SELECT 1 FROM archive_observatories WHERE name=%s;', (camera_name,))
        return len(self.con.fetchall()) > 0

    def get_camera_from_name(self, camera_name):
        self.con.execute('SELECT * FROM archive_observatories WHERE name=%s;', (camera_name,))
        results = self.con.fetchall()
        if len(results) < 1:
            raise ValueError("No such camera: %s" % camera_name)
        return results[0]

    def get_camera_from_id(self, camera_id):
        self.con.execute('SELECT * FROM archive_observatories WHERE publicId=%s;', (camera_id,))
        results = self.con.fetchall()
        if len(results) < 1:
            raise ValueError("No such camera: %s" % camera_id)
        return results[0]

    def register_camera(self, camera_name, latitude, longitude):
        camera_id = uuid.uuid4().hex[:16]
        self.con.execute("""
INSERT INTO archive_observatories
(publicId, name, latitude, longitude)
VALUES
(%s, %s, %s, %s);
""", (camera_id, camera_name, latitude, longitude))
        return camera_id

    def delete_camera(self, camera_name):
        self.con.execute("DELETE FROM archive_observatories WHERE name=%s;", (camera_name,))

    def get_camera_ids(self):
        """
        Retrieve the IDs of all cameras.

        :return:
            A list of camera IDs for all cameras
        """
        self.con.execute('SELECT publicId FROM archive_observatories;')
        return map(lambda row: row['publicId'], self.con.fetchall())

    def get_camera_names(self):
        self.con.execute('SELECT name FROM archive_observatories;')
        return map(lambda row: row['name'], self.con.fetchall())

    # Functions for returning observatory metadata
    def has_camera_metadata(self, status_id):
        """
        Check for the presence of the given metadata item

        :param string status_id:
            The metadata item ID
        :return:
            True if we have a metadata item with this ID, False otherwise
        """
        self.con.execute('SELECT 1 FROM archive_metadata WHERE publicId=%s;', (status_id,))
        return len(self.con.fetchall()) > 0

    def get_camera_metadata(self, item_id):
        search = mp.ObservatoryMetadataSearch(item_id=item_id)
        b = search_metadata_sql_builder(search)
        sql = b.get_select_sql(columns='l.publicId AS camera_id, l.name AS camera_name, '
                                       'l.latitude AS camera_lat, l.longitude AS camera_lng'
                                       'stringValue, floatValue, '
                                       'f.name AS metadata_key, time, setAtTime AS time_created, setByUser AS user_created',
                               skip=0, limit=1, order='f.fileTime DESC')
        items = list(self.generators.camera_metadata_generator(sql=sql, sql_args=b.sql_args))
        if not items:
            return None
        return items[0]

    def search_camera_metadata(self, search):
        b = search_metadata_sql_builder(search)
        sql = b.get_select_sql(columns='l.publicId AS camera_id, l.name AS camera_name, '
                                       'l.latitude AS camera_lat, l.longitude AS camera_lng'
                                       'stringValue, floatValue, '
                                       'f.name AS metadata_key, time, setAtTime AS time_created, setByUser AS user_created',
                               skip=0, limit=1, order='f.fileTime DESC')
        items = list(self.generators.camera_metadata_generator(sql=sql, sql_args=b.sql_args))
        rows_returned = len(items)
        total_rows = rows_returned + search.skip
        if (rows_returned == search.limit > 0) or (rows_returned == 0 and search.skip > 0):
            self.con.execute(b.get_count_sql(), b.sql_args)
            total_rows = self.con.fetchone()[0]
        return {"count": total_rows,
                "items": items}

    def register_camera_metadata(self, camera_name, key, value, metadata_time, time_created, user_created):
        camera = self.get_camera_from_name(camera_name)
        item_id = mp.getHash(metadata_time, camera['publicId'], key)
        key_id = self.get_metadata_key_id(key)

        str_value = float_value = None
        if isinstance(value, numbers.Number):
            float_value = value
        else:
            str_value = str(value)

        # Insert into database
        self.con.execute("""
INSERT INTO archive_metadata
(publicId, observatory, fieldId, time, setAtTime, setByUser, stringValue, floatValue)
VALUES
(%s, %s, %s, %s, %s, %s, %s, %s);
""", (item_id, camera['uid'], key_id, metadata_time, time_created, user_created, str_value, float_value))

        return mp.ObservatoryMetadata(camera_id=camera['uid'], camera_name=camera_name,
                                      camera_lat=camera['latitude'], camera_lng=camera['longitude'],
                                      key=key, value=value, metadata_time=metadata_time,
                                      time_created=time_created, user_created=user_created)

    def get_camera_status(self, time=None, camera_name=None):
        if time is None:
            time = mp.now()
        if camera_name is None:
            camera_name = self.camera_name
        camera = self.get_camera_from_name(camera_name)

        output = {}

        self.con.execute('SELECT uid,metaKey FROM archive_metadataFields;')
        for item in self.con.fetchall():
            self.con.execute("""
SELECT floatValue, stringValue FROM archive_metadata
WHERE observatory=%s AND fieldId=%s AND time<%s ORDER BY time DESC LIMIT 1
""", (camera['uid'], item['uid'], time))
            results = self.con.fetchall()
            if len(results) > 0:
                result = results[0]
                if result['stringValue'] is None:
                    value = result['floatValue']
                else:
                    value = result['stringValue']
                output[item['metaKey']] = value
        return output

    def lookup_camera_metadata(self, key, time=None, camera_name=None):
        if time is None:
            time = mp.now()
        if camera_name is None:
            camera_name = self.camera_name
        camera = self.get_camera_from_name(camera_name)

        self.con.execute('SELECT uid FROM archive_metadataFields WHERE metaKey=%s;', (key,))
        results = self.con.fetchall()
        if len(results) < 1:
            return None
        self.con.execute("""
SELECT floatValue, stringValue FROM archive_metadata
WHERE observatory=%s AND fieldId=%s AND time<%s ORDER BY time DESC LIMIT 1
""", (camera['uid'], results[0]['uid'], time))
        results = self.con.fetchall()
        if len(results) < 1:
            return None
        result = results[0]
        if result['stringValue'] is None:
            value = result['floatValue']
        else:
            value = result['stringValue']
        return value

    # Functions relating to metadata keys
    def get_metadata_key_id(self, metakey):
        self.con.execute("SELECT uid FROM archive_metadataFields WHERE metaKey=%s;", (metakey,))
        results = self.con.fetchall()
        if len(results) < 1:
            self.con.execute("INSERT INTO archive_metadataFields (metaKey) VALUES (%s);", (metakey,))
            self.con.execute("SELECT uid FROM archive_metadataFields WHERE metaKey=%s;", (metakey,))
            results = self.con.fetchall()
        return results[0]['uid']

    # Functions relating to file objects
    def file_path_for_id(self, repository_fname):
        """
        Get the system file path for a given file ID. Does not guarantee that the file exists!

        :param string repository_fname:
            ID of a file (which may or may not exist, this method doesn't check)
        :return:
            System file path for the file
        """
        return os.path.join(self.file_store_path, repository_fname)

    def has_file_id(self, repository_fname):
        """
        Check for the presence of the given file_id

        :param string repository_fname:
            The file ID
        :return:
            True if we have a :class:`meteorpi_model.FileRecord` with this ID, False otherwise
        """
        self.con.execute('SELECT 1 FROM archive_files WHERE repositoryFname = %s', (repository_fname,))
        return len(self.con.fetchall()) > 0

    def delete_file(self, repository_fname):
        file_path = self.file_path_for_id(repository_fname)
        try:
            os.unlink(file_path)
        except OSError:
            print "Could not delete file <%s>" % file_path
            pass
        self.con.execute('DELETE FROM archive_files WHERE repositoryFname = %s', (repository_fname,))

    def get_file(self, repository_fname):
        """
        Retrieve an existing :class:`meteorpi_model.FileRecord` by its ID

        :param string repository_fname:
            The file ID
        :return:
            A :class:`meteorpi_model.FileRecord` instance, or None if not found
        """
        search = mp.FileRecordSearch(repository_fname=repository_fname)
        b = search_files_sql_builder(search)
        sql = b.get_select_sql(columns='f.observationId, f.mimeType, f.fileName, f.semanticType, f.fileTime, '
                                       'f.fileSize, f.fileMD5, l.publicId AS camera_id, l.name AS camera_name',
                               skip=0, limit=1, order='f.fileTime DESC')
        files = list(self.generators.file_generator(sql=sql, sql_args=b.sql_args))
        if not files:
            return None
        return files[0]

    def search_files(self, search):
        """
        Search for :class:`meteorpi_model.FileRecord` entities

        :param search:
            an instance of :class:`meteorpi_model.FileRecordSearch` used to constrain the events returned from the DB
        :return:
            a structure of {count:int total rows of an unrestricted search, events:list of
            :class:`meteorpi_model.FileRecord`}
        """
        b = search_files_sql_builder(search)
        sql = b.get_select_sql(columns='f.observationId, f.mimeType, f.fileName, f.semanticType, f.fileTime, '
                                       'f.fileSize, f.fileMD5, l.publicId AS camera_id, l.name AS camera_name',
                               skip=search.skip,
                               limit=search.limit,
                               order='f.fileTime DESC')
        files = list(self.generators.file_generator(sql=sql, sql_args=b.sql_args))
        rows_returned = len(files)
        total_rows = rows_returned + search.skip
        if (rows_returned == search.limit > 0) or (rows_returned == 0 and search.skip > 0):
            self.con.execute(b.get_count_sql(), b.sql_args)
            total_rows = self.con.fetchone()[0]
        return {"count": total_rows,
                "files": files}

    def register_file(self, observation_id, file_path, file_time, mime_type, semantic_type):
        """
        Register a file in the database, also moving the file into the file store. Returns the corresponding FileRecord
        object.

        :param string file_path:
            The path of the file on disk to register. This file will be moved into the file store and renamed.
        :param string mime_type:
            MIME type of the file
        :param string semantic_type:
            A string defining the semantic type of the file
        :param float file_time:
            UTC datetime of the import of the file into the database
        :return:
            The resultant :class:`meteorpi_model.FileRecord` as stored in the database
        """

        # Check that file exists
        if not os.path.exists(file_path):
            raise ValueError('No file exists at {0}'.format(file_path))

        # Get checksum for file, and size
        file_size_bytes = os.stat(file_path).st_size
        md5 = mp.get_md5_hash(file_path)
        file_name = os.path.split(file_path)[1]

        # Fetch information about parent observation
        self.con.execute("""
SELECT obsTime, l.publicId AS camera_id, l.name AS camera_name FROM archive_observations o
INNER JOIN archive_observatories l ON observatory=l.uid
WHERE o.publicId=%s
""", (observation_id,))
        obs = self.con.fetchall()
        if len(obs) == 0:
            raise ValueError("No observation with ID <%s>" % observation_id)
        obs = obs[0]
        repository_fname = mp.getHash(obs['obsTime'], obs['publicId'], file_name)

        # Insert into database
        self.con.execute("""
INSERT INTO archive_files
(observationId, mimeType, fileName, semanticType, fileTime, fileSize, repositoryFname, fileMD5)
VALUES
(%s, %s, %s, %s, %s, %s, %s, %s);
""", (observation_id, mime_type, file_name, semantic_type, file_time, file_size_bytes, repository_fname, md5))

        # Move the original file from its path
        target_file_path = os.path.join(self.file_store_path, repository_fname)
        try:
            shutil.move(file_path, target_file_path)
        except:
            sys.stderr.write("Could not move file into repository\n")

        result_file = mp.FileRecord(camera_id=obs['camera_id'],
                                    camera_name=obs['camera_name'],
                                    observation_id=observation_id,
                                    repository_fname=repository_fname,
                                    file_time=file_time,
                                    file_size=file_size_bytes,
                                    file_name=file_name,
                                    mime_type=mime_type,
                                    semantic_type=semantic_type,
                                    file_md5=md5
                                    )

        # Return the resultant file object
        return result_file

    def has_observation_id(self, observation_id):
        """
        Check for the presence of the given event_id

        :param string observation_id:
            The observation ID
        :return:
            True if we have a :class:`meteorpi_model.Observation` with this Id, False otherwise
        """
        self.con.execute('SELECT 1 FROM archive_observations WHERE publicId = %s', (observation_id,))
        return len(self.con.fetchall()) > 0

    def delete_observation(self, observation_id):
        self.con.execute('SELECT repositoryFname FROM archive_files f '
                         'INNER JOIN archive_observations o ON f.observationId=o.uid '
                         'WHERE o.publicId=%s;', (observation_id,))
        for file in self.con.fetchall():
            self.delete_file(file['repositoryFname'])
        self.con.execute('DELETE FROM archive_observations WHERE publicId = %s', (observation_id,))

    def get_observation(self, observation_id):
        """
        Retrieve an existing :class:`meteorpi_model.Observation` by its ID

        :param string observation_id:
            UUID of the observation
        :return:
            A :class:`meteorpi_model.Observation` instance, or None if not found
        """
        search = mp.ObservationSearch(observation_id=observation_id)
        b = search_observations_sql_builder(search)
        sql = b.get_select_sql(columns='l.publicId AS camera_id, l.name AS camera_name, '
                                       'o.obsTime, o.obsType, o.publicId',
                               skip=0, limit=1, order='f.obsTime DESC')
        obs = list(self.generators.observation_generator(sql=sql, sql_args=b.sql_args))
        if not obs:
            return None
        return obs[0]

    def search_events(self, search):
        """
        Search for :class:`meteorpi_model.Event` entities

        :param search:
            an instance of :class:`meteorpi_model.EventSearch` used to constrain the events returned from the DB
        :return:
            a structure of {count:int total rows of an unrestricted search, events:list of
            :class:`meteorpi_model.Event`}
        """
        b = search_observations_sql_builder(search)
        sql = b.get_select_sql(columns='l.publicId AS camera_id, l.name AS camera_name, '
                                       'o.obsTime, o.obsType, o.publicId',
                               skip=0, limit=1, order='f.obsTime DESC')
        obs = list(self.generators.observation_generator(sql=sql, sql_args=b.sql_args))
        rows_returned = len(obs)
        total_rows = rows_returned + search.skip
        if (rows_returned == search.limit > 0) or (rows_returned == 0 and search.skip > 0):
            self.con.execute(b.get_count_sql(), b.sql_args)
            total_rows = self.con.fetchone()[0]
        return {"count": total_rows,
                "obs": obs}

    def register_observation(self, camera_name, user_id, time_set, obs_time, obs_type, obs_meta=None):
        """
        Register a new event, updating the database and returning the corresponding Event object

        :param string camera_name:
            The ID of the camera which produced this event
        :param string user_id:
            The ID of the user who created this observation
        :param float obs_time:
            The UTC date/time of the observation
        :param string obs_type:
            A string describing the semantic type of this observation
        :param list obs_meta:
            A list of :class:`meteorpi_model.Meta` used to provide additional information about this event
        :return:
            The :class:`meteorpi_model.Observation` as stored in the database
        """

        if obs_meta is None:
            obs_meta = []

        # Get camera id from name
        camera = self.get_camera_from_name(camera_name)

        # Create a unique ID for this observation
        observation_id = mp.getHash(obs_time, camera['publicId'], obs_type)

        # Insert into database
        self.con.execute("""
INSERT INTO archive_observations
(publicId, observatory, userId, obsTime, obsType)
VALUES
(%s, %s, %s, %s, %s);
""", (observation_id, camera['uid'], user_id, obs_time, obs_type))

        # Store the observation metadata
        for meta in obs_meta:
            self.con.execute("""
INSERT INTO archive_metadata (fieldId, time, setAtTime, setByUser, stringValue, floatValue, observationId)
VALUES (%s, %s, %s, %s, %s, %s, %s)
""", (self.get_metadata_key_id(meta.key),
      obs_time,
      time_set,
      user_id,
      meta.string_value(),
      meta.float_value(),
      observation_id))

        observation = mp.Observation(camera_name=camera_name,
                                     camera_id=camera['publicId'],
                                     obs_time=obs_time,
                                     obs_id=observation_id,
                                     file_records=None,
                                     meta=obs_meta)
        return observation

    # Functions for handling user accounts
    def get_user(self, user_id, password):
        """
        Retrieve a user record

        :param user_id:
            the user ID
        :param password:
            password
        :return:
            A :class:`meteorpi_model.User` if everything is correct
        :raises:
            ValueError if the user is found but password is incorrect or if the user is not found.
        """
        self.con.execute('SELECT uid, pwHash FROM archive_users WHERE userId = %s;', (user_id,))
        results = self.con.fetchall()
        if len(results) == 0:
            raise ValueError("No such user")
        pw_hash = results[0]['pwHash']
        # Check the password
        if not pbkdf2_sha256.verify(password, pw_hash):
            raise ValueError("Incorrect password")

        # Fetch list of roles
        self.con.execute('SELECT name FROM archive_roles r INNER JOIN archive_user_roles u ON u.roleId=r.uid '
                         'WHERE u.userId = %s;', (results[0]['uid'],))
        role_list = [row['name'] for row in self.con.fetchall()]
        return mp.User(user_id=user_id, roles=role_list)

    def get_users(self):
        """
        Retrieve all users in the system

        :return:
            A list of :class:`meteorpi_model.User`
        """
        output = []
        self.con.execute('SELECT userId, uid FROM archive_users;')
        results = self.con.fetchall()

        for result in results:
            # Fetch list of roles
            self.con.execute('SELECT name FROM archive_roles r INNER JOIN archive_user_roles u ON u.roleId=r.uid '
                             'WHERE u.userId = %s;', (result['uid'],))
            role_list = [row['name'] for row in self.con.fetchall()]
            output.append(mp.User(user_id=result['userId'], roles=role_list))
        return output

    def create_or_update_user(self, user_id, password, roles):
        """
        Create a new user record, or update an existing one

        :param user_id:
            user ID to update or create
        :param password:
            new password, or None to leave unchanged
        :param roles:
            new roles, or None to leave unchanged
        :return:
            the action taken, one of "none", "update", "create"
        :raises:
            ValueError if there is no existing user and either password or roles is None
        """
        action = "update"
        self.con.execute('SELECT 1 FROM archive_users WHERE userId = %s;', (user_id,))
        results = self.con.fetchall()
        if len(results) == 0:
            if password is None:
                raise ValueError("Must specify an initial password when creating a new user!")
            action = "create"
            self.con.execute('INSERT INTO archive_users (userId, pwHash) VALUES (%s,%s)',
                             (user_id, pbkdf2_sha256.encrypt(password)))

        if password is None and roles is None:
            action = "none"
        if password is not None:
            self.con.execute('UPDATE archive_users SET pwHash = %s WHERE userId = %s',
                             (pbkdf2_sha256.encrypt(password), user_id))
        if roles is not None:

            # Clear out existing roles, and delete any unused roles
            self.con.execute("DELETE FROM archive_user_roles r INNER JOIN archive_users u ON r.userId=u.uid "
                             "WHERE u.userId=%s;", (user_id,))
            self.con.execute("DELETE FROM archive_roles r WHERE r.uid NOT IN "
                             "(SELECT roleId FROM archive_user_roles);")

            for role in roles:
                self.con.execute("SELECT uid FROM archive_roles WHERE name=%s;", (role,))
                results = self.con.fetchall()
                if len(results) < 1:
                    self.con.execute("INSERT INTO archive_roles (name) VALUES (%s);", (role,))
                    self.con.execute("SELECT uid FROM archive_roles WHERE name=%s;", (role,))
                    results = self.con.fetchall()

                    self.con.execute('INSERT INTO archive_user_roles (userId, roleId) VALUES '
                                     '(%s, %s)', (user_id, results[0]['uid']))
            return action

    def delete_user(self, user_id):
        """
        Completely remove the specified user ID from the system

        :param string user_id:
            The user_id to remove
        """
        self.con.execute('DELETE FROM archive_users WHERE userId = %s', (user_id,))

    # Functions for handling export configurations
    def get_export_configuration(self, config_id):
        """
        Retrieve the ExportConfiguration with the given ID

        :param string config_id:
            ID for which to search
        :return:
            a :class:`meteorpi_model.ExportConfiguration` or None, or no match was found.
        """
        sql = (
            'SELECT uid, exportConfigId, exportType, searchString, targetURL, '
            'targetUser, targetPassword, exportName, description, active '
            'FROM archive_exportConfig WHERE exportConfigId = %s')
        return first_from_generator(
                self.generators.export_configuration_generator(sql=sql, sql_args=(config_id,)))

    def get_export_configurations(self):
        """
        Retrieve all ExportConfigurations held in this db

        :return: a list of all :class:`meteorpi_model.ExportConfiguration` on this server
        """
        sql = (
            'SELECT uid, exportConfigId, exportType, searchString, targetURL, '
            'targetUser, targetPassword, exportName, description, active '
            'FROM archive_exportConfig ORDER BY uid DESC')
        return list(self.generators.export_configuration_generator(sql=sql, sql_args=[]))

    def create_or_update_export_configuration(self, export_config):
        """
        Create a new file export configuration or update an existing one

        :param ExportConfiguration export_config:
            a :class:`meteorpi_model.ExportConfiguration` containing the specification for the export. If this
            doesn't include a 'config_id' field it will be inserted as a new record in the database and the field will
            be populated, updating the supplied object. If it does exist already this will update the other properties
            in the database to match the supplied object.
        :returns:
            The supplied :class:`meteorpi_model.ExportConfiguration` as stored in the DB. This is guaranteed to have
            its 'config_id' string field defined.
        """
        search_string = json.dumps(obj=export_config.search.as_dict())
        user_id = export_config.user_id
        password = export_config.password
        target_url = export_config.target_url
        enabled = export_config.enabled
        name = export_config.name
        description = export_config.description
        export_type = export_config.type
        if export_config.config_id is not None:
            # Update existing record
            self.con.execute(
                    'UPDATE archive_exportConfig c '
                    'SET c.searchString = %s, c.targetUrl = %s, c.targetUser = %s, c.targetPassword = %s, '
                    'c.exportName = %s, c.description = %s, c.active = %s, c.exportType = %s '
                    'WHERE c.exportConfigId = %s',
                    (search_string, target_url, user_id, password, name, description, enabled, export_type,
                     export_config.config_id))
        else:
            # Create new record and add the ID into the supplied config
            item_id = mp.getHash(mp.now(), name, export_type)
            self.con.execute(
                    'INSERT INTO archive_exportConfig '
                    '(searchString, targetUrl, targetUser, targetPassword, '
                    'exportName, description, active, exportType, exportConfigId) '
                    'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ',
                    (search_string, target_url, user_id, password,
                     name, description, enabled, export_type, item_id))
            export_config.config_id = item_id
        return export_config

    def delete_export_configuration(self, config_id):
        """
        Delete a file export configuration by external UUID

        :param string config_id: the ID of the config to delete
        """
        self.con.execute('DELETE FROM archive_exportConfig WHERE exportConfigId = %s;', (config_id,))

    def mark_entities_to_export(self, export_config):
        """
        Apply the specified :class:`meteorpi_model.ExportConfiguration` to the database, running its contained query and
        creating rows in t_eventExport or t_fileExport for matching entities.

        :param ExportConfiguration export_config:
            An instance of :class:`meteorpi_model.ExportConfiguration` to apply.
        :returns:
            The integer number of rows added to the export tables
        """
        # Retrieve the internal ID of the export configuration, failing if it hasn't been stored
        self.con.execute('SELECT uid FROM archive_exportConfig WHERE exportConfigID = %s;',
                         (export_config.config_id,))
        export_config_id = self.con.fetchall()
        if len(export_config_id) < 1:
            raise ValueError("Attempt to run export on ExportConfiguration not in database")
        export_config_id = export_config_id[0]['internalId']

        # If the export is inactive then do nothing
        if not export_config.enabled:
            return 0

        # Track the number of rows created, return it later
        rows_created = 0

        # Handle ObservationSearch
        if isinstance(export_config.search, mp.ObservationSearch):
            # Create a deep copy of the search and set the properties required when creating exports
            search = mp.ObservationSearch.from_dict(export_config.search.as_dict())
            search.exclude_export_to = export_config.config_id
            b = search_observations_sql_builder(search)

            self.con.execute(b.get_select_sql(columns='o.uid'), b.sql_args)
            for result in self.con.fetchall():
                self.con.execute('INSERT INTO archive_observationExport (observationId, exportConfig, exportState) '
                                 'VALUES (%s,%s,%s)', (result['uid'], export_config_id, 1))
                rows_created += 1

        # Handle ObservatoryMetadataSearch
        elif isinstance(export_config.search, mp.ObservatoryMetadataSearch):
            # Create a deep copy of the search and set the properties required when creating exports
            search = mp.ObservatoryMetadataSearch.from_dict(export_config.search.as_dict())
            search.exclude_export_to = export_config.config_id
            b = search_metadata_sql_builder(search)

            self.con.execute(b.get_select_sql(columns='f.internalID'), b.sql_args)
            for result in self.con.fetchall():
                self.con.execute('INSERT INTO archive_metadataExport (metadataId, exportConfig, exportState) '
                                 'VALUES (%s,%s,%s)', (result['uid'], export_config_id, 1))
                rows_created += 1

        # Complain if it's anything other than these two (nothing should be at the moment but we might introduce
        # more search types in the future
        else:
            raise ValueError("Unknown search type")
        return rows_created

    def get_next_entity_to_export(self):
        """
        Examines the archive_observationExport and archive_metadataExport tables, and builds
        either a :class:`meteorpi_db.ObservationExportTask` or a :class:`meteorpi_db.MetadataExportTask` as appropriate. These
        task objects can be used to retrieve the underlying entity and export configuration, and to update the
        completion state or push the timestamp into the future, deferring evaluation of the task until later.

        :returns:
            Either None, if no exports are available, or an object, depending on whether an observation or metadata item is next in the queue to export.
        """
        entity_type = None
        config_id = None
        entity_id = None
        timestamp = None
        config_internal_id = None
        entity_internal_id = None
        status = None
        target_url = None
        target_user = None
        target_password = None
        current_timestamp = mp.utc_datetime_to_milliseconds(mp.now())
        with closing(self.con.cursor()) as cur:
            # Try to retrieve the earliest record in t_eventExport
            cur.execute('SELECT c.exportConfigID, e.eventID, x.exportTime, x.eventID, x.exportConfig, x.exportState, '
                        'c.targetURL, c.targetUser, c.targetPassword '
                        'FROM t_eventExport x, t_exportConfig C, t_event e '
                        'WHERE x.exportConfig = c.internalID AND x.eventID = e.internalID '
                        'AND c.active = 1 '
                        'AND x.exportState > 0 '
                        'AND x.exportTime <= (?)'
                        'ORDER BY x.exportTime ASC, x.eventID ASC '
                        'ROWS 1', (current_timestamp,))
            row = cur.fetchone()
            if row is not None:
                entity_type = 'event'
                config_id = uuid.UUID(bytes=row[0])
                entity_id = uuid.UUID(bytes=row[1])
                timestamp = row[2]
                entity_internal_id = row[3]
                config_internal_id = row[4]
                status = row[5]
                target_url = row[6]
                target_user = row[7]
                target_password = row[8]
            # Similar operation for t_fileExport
            cur.execute('SELECT c.exportConfigID, f.fileID, x.exportTime, x.fileID, x.exportConfig, x.exportState, '
                        'c.targetURL, c.targetUser, c.targetPassword '
                        'FROM t_fileExport x, t_exportConfig c, t_file f '
                        'WHERE x.exportConfig = C.internalID AND x.fileID = f.internalID '
                        'AND c.active = 1 '
                        'AND x.exportState > 0 '
                        'AND x.exportTime <= (?)'
                        'ORDER BY x.exportTime ASC, x.fileID ASC '
                        'ROWS 1', (current_timestamp,))
            row = cur.fetchone()
            if row is not None:
                if timestamp is None or row[2] < timestamp:
                    entity_type = 'file'
                    config_id = uuid.UUID(bytes=row[0])
                    entity_id = uuid.UUID(bytes=row[1])
                    timestamp = row[2]
                    entity_internal_id = row[3]
                    config_internal_id = row[4]
                    status = row[5]
                    target_url = row[6]
                    target_user = row[7]
                    target_password = row[8]
        if entity_type is None:
            return None
        elif entity_type == 'file':
            return FileExportTask(db=self, config_id=config_id, config_internal_id=config_internal_id,
                                  file_id=entity_id, file_internal_id=entity_internal_id, timestamp=timestamp,
                                  status=status, target_url=target_url, target_user=target_user,
                                  target_password=target_password)
        elif entity_type == 'event':
            return EventExportTask(db=self, config_id=config_id, config_internal_id=config_internal_id,
                                   event_id=entity_id, event_internal_id=entity_internal_id, timestamp=timestamp,
                                   status=status, target_url=target_url, target_user=target_user,
                                   target_password=target_password)
        else:
            raise ValueError("Unknown entity type, should never see this!")

    def import_event(self, event, user_id):
        """
        Functionality used by the import API, pulls in a :class:`meteorpi_model.Event` including its pre-existing links
        to camera status and UUID. Do not use this to register a new event, it is only for use by the import system,
        this system ensures that all pre-requisites (files, camera status etc) are in place. If you use it outside of
        this context you will break your database. Don't.

        :param Event event:
            The :class:`meteorpi_model.Event` instance to import
        :param string user_id:
            The user_id of the importing :class:`meteorpi_model.User`
        :internal:
        """
        if self.has_event_id(event.event_id):
            return
        status_id = self._get_camera_status_id(camera_id=event.camera_id, time=event.event_time)
        if status_id is None:
            raise ValueError(
                    'No status defined for camera id {0} at time {1}!'.format(event.camera_id, event.event_time))
        if status_id['status_id'].hex != event.status_id.hex:
            raise ValueError('Existing status and supplied status IDs must be equal')
        day_and_offset = mp.get_day_and_offset(event.event_time)
        # Import the file records first
        file_internal_ids = list(self.import_file_record(file_record=f, user_id=user_id) for f in event.file_records)
        # Import the event
        with closing(self.con.trans()) as transaction:
            with closing(transaction.cursor()) as cur:
                cur.execute(
                        'INSERT INTO t_event (cameraID, eventTime, eventOffset, eventType, '
                        'statusID, eventID) '
                        'VALUES (?, ?, ?, ?, ?, ?) '
                        'RETURNING internalID, eventID, eventTime',
                        (event.camera_id,
                         mp.utc_datetime_to_milliseconds(event.event_time),
                         day_and_offset['seconds'],
                         str(event.event_type),
                         status_id['internal_id'],
                         event.event_id.bytes))
                ids = cur.fetchone()
                event_internal_id = ids[0]
                # Insert into event import table
                cur.execute('INSERT INTO t_eventImport (eventID, importUser, importTime) VALUES (?, ?, ?)',
                            (event_internal_id, user_id, mp.utc_datetime_to_milliseconds(mp.now())))
                for file_record_index, file_internal_id in enumerate(file_internal_ids):
                    cur.execute(
                            'INSERT INTO t_event_to_file '
                            '(fileID, eventID, sequenceNumber) '
                            'VALUES (?, ?, ?)',
                            (file_internal_id,
                             event_internal_id,
                             file_record_index))
                for meta_index, meta in enumerate(event.meta):
                    cur.execute(
                            'INSERT INTO t_eventMeta '
                            '(eventID, metaKey, stringValue, floatValue, dateValue, metaIndex) '
                            'VALUES (?, ?, ?, ?, ?, ?)',
                            (event_internal_id,
                             str(meta.key),
                             meta.string_value(),
                             meta.float_value(),
                             mp.utc_datetime_to_milliseconds(meta.date_value()),
                             meta_index))
            transaction.commit()

    def import_file_record(self, file_record, user_id):
        """
        Used by the import system to import a previously instantiated and named :class:`meteorpi_model.FileRecord`. Do
        not use this method outside of the import system, this system will ensure that any pre-requisite status or file
        data is in place, using this method directly will certainly break your database.

        :param FileRecord file_record:
            The :class:`meteorpi_model.FileRecord` to import
        :param string user_id:
            The user_id of the importing :class:`meteorpi_model.User`
        :return:
            The integer internal ID of the imported record, used when importing events to create the link tables without
            additional database queries.
        :internal:
        """
        if self.has_file_id(file_record.file_id):
            return
        if not path.exists(self.file_path_for_id(file_record.file_id)):
            raise ValueError('Must get the binary file before importing FileRecord')
        status_id = self._get_camera_status_id(camera_id=file_record.camera_id, time=file_record.file_time)
        if status_id is None:
            raise ValueError(
                    'No status defined for camera id {0} at time {1}!'.format(file_record.camera_id,
                                                                              file_record.file_time))
        if status_id['status_id'].hex != file_record.status_id.hex:
            raise ValueError('Existing status and supplied status IDs must be equal')
        day_and_offset = mp.get_day_and_offset(file_record.file_time)
        with closing(self.con.trans()) as transaction:
            with closing(transaction.cursor()) as cur:
                cur.execute(
                        'INSERT INTO t_file (cameraID, mimeType, '
                        'semanticType, fileTime, fileOffset, fileSize, statusID, fileName, fileID, md5Hex) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '
                        'RETURNING internalID, fileID, fileTime',
                        (file_record.camera_id,
                         file_record.mime_type,
                         str(file_record.semantic_type),
                         mp.utc_datetime_to_milliseconds(file_record.file_time),
                         day_and_offset['seconds'],
                         file_record.file_size,
                         status_id['internal_id'],
                         file_record.file_name,
                         file_record.file_id.bytes,
                         file_record.md5))
                row = cur.fetchonemap()
                # Retrieve the internal ID of the file row to link fileMeta if required
                file_internal_id = row['internalID']
                # Insert into file import table
                cur.execute('INSERT INTO t_fileImport (fileID, importUser, importTime) VALUES (?, ?, ?)',
                            (file_internal_id, user_id, mp.utc_datetime_to_milliseconds(mp.now())))
                for file_meta_index, file_meta in enumerate(file_record.meta):
                    cur.execute(
                            'INSERT INTO t_fileMeta '
                            '(fileID, metaKey, stringValue, floatValue, dateValue, metaIndex) '
                            'VALUES (?, ?, ?, ?, ?, ?)',
                            (file_internal_id,
                             str(file_meta.key),
                             file_meta.string_value(),
                             file_meta.float_value(),
                             mp.utc_datetime_to_milliseconds(file_meta.date_value()),
                             file_meta_index))
            transaction.commit()
        return file_internal_id

    def import_camera_status(self, status):
        """
        Import a new camera status block, used by the import server - do not use this for local status changes, it
        doesn't update high water marks and will not execute any kind of roll-back. Clears the status cache, as camera
        status instances are somewhat dynamically generated based on other instances, most particularly for their time
        ranges.

        :param status:
            The new camera status block to import, this must be pre-populated with all required fields.
        """
        with closing(self.con.trans()) as transaction:
            with closing(transaction.cursor()) as cur:
                # Insert the new status into the database
                cur.execute(
                        'INSERT INTO t_cameraStatus (statusID, cameraID, validFrom, '
                        'softwareVersion, orientationAltitude, orientationAzimuth, '
                        'orientationRotation, orientationError, widthOfField, locationLatitude, locationLongitude, '
                        'locationGPS, lens, sensor, instURL, instName, locationError) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '
                        'RETURNING internalID',
                        (status.status_id.bytes,
                         status.camera_id,
                         mp.utc_datetime_to_milliseconds(status.valid_from),
                         SOFTWARE_VERSION,
                         status.orientation.altitude,
                         status.orientation.azimuth,
                         status.orientation.rotation,
                         status.orientation.error,
                         status.orientation.width_of_field,
                         status.location.latitude,
                         status.location.longitude,
                         status.location.gps,
                         status.lens,
                         status.sensor,
                         status.inst_url,
                         status.inst_name,
                         status.location.error))
                # Retrieve the newly created internal ID for the status block, use this to
                # insert visible regions
                status_internal_id = cur.fetchone()[0]
                for region_index, region in enumerate(status.regions):
                    for point_index, point in enumerate(region):
                        cur.execute(
                                'INSERT INTO t_visibleRegions (cameraStatusID, '
                                'region, pointOrder, x, y) VALUES (?,?,?,?,?)',
                                (status_internal_id,
                                 region_index,
                                 point_index,
                                 point['x'],
                                 point['y']))
            transaction.commit()
        self.generators.cache_clear(cache='status')

    # Functions relating to high water marks
    def get_hwm_key_id(self, metakey):
        self.con.execute("SELECT uid FROM archive_highWaterMarkTypes WHERE metaKey=%s;", (metakey,))
        results = self.con.fetchall()
        if len(results) < 1:
            self.con.execute("INSERT INTO archive_highWaterMarkTypes (metaKey) VALUES (%s);", (metakey,))
            self.con.execute("SELECT uid FROM archive_highWaterMarkTypes WHERE metaKey=%s;", (metakey,))
            results = self.con.fetchall()
        return results[0]['uid']

    def get_high_water_mark(self, mark_type, camera_name=None):
        """
        Retrieves the high water mark for a given camera, defaulting to the current installation ID

        :param string camera_name:
            The camera ID to check for, or the default installation ID if not specified
        :return:
            A UTC datetime for the high water mark, or None if none was found.
        """
        if camera_name is None:
            camera_name = self.camera_name

        camera = self.get_camera_from_name(camera_name)
        key_id = self.get_metadata_key_id(mark_type)

        self.con.execute('SELECT time FROM archive_highWaterMarks WHERE markType=%s AND observatoryId=%s',
                         (key_id, camera['uid']))
        results = self.con.fetchall()
        if len(results) > 0:
            return results[0]['time']
        return None

    def set_high_water_mark(self, mark_type, time, camera_name=None, ):
        if camera_name is None:
            camera_name = self.camera_name

        camera = self.get_camera_from_name(camera_name)
        key_id = self.get_metadata_key_id(mark_type)

        self.con.execute('DELETE FROM archive_highWaterMarks WHERE markType=%s AND observatoryId=%s',
                         (key_id, camera['uid']))
        self.con.execute('INSERT INTO archive_highWaterMarks (markType, observatoryId, time) VALUES (%s,%s,%s);',
                         (key_id, camera['uid'], time))

    def clear_database(self, tmin=None, tmax=None, camera_names=None):

        if camera_names is None:
            camera_names = self.get_camera_names()
        if isinstance(camera_names, basestring):
            camera_names = [camera_names]

        for camera_name in camera_names:
            camera = self.get_camera_from_name(camera_name)
            # Purge tables - other tables are deleted by foreign key cascades from these ones.
            self.con.execute('SELECT publicId FROM archive_observations '
                             'WHERE obsTime>%s AND obsTime<%s AND observatory=%s',
                             (tmin, tmax, camera['uid']))
            for obs in self.con.fetchall():
                self.delete_observation(obs['publicId'])
            self.con.execute('DELETE FROM archive_metadata WHERE time>%s AND time<%s AND observatory=%s',
                             (tmin, tmax, camera['uid']))
