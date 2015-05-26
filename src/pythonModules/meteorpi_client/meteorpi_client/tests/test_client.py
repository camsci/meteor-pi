from unittest import TestCase

import meteorpi_server
import meteorpi_fdb.testing.dummy_data as dummy
import meteorpi_client as client
import meteorpi_model as model


class TestClient(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestClient, self).__init__(*args, **kwargs)
        self.server = meteorpi_server.MeteorServer()
        self.client = client.MeteorClient(base_url=self.server.base_url())
        self.longMessage = True

    def setUp(self):
        """Clear the database and populate it with example contents"""
        self.dummy_helper = dummy.setup_dummy_data(self.server.db, clear=True)
        # Start the server, returns a function
        # which can be used to stop it afterwards
        self.stop = self.server.start_non_blocking()

    def tearDown(self):
        """Stop the server"""
        self.stop()
        self.server = None

    def test_list_cameras(self):
        cameras_from_db = self.server.db.get_cameras()
        cameras_from_client = self.client.list_cameras()
        self.assertSequenceEqual(cameras_from_db, cameras_from_client)

    def test_get_camera_status(self):
        # Test acquiring status with no time, should use the current time.
        status_from_db_now = self.server.db.get_camera_status(camera_id=dummy.CAMERA_1)
        status_from_client_now = self.client.get_camera_status(camera_id=dummy.CAMERA_1)
        self.assertDictEqual(status_from_db_now.as_dict(), status_from_client_now.as_dict())
        # Test that an unknown camera results in a status of None (logs will show a 404 from the server)
        self.assertEquals(self.client.get_camera_status(camera_id='nosuchcamera'), None)
        for t in range(0, 30):
            # At time 0 there shouldn't be a status and both should return None
            status_from_db = self.server.db.get_camera_status(camera_id=dummy.CAMERA_1, time=dummy.make_time(t))
            status_from_client = self.client.get_camera_status(camera_id=dummy.CAMERA_1, time=dummy.make_time(t))
            if status_from_db is not None and status_from_client is not None:
                self.assertDictEqual(status_from_db.as_dict(), status_from_client.as_dict())
            else:
                self.assertEquals(status_from_db, status_from_client)

    def test_search_events(self):
        # Run all the searches in the list below, checking that results from the db and the client match
        searches = [
            {'search': model.EventSearch(),
             'expect': 'e0,e1,e2,e3,e4'},
            {'search': model.EventSearch(camera_ids=dummy.CAMERA_1),
             'expect': 'e0,e1'},
            {'search': model.EventSearch(camera_ids=[dummy.CAMERA_1, dummy.CAMERA_2]),
             'expect': 'e0,e1,e2,e3,e4'},
            # Test that the edge case where the time equals an event doesn't include it (e1 in this case)
            {'search': model.EventSearch(after=dummy.make_time(30)),
             'expect': 'e4'},
            {'search': model.EventSearch(before=dummy.make_time(30)),
             'expect': 'e0,e2,e3'},
            # Should now include e1 as e1 has time set to dummy.make_time(30)
            {'search': model.EventSearch(before=dummy.make_time(31)),
             'expect': 'e0,e1,e2,e3'},
            # Test whether we can use both after and before
            {'search': model.EventSearch(before=dummy.make_time(31), after=dummy.make_time(29)),
             'expect': 'e1'},
        ]
        for search in searches:
            events_from_db = self.server.db.search_events(search['search'])
            events_from_client = self.client.search_events(search['search'])
            # Check that the results are the same from the API client and the DB directly
            self.assertSequenceEqual(
                list(x.as_dict() for x in events_from_db),
                list(x.as_dict() for x in events_from_client))
            # Check that the results are as expected
            self.assertEquals(search['expect'], self.dummy_helper.seq_to_string(events_from_client),
                              'from {0}'.format(search['search']))

    def test_search_files(self):
        # As for the event search
        searches = [
            {'search': model.FileRecordSearch(),
             'expect': 'e0:f0,e0:f1,e1:f0,e1:f1,e1:f2,e1:f3,e2:f0,e2:f1,'
                       'e3:f0,e3:f1,e3:f2,e4:f0,e4:f1,e4:f2,e4:f3,e4:f4,e4:f5,f10,f11,f6,f7,f8,f9'},
            {'search': model.FileRecordSearch(camera_ids=dummy.CAMERA_1),
             'expect': 'e0:f0,e0:f1,e1:f0,e1:f1,e1:f2,e1:f3,f10,f11,f6,f7,f8,f9'},
            {'search': model.FileRecordSearch(exclude_events=True),
             'expect': 'f10,f11,f6,f7,f8,f9'},
            {'search': model.FileRecordSearch(exclude_events=True, latest=True, camera_ids=dummy.CAMERA_1),
             'expect': 'f7'},
            {'search': model.FileRecordSearch(camera_ids=dummy.CAMERA_1,
                                              meta_constraints=[model.FileMetaConstraint(constraint_type='less',
                                                                                         key=model.NSString(
                                                                                             'number_key'), value=4)]),
             'expect': 'f6'},
            {'search': model.FileRecordSearch(camera_ids=dummy.CAMERA_1,
                                              meta_constraints=[model.FileMetaConstraint(constraint_type='greater',
                                                                                         key=model.NSString(
                                                                                             'number_key'), value=4)]),
             'expect': 'f8,f9'},
            {'search': model.FileRecordSearch(camera_ids=dummy.CAMERA_1,
                                              meta_constraints=[
                                                  model.FileMetaConstraint(constraint_type='number_equals',
                                                                           key=model.NSString(
                                                                               'number_key'), value=10.002)]),
             'expect': 'f9'},
            {'search': model.FileRecordSearch(camera_ids=dummy.CAMERA_1,
                                              meta_constraints=[
                                                  model.FileMetaConstraint(constraint_type='less',
                                                                           key=model.NSString(
                                                                               'number_key'), value=6),
                                                  model.FileMetaConstraint(constraint_type='greater',
                                                                           key=model.NSString(
                                                                               'number_key'), value=4)]),
             'expect': 'f8'},
            {'search': model.FileRecordSearch(camera_ids=dummy.CAMERA_1,
                                              meta_constraints=[
                                                  model.FileMetaConstraint(constraint_type='before',
                                                                           key=model.NSString(
                                                                               'date_key'),
                                                                           value=dummy.make_time(14))]),
             'expect': 'f10,f6'},
            {'search': model.FileRecordSearch(camera_ids=dummy.CAMERA_1,
                                              meta_constraints=[
                                                  model.FileMetaConstraint(constraint_type='after',
                                                                           key=model.NSString(
                                                                               'date_key'),
                                                                           value=dummy.make_time(14))]),
             'expect': 'f8'},
        ]
        for search in searches:
            files_from_db = self.server.db.search_files(search['search'])
            files_from_client = self.client.search_files(search['search'])
            # Check that the results are the same from the API client and the DB directly
            self.assertSequenceEqual(
                list(x.as_dict() for x in files_from_db),
                list(x.as_dict() for x in files_from_client))
            # Check that the results are as expected
            self.assertEquals(search['expect'], self.dummy_helper.seq_to_string(files_from_client),
                              'from {0}'.format(search['search']))
