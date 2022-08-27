import unittest
import numpy as np
import dtw
import matplotlib.pyplot as plt
import skimage.measure as measure
import edit_gpx
import scipy.stats as sci_stats
import folium

def gen_2d(len_pts=100):
    # a full 2pi
    len_pts = 100
    idx_query = np.linspace(0, 2 * np.pi, num=len_pts)
    query_y = np.sin(idx_query) + np.random.uniform(size=len_pts) / 10.0
    query_x = np.cos(idx_query) + np.random.uniform(size=len_pts) / 10.0
    query = np.zeros(shape=(len_pts, 2))
    query[:, 0] = query_x
    query[:, 1] = query_y

    # prepend some points and lop off the end
    idx_template = np.linspace(-np.pi / 2, 3 * np.pi / 2, num=len_pts)
    template_y = np.sin(idx_template)
    template_x = np.cos(idx_template)
    template = np.zeros(shape=(len_pts, 2))
    template[:, 0] = template_x
    template[:, 1] = template_y

    return query, template

class MyTestCase(unittest.TestCase):
    def test_dtw_1d(self):
        # test code from the dtw-python docs
        # compares two 1-d sinusoidal curves
        # A noisy sine wave as query
        idx = np.linspace(0, 6.28, num=100)
        query = np.sin(idx) + np.random.uniform(size=100) / 10.0

        # A cosine is for template; sin and cos are offset by 25 samples
        template = np.cos(idx)

        # Find the best match with the canonical recursion formula
        alignment = dtw.dtw(query, template, keep_internals=True)

        # Display the warping curve, i.e. the alignment curve
        alignment.plot(type="threeway")

        alignment.plot(type="twoway")

    def test_dtw_2d(self):

        query, template = gen_2d(100)

        alignment = dtw.dtw(query, template, keep_internals=True)

        # compute distance along the template as a reference length
        delta = template[1:, :] - template[0:-1, :]
        template_dist = np.sum(np.linalg.norm(delta, axis=1))
        print(template_dist)

        delta = query[1:, :] - query[0:-1, :]
        query_dist = np.sum(np.linalg.norm(delta, axis=1))
        # the query distance is inflated by noise
        print(query_dist)

        # Display the warping curve, i.e. the alignment curve
        alignment.plot(type="threeway")
        # this does not work in higher dimensions!
        #alignment.plot(type="twoway")


    def test_dtw_patch(self):
        # merge two trajectories into one. use edit_gpx.patch_deletions_with_template
        query, template = gen_2d(100)
        delta_dist_median, delta_dist_smad = edit_gpx.get_point_stats(query)
        # patch the query
        # aligned values more than 3*SMAD indicate differences to be patched
        smad_factor = 2
        output, _ = edit_gpx.patch_deletions_with_template(query, template, delta_dist_median+smad_factor*delta_dist_smad)

        plt.figure()
        plt.plot(output[:, 0], 'b+')
        plt.plot(output[:, 1], 'r+')
        plt.title('corrected query')
        plt.show()

        # compute distance along the output - this should be 5pi/2, except
        # that the query is noisy, so it is query_dist + pi/2
        delta = output[1:, :] - output[0:-1, :]
        output_dist = np.sum(np.linalg.norm(delta, axis=1))
        print('output_dist:', output_dist)
        delta = query[1:, :] - query[0:-1, :]
        query_dist = np.sum(np.linalg.norm(delta, axis=1))
        target_dist = query_dist + np.pi/2
        print('target dist:', target_dist)
        max_diff = target_dist * 0.05
        self.assertTrue(abs(output_dist-target_dist) < max_diff)


if __name__ == '__main__':
    unittest.main()
