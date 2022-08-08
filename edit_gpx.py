import gpxpy as gp
import numpy as np
import dtw
import skimage.measure as measure


def patch_deletions_with_template(query: np.ndarray, template: np.ndarray) -> np.ndarray:
    # compute distance along the template as a reference length
    delta = template[1:, :] - template[0:-1, :]
    template_dist = np.sum(np.linalg.norm(delta, axis=1))
    alignment = dtw.dtw(query, template, keep_internals=True)
    alignment.plot(type="threeway")
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
    for region_label in range(1, max(cc_deletions) + 1):
        deletion_region_indices = reference_index[cc_deletions == region_label]
        # find the region indices in the alignment index (as opposed to
        # the index in the index differences)
        region_min = min(deletion_region_indices) + 1
        region_max = max(deletion_region_indices) + 2
        # compute the distance along this items in the query
        pts = template[alignment.index2[region_min:region_max], :]
        pts_diff = pts[1:, :] - pts[0:-1, :]
        dist = np.sum(np.linalg.norm(pts_diff, axis=1))
        # print(region_label, region_min, region_max, dist)
        deletion_regions.append((region_min, region_max, dist))
    # now copy the appropriate patches in the query and template into
    # the result.
    # First, copy in the entire query.
    len_output = len(alignment.index1)
    output = np.zeros(shape=(len_output, 2))
    output = query[alignment.index1, :]
    # and now fix the deletions. We already have the insertions.
    # filter out the small regions
    min_dist = template_dist * 0.02
    for region in deletion_regions:
        d = region[2]
        if d > min_dist:
            region_min = region[0]
            region_max = region[1]
            output[region_min:region_max, :] = template[region_min:region_max, :]
    # print(output)
    return output


def gpx_to_lat_lon(file_name):
    ''' see https://towardsdatascience.com/build-interactive-gps-activity-maps-from-gpx-files-using-folium-cf9eebba1fe7 '''
    gf = open(file_name, 'r')
    gfp = gp.parse(gf)
    points = []
    for track in gfp.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    return points




def patch_gaps(gpx1, gpx2, gpx_out, gap_threshold_meters, gap_threshold_seconds):
    ''' Patch the gaps (points seperated by more than the threshold) in
    gpx1 with data from gpx2. This includes regions before and after the
    gpx1 track. '''
    # convert the two files to gpx lists
    gf1 = open(gpx1, 'r')
    gf1p = gp.parse(gf1)
    gf2 = open(gpx2, 'r')
    gf2p = gp.parse(gf2)
    # grab the points
    pts1 = gf1p.tracks[0].segments[0].points
    pts2 = gf2p.tracks[0].segments[0].points
    # start by checking for a time gap between the first entries.

