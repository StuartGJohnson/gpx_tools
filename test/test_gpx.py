import unittest
import gpxpy as gp
import numpy as np
import time
import scipy
import matplotlib.pyplot as plt

import edit_gpx
from edit_gpx import gpx_to_points3
import os


class MyTestCase(unittest.TestCase):
    def test_gpx_load(self):
        gf = open('../data/Calero_Mayfair_ranch_trail.gpx', 'r')
        gfp = gp.parse(gf)
        gf.close()
        points = gfp.tracks[0].segments[0].points
        # note that this does not load extensions - like temperatures and heart rates
        # see: https://github.com/tkrajina/gpxpy/issues/119
        self.assertEqual(len(points), 2311)

    def test_gpx_load2(self):
        gf = open('../data/Calero_big_ride_2.gpx', 'r')
        gfp = gp.parse(gf)
        gf.close()
        points = gfp.tracks[0].segments[0].points
        # note that this does not load extensions - like temperatures and heart rates
        # see: https://github.com/tkrajina/gpxpy/issues/119
        self.assertEqual(len(points), 9454)

    def test_gpx_distance_matrix(self, do_plots=False):
        # form the distance matrix required by dtw. This will have size 2311x9454
        gf = open('../data/Calero_Mayfair_ranch_trail.gpx', 'r')
        gfp_query = gp.parse(gf)
        gf.close()
        gf = open('../data/Calero_big_ride_2.gpx', 'r')
        gfp_template = gp.parse(gf)
        gf.close()
        # Hmm, should we assert that each gfp has a single track and segment?
        # Or, perhaps perform the analysis on each track/segment?
        # Do strava gpx tracks ever have more than one track/segment?
        gfp_query_points = gfp_query.tracks[0].segments[0].points
        gfp_template_points = gfp_template.tracks[0].segments[0].points
        len_query = len(gfp_query_points)
        len_template = len(gfp_template_points)
        # unpack gfp into numpy arrays
        t0 = time.time()
        query_points, mean_point = gpx_to_points3(gfp_query_points)
        # this should be ... small
        print(np.mean(query_points, axis=0))
        template_points, _ = gpx_to_points3(gfp_template_points, mean_point)
        t1 = time.time()
        print('conversion time (expect << 1 sec) ', t1-t0)
        t0 = time.time()
        dist_mat = scipy.spatial.distance.cdist(query_points, template_points, metric='euclidean')
        t1 = time.time()
        # Note the distance matrix can take a long time when not using cdist!
        print('distance_matrix time (expect ~ 1 sec)', t1 - t0)
        self.assertTrue(np.min(dist_mat) >= 0.0)
        if do_plots:
            plt.figure()
            plt.imshow(dist_mat/np.max(dist_mat))
            plt.title('distance matrix')
            plt.ylabel('query index')
            plt.xlabel('template index')
            plt.show()
        # surprisingly, this route only spans about 6+km as the
        # crow flies
        self.assertTrue(np.abs(np.max(dist_mat)-6342) < 1.0)
        print(np.max(dist_mat))

    def test_gpx_dtw(self):
        qfile = '../data/Calero_Mayfair_ranch_trail.gpx'
        tfile = '../data/Calero_big_ride_2.gpx'
        ofile = 'calero_fixed.gpx'
        gpx = edit_gpx.edit_gpx(qfile, tfile, ofile, do_plots=False, folium_output=False)
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
        # output point count should be greater than the query but less than the template - in this case
        print('query points:', len(gfp_query.tracks[0].segments[0].points))
        print('template points:', len(gfp_template.tracks[0].segments[0].points))
        self.assertGreater(len(gpx.tracks[0].segments[0].points), len(gfp_query.tracks[0].segments[0].points))
        self.assertLess(len(gpx.tracks[0].segments[0].points), len(gfp_template.tracks[0].segments[0].points))
        # todo: more checks!


if __name__ == '__main__':
    unittest.main()
