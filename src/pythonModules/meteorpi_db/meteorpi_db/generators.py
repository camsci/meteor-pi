# generators.py

# -------------------------------------------------
# Copyright 2016 Cambridge Science Centre.

# This file is part of Meteor Pi.

# Meteor Pi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Meteor Pi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Meteor Pi.  If not, see <http://www.gnu.org/licenses/>.
# -------------------------------------------------

# Helper functions for generating Meteor Pi objects from SQL query results

import json
import meteorpi_model as mp


def first_from_generator(generator):
    """Pull the first value from a generator and return it, closing the generator

    :param generator:
        A generator, this will be mapped onto a list and the first item extracted.
    :return:
        None if there are no items, or the first item otherwise.
    :internal:
    """
    try:
        result = next(generator)
    except StopIteration:
        result = None
    finally:
        generator.close()
    return result


def first_non_null(values):
    """
    Retrieve the first, non-null item in the specified list

    :param values:
        a list of values from which the first non-null is returned
    :return:
        the first non-null item
    :raises:
        ValueError if there isn't any such item in the list.
    """
    for item in values:
        if item is not None:
            return item
    raise ValueError("No non-null item in supplied list.")


class MeteorDatabaseGenerators(object):
    """
    Generator functions used to retrieve, and cache, items from the database.
    """

    def __init__(self, db, con):
        self.con = con
        self.db = db

    def file_generator(self, sql, sql_args):
        """Generator for FileRecord

        :param sql:
            A SQL statement which must return rows describing files.
        :param sql_args:
            Any variables required to populate the query provided in 'sql'
        :return:
            A generator which produces FileRecord instances from the supplied SQL, closing any opened cursors on
            completion.
        """

        self.con.execute(sql, sql_args)
        results = self.con.fetchall()
        output = []
        for result in results:
            file_record = mp.FileRecord(obstory_id=result['obstory_id'], obstory_name=result['obstory_name'],
                                        observation_id=result['observationId'],
                                        repository_fname=result['repositoryFname'],
                                        file_time=result['fileTime'], file_size=result['fileSize'],
                                        file_name=result['fileName'], mime_type=result['mimeType'],
                                        file_md5=result['fileMD5'],
                                        semantic_type=result['semanticType'])

            # Look up observation metadata
            sql = """SELECT f.metaKey, stringValue, floatValue
FROM archive_metadata m
INNER JOIN archive_metadataFields f ON m.fieldId=f.uid
WHERE m.fileId=%s
"""
            self.con.execute(sql, (result['uid'],))
            for item in self.con.fetchall():
                value = first_non_null([item['stringValue'], item['floatValue']])
                file_record.meta.append(mp.Meta(item['metaKey'], value))

            output.append(file_record)
        return output

    def observation_generator(self, sql, sql_args):
        """Generator for Observation

        :param sql:
            A SQL statement which must return rows describing observations
        :param sql_args:
            Any variables required to populate the query provided in 'sql'
        :return:
            A generator which produces Event instances from the supplied SQL, closing any opened cursors on completion.
        """

        self.con.execute(sql, sql_args)
        results = self.con.fetchall()
        output = []
        for result in results:
            observation = mp.Observation(obstory_id=result['obstory_id'], obstory_name=result['obstory_name'],
                                         obs_time=result['obsTime'], obs_id=result['publicId'],
                                         obs_type=result['obsType'])

            # Look up observation metadata
            sql = """SELECT f.metaKey, stringValue, floatValue
FROM archive_metadata m
INNER JOIN archive_metadataFields f ON m.fieldId=f.uid
WHERE m.observationId=%s
"""
            self.con.execute(sql, (result['uid'],))
            for item in self.con.fetchall():
                value = first_non_null([item['stringValue'], item['floatValue']])
                observation.meta.append(mp.Meta(item['metaKey'], value))

            # Fetch file objects
            sql = "SELECT f.repositoryFname FROM archive_files f WHERE f.observationId=%s"
            self.con.execute(sql, (result['uid'],))
            for item in self.con.fetchall():
                observation.file_records.append(self.db.get_file(item['repositoryFname']))

            # Count votes for observation
            self.con.execute("SELECT COUNT(*) FROM archive_obs_likes WHERE observationId="
                             "(SELECT uid FROM archive_observations WHERE publicId=%s);", (result['publicId'],))
            observation.likes = self.con.fetchone()['COUNT(*)']

            output.append(observation)

        return output

    def obsgroup_generator(self, sql, sql_args):
        """Generator for ObservationGroup

        :param sql:
            A SQL statement which must return rows describing observation groups
        :param sql_args:
            Any variables required to populate the query provided in 'sql'
        :return:
            A generator which produces Event instances from the supplied SQL, closing any opened cursors on completion.
        """

        self.con.execute(sql, sql_args)
        results = self.con.fetchall()
        output = []
        for result in results:
            obs_group = mp.ObservationGroup(group_id=result['publicId'], title=result['title'],
                                            obs_time=result['time'], set_time=result['setAtTime'],
                                            semantic_type=result['semanticType'],
                                            user_id=result['setByUser'])

            # Look up observation group metadata
            sql = """SELECT f.metaKey, stringValue, floatValue
FROM archive_metadata m
INNER JOIN archive_metadataFields f ON m.fieldId=f.uid
WHERE m.groupId=%s
"""
            self.con.execute(sql, (result['uid'],))
            for item in self.con.fetchall():
                value = first_non_null([item['stringValue'], item['floatValue']])
                obs_group.meta.append(mp.Meta(item['metaKey'], value))

            # Fetch observation objects
            sql = """SELECT o.publicId
FROM archive_obs_group_members m
INNER JOIN archive_observations o ON m.observationId=o.uid
WHERE m.groupId=%s
"""
            self.con.execute(sql, (result['uid'],))
            for item in self.con.fetchall():
                obs_group.obs_records.append(self.db.get_observation(item['publicId']))

            output.append(obs_group)

        return output

    def obstory_metadata_generator(self, sql, sql_args):
        """
        Generator for :class:`meteorpi_model.CameraStatus`

        :param sql:
            A SQL statement which must return rows describing obstory metadata
        :param sql_args:
            Any arguments required to populate the query provided in 'sql'
        :return:
            A generator which produces :class:`meteorpi_model.CameraStatus` instances from the supplied SQL, closing
            any opened cursors on completion
        """

        self.con.execute(sql, sql_args)
        results = self.con.fetchall()
        output = []
        for result in results:
            value = ""
            if ('floatValue' in result) and (result['floatValue'] is not None):
                value = result['floatValue']
            if ('stringValue' in result) and (result['stringValue'] is not None):
                value = result['stringValue']
            obs_meta = mp.ObservatoryMetadata(metadata_id=result['metadata_id'], obstory_id=result['obstory_id'],
                                              obstory_name=result['obstory_name'],
                                              obstory_lat=result['obstory_lat'], obstory_lng=result['obstory_lng'],
                                              key=result['metadata_key'], value=value,
                                              metadata_time=result['time'], time_created=result['time_created'],
                                              user_created=result['user_created'])
            output.append(obs_meta)

        return output

    def export_configuration_generator(self, sql, sql_args):
        """
        Generator for :class:`meteorpi_model.ExportConfiguration`

        :param sql:
            A SQL statement which must return rows describing export configurations
        :param sql_args:
            Any variables required to populate the query provided in 'sql'
        :return:
            A generator which produces :class:`meteorpi_model.ExportConfiguration` instances from the supplied SQL,
            closing any opened cursors on completion.
        """

        self.con.execute(sql, sql_args)
        results = self.con.fetchall()
        output = []
        for result in results:
            if result['exportType'] == "observation":
                search = mp.ObservationSearch.from_dict(json.loads(result['searchString']))
            elif result['exportType'] == "file":
                search = mp.FileRecordSearch.from_dict(json.loads(result['searchString']))
            else:
                search = mp.ObservatoryMetadataSearch.from_dict(json.loads(result['searchString']))
            conf = mp.ExportConfiguration(target_url=result['targetURL'], user_id=result['targetUser'],
                                          password=result['targetPassword'], search=search,
                                          name=result['exportName'], description=result['description'],
                                          enabled=result['active'], config_id=result['exportConfigId'])
            output.append(conf)

        return output
