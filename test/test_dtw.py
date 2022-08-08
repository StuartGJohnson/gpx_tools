import unittest
import numpy as np
import dtw
import matplotlib.pyplot as plt
import skimage.measure as measure


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

        # compute distance along the template as a reference length
        delta = template[1:, :] - template[0:-1, :]
        template_dist = np.sum(np.linalg.norm(delta, axis=1))
        #print(template_dist)

        delta = query[1:, :] - query[0:-1, :]
        query_dist = np.sum(np.linalg.norm(delta, axis=1))
        #print(query_dist)

        # Display the warping curve, i.e. the alignment curve
        alignment.plot(type="threeway")
        # this does not work in higher dimensions!
        #alignment.plot(type="twoway")

        # merge these two trajectories into a single trajectory.
        # first, locate the alignment gaps. These have to be at least
        # min_dist in euclidean dist to be corrected. We'll do this with
        # connected component analysis of alignment regions which have zero
        # progress in the query (deletions in the template).

        # deletions are connected regions of no progress in the query index:
        # alignment.
        diff_index1 = alignment.index1[1:] - alignment.index1[0:-1]
        # find the regions where this is zero
        deletion_state = (diff_index1 == 0).astype(int)
        # run connected components analysis
        cc_deletions = measure.label(deletion_state, connectivity=1)
        # scan the cc for region extents
        reference_index = np.arange(0, len(cc_deletions))
        deletion_regions = []
        for region_label in range(1, max(cc_deletions)+1):
            deletion_region_indices = reference_index[cc_deletions == region_label]
            # find the region indices in the alignment index (as opposed to
            # the index in the index differences)
            region_min = min(deletion_region_indices)
            region_max = max(deletion_region_indices)+1
            # compute the distance along this items in the query
            pts = template[alignment.index2[region_min:region_max+1], :]
            pts_diff = pts[1:, :] - pts[0:-1, :]
            dist = np.sum(np.linalg.norm(pts_diff, axis=1))
            #print(region_label, region_min, region_max, dist)
            deletion_regions.append((region_min, region_max, dist))
        # insertions are connected regions of no progress in the template index:
        diff_index2 = alignment.index2[1:] - alignment.index2[0:-1]
        # find the regions where this is zero
        insertion_state = (diff_index2 == 0).astype(int)
        # run connected components analysis
        cc_insertions = measure.label(insertion_state, connectivity=1)
        # scan the cc for region extents
        reference_index = np.arange(0, len(cc_insertions))
        insertion_regions = []
        for region_label in range(1, max(cc_insertions)+1):
            insertion_region_indices = reference_index[cc_insertions == region_label]
            # find the region indices in the alignment index (as opposed to
            # the index in the index differences)
            region_min = min(insertion_region_indices)
            region_max = max(insertion_region_indices)+1
            # compute the distance along this items in the query
            pts = query[alignment.index1[region_min:region_max+1], :]
            pts_diff = pts[1:, :] - pts[0:-1, :]
            dist = np.sum(np.linalg.norm(pts_diff, axis=1))
            #print(region_label, region_min, region_max, dist)
            insertion_regions.append((region_min, region_max, dist))
        # now copy the appropriate patches in the query and template into
        # the result.
        # First, copy in the entire query.
        len_output = len(alignment.index1)
        output = np.zeros(shape=(len_output, 2))
        output = query[alignment.index1, :]
        # and now fix the deletions. We already have the insertions.
        # filter out the small regions
        min_dist = template_dist * 0.05
        for region in deletion_regions:
            d = region[2]
            if d > min_dist:
                region_min = region[0]
                region_max = region[1]
                output[region_min:region_max, :] = template[region_min:region_max, :]
        #print(output)

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
        target_dist = query_dist + np.pi/2
        print('target dist:', target_dist)
        max_diff = target_dist * 0.05
        self.assertTrue(abs(output_dist-target_dist) < max_diff)




if __name__ == '__main__':
    unittest.main()
