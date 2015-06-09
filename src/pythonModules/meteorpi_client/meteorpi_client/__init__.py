import time
import json
import urllib

import types
import requests
from yaml import safe_load
import meteorpi_model as model


class MeteorClient():
    """Client for the MeteorPi HTTP API"""

    def __init__(self, base_url):
        """Create a new API client, pointing at the server defined by base_url"""
        self.base_url = base_url

    def list_cameras(self):
        """Returns a list of camera IDs currently active in this installation"""
        response = requests.get(self.base_url + '/cameras').text
        return safe_load(response)['cameras']

    def get_camera_status(self, camera_id, time=None):
        """Get the status of a given camera, optionally at a supplied time.
        If the time is not specified it will default to 'now'. If the camera
        can't be found, or it has no status at the specified time, this
        method will return None."""
        if time is None:
            response = requests.get(
                self.base_url + '/cameras/{0}/status'.format(camera_id))
        else:
            response = requests.get(
                self.base_url + '/cameras/{0}/status/{1}'.format(camera_id, _datetime_string(time)))
        if response.status_code == 200:
            d = safe_load(response.text)
            if 'status' in d:
                return model.CameraStatus.from_dict(d['status'])
        return None

    def search_events(self, search=None):
        """Search for events using an EventSearch object"""
        if search is None:
            search = model.EventSearch()
        search_string = urllib.quote_plus(json.dumps(obj=search.as_dict(), separators=(',', ':')))
        response = requests.get(self.base_url + '/events/{0}'.format(search_string))
        response_object = safe_load(response.text)
        event_dicts = response_object['events']
        event_count = response_object['count']
        return {'count': event_count,
                'events': list((self._augment_event_files(e) for e in (model.Event.from_dict(d) for d in event_dicts)))}

    def search_files(self, search=None):
        if search is None:
            search = model.FileRecordSearch()
        search_string = urllib.quote_plus(json.dumps(obj=search.as_dict(), separators=(',', ':')))
        response = requests.get(self.base_url + '/files/{0}'.format(search_string))
        response_object = safe_load(response.text)
        file_dicts = response_object['files']
        file_count = response_object['count']
        return {'count': file_count,
                'files': list((self._augment_file(f) for f in (model.FileRecord.from_dict(d) for d in file_dicts)))}

    def _augment_file(self, f):
        """Augment a FileRecord with methods to get the data URL and to download, returning the updated file for use
        in generator functions"""
        # Placeholder
        def get_url(target):
            if target.file_size is None:
                return None
            return self.base_url + '/files/content/{0}/{1}'.format(target.file_id.hex, target.file_name)

        f.get_url = types.MethodType(get_url, f)

        def download_to(target, file_name):
            url = target.get_url()
            r = requests.get(url, stream=True)
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
            return file_name

        f.download_to = types.MethodType(download_to, f)
        return f

    def _augment_event_files(self, e):
        """Augment all the file records in an event"""
        e.file_records = list(self._augment_file(f) for f in e.file_records)
        return e


def _datetime_string(t):
    """Builds a string representation of a timestamp, used for URL components"""
    if t is not None:
        return str(time.mktime((t.year, t.month, t.day,
                                t.hour, t.minute, t.second,
                                -1, -1, -1)) + t.microsecond / 1e6)
    raise ValueError("Time t cannot be None")
