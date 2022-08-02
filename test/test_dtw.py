import unittest
import numpy as np
import dtw
import matplotlib.pyplot as plt


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
        # OK, let's try 2D data
        # a full 2pi
        len_pts = 100
        idx_query = np.linspace(0, 2*np.pi, num=len_pts)
        query_y = np.sin(idx_query) + np.random.uniform(size=len_pts) / 10.0
        query_x = np.cos(idx_query) + np.random.uniform(size=len_pts) / 10.0
        query = np.zeros(shape=(len_pts, 2))
        query[:, 0] = query_x
        query[:, 1] = query_y

        idx_template = np.linspace(-np.pi/2, 3*np.pi/2, num=len_pts)
        template_y = np.sin(idx_template)
        template_x = np.cos(idx_template)
        template = np.zeros(shape=(len_pts, 2))
        template[:, 0] = template_x
        template[:, 1] = template_y

        alignment = dtw.dtw(query, template, keep_internals=True)
        # Display the warping curve, i.e. the alignment curve
        alignment.plot(type="threeway")
        # this does not work in higher dimensions!
        #alignment.plot(type="twoway")


if __name__ == '__main__':
    unittest.main()
