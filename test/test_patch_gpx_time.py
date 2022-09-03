import unittest
from datetime import datetime, timedelta

import gpxpy.gpx
import patch_gpx_time
import gpxpy as gp
import os
import numpy as np
import matplotlib.pyplot as plt


def points_to_gpx(
        name: str,
        points: np.ndarray,
        points_time: np.ndarray,
        base_time: datetime) -> gp.gpx.GPX:
    # update the points in gfp_query_copy
    gpx = gp.gpx.GPX()
    gpx.tracks = [gp.gpx.GPXTrack()]
    gpx.tracks[0].segments = [gp.gpx.GPXTrackSegment()]
    gpx.name = name
    track_points = []
    for ind_pt in range(0, points.shape[0]):
        time = base_time + timedelta(seconds=float(points_time[ind_pt, 0]))
        track_points.append(gp.gpx.GPXTrackPoint(latitude=points[ind_pt, 0], longitude=points[ind_pt, 1], time=time))
    # slap this into the GPX
    gpx.tracks[0].segments[0].points = track_points
    gpx.tracks[0].name = name
    return gpx


def gen_gpx():
    # for the query, go 60 seconds, stop for the gap, then go another 60 seconds
    time_interval_seconds = 2
    speed_degrees_per_second = 0.01
    time_start = datetime.now()
    start_lat_lon = np.zeros(shape=(1, 2))
    speed = np.ones(shape=(1, 2)) * speed_degrees_per_second
    t_query = np.concatenate((np.arange(0, 60, time_interval_seconds), np.arange(60+44, 60+44+60, time_interval_seconds)))
    t_template = np.arange(-36, 130, time_interval_seconds)
    t_query = np.expand_dims(t_query, axis=1)
    t_template = np.expand_dims(t_template, axis=1)
    query_lat_lon = t_query * speed + start_lat_lon
    # tweak the template a bit so I can distinguish the two
    template_lat_lon = t_template * speed + start_lat_lon
    plt.figure()
    plt.plot(query_lat_lon[:, 0], query_lat_lon[:, 1], 'r+')
    plt.title('query')
    plt.show()
    plt.figure()
    plt.plot(template_lat_lon[:, 0], template_lat_lon[:, 1], 'go')
    plt.title('template')
    plt.show()
    # ok. we have timestamps (in seconds) and lat,lon
    # to GPX!
    gpx_query = points_to_gpx('query', query_lat_lon, t_query, time_start)
    gpx_template = points_to_gpx('template', template_lat_lon, t_template, time_start)
    return gpx_query, gpx_template


class MyTestCase(unittest.TestCase):
    def test_gen(self):
        q, t = gen_gpx()
        query_points = patch_gpx_time.gpx_to_lat_lon(q.tracks[0].segments[0].points)
        template_points = patch_gpx_time.gpx_to_lat_lon(t.tracks[0].segments[0].points)
        plt.figure()
        plt.plot(query_points[:, 0], query_points[:, 1], 'r+')
        plt.title('query')
        plt.show()
        plt.figure()
        plt.plot(template_points[:, 0], template_points[:, 1], 'r+')
        plt.title('template')
        plt.show()

    def test_generated(self):
        q, t = gen_gpx()
        fixed = patch_gpx_time.patch_gpx(q, t, max_time_gap_seconds=30)
        fixed_points = patch_gpx_time.gpx_to_lat_lon(fixed.tracks[0].segments[0].points)
        plt.figure()
        plt.plot(fixed_points[:, 0], fixed_points[:, 1], 'r+')
        plt.title('fixed')
        plt.show()
        fixed_points_time, fixed_points_start_time = \
            patch_gpx_time.gpx_to_time_seconds(fixed.tracks[0].segments[0].points)
        #print(fixed_points_time)
        print(fixed_points_start_time)

        query_points_time, query_points_start_time = \
            patch_gpx_time.gpx_to_time_seconds(q.tracks[0].segments[0].points)
        #print(query_points_time)
        print(query_points_start_time)

        template_points_time, template_points_start_time = \
            patch_gpx_time.gpx_to_time_seconds(t.tracks[0].segments[0].points)
        #print(template_points_time)
        print(template_points_start_time)

    def test_diff_seconds(self):
        time1 = datetime.now()
        time2 = time1 + timedelta(seconds=10)
        td = patch_gpx_time.diff_seconds(time2, time1)
        print(td)
        self.assertEqual(td, 10)
        td = patch_gpx_time.diff_seconds(time1, time2)
        print(td)
        self.assertEqual(td, -10)

    def test_point(self):
        # what is this thing (debugger)?
        pt = gp.gpx.GPXTrackPoint()
        pass

    def test_gpx_pair(self, folium_output=True):
        # process the gpx files from the Calero ride
        # also generates plots for the README.md
        qfile = '../data/Calero_Mayfair_ranch_trail.gpx'
        tfile = '../data/Calero_big_ride_2.gpx'
        ofile = 'calero_patched_time.gpx'
        gpx = patch_gpx_time.patch_gpx_file(qfile, tfile, ofile, 30)
        self.assertTrue(os.path.exists(ofile))
        gf = open(qfile, 'r')
        gfp_query = gp.parse(gf)
        gf.close()
        gf = open(tfile, 'r')
        gfp_template = gp.parse(gf)
        gf.close()
        gf = open(ofile, 'r')
        gfp_output = gp.parse(gf)
        gf.close()
        # gpx and the output should be quite similar!
        print('output points:', len(gpx.tracks[0].segments[0].points))
        self.assertEqual(len(gpx.tracks[0].segments[0].points), len(gfp_output.tracks[0].segments[0].points))
        # todo: more checks!
        # output point count should be between the template and the query
        query_points = len(gfp_query.tracks[0].segments[0].points)
        template_points = len(gfp_template.tracks[0].segments[0].points)
        print('query points:', query_points)
        print('template points:', template_points)
        min_points = min(query_points, template_points)
        max_points = max(query_points, template_points)
        self.assertGreaterEqual(len(gpx.tracks[0].segments[0].points), min_points)
        self.assertLessEqual(len(gpx.tracks[0].segments[0].points), max_points)


if __name__ == '__main__':
    unittest.main()
