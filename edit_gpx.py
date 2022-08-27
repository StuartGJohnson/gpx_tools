import gpxpy as gp
import numpy as np
import dtw
import skimage.measure as measure
import matplotlib.pyplot as plt
import scipy.stats as sci_stats
from gpxpy import geo as gp_geo
import datetime


def patch_deletions_with_template(
        query: np.ndarray,
        template: np.ndarray,
        dist_thresh: np.float,
        query_time=None,
        template_time=None) -> (np.ndarray, list):
    # compute distance along the template as a reference length
    track_time = False
    if query_time is not None:
        track_time = True
    alignment = dtw.dtw(query, template, keep_internals=True)
    alignment.plot(type="threeway")
    # merge these two trajectories into a single trajectory.
    # deletions are connected regions which are far from their aligned points
    pts_diff = template[alignment.index2, :] - query[alignment.index1, :]
    aligned_distance = np.linalg.norm(pts_diff, axis=1)
    deletion_state = (aligned_distance >= dist_thresh).astype(int)
    # run connected components analysis
    cc_deletions = measure.label(deletion_state, connectivity=1)
    # scan the cc for region extents
    reference_index = np.arange(0, len(cc_deletions))
    deletion_regions = []
    for region_label in range(1, max(cc_deletions) + 1):
        deletion_region_indices = reference_index[cc_deletions == region_label]
        # find the region indices in the alignment index
        region_min = min(deletion_region_indices)
        region_max = max(deletion_region_indices) + 1
        # print(region_label, region_min, region_max, dist)
        # if this misaligned region is better sampled in the template, mark it
        # as a deletion. Otherwise, forget about it - it's an insertion.
        if (alignment.index2[region_max-1] - alignment.index2[region_min])\
                > (alignment.index1[region_max-1] - alignment.index1[region_min]):
            deletion_regions.append((region_min, region_max))
    # now copy the appropriate patches in the query and template into
    # the result. First, copy in the entire query.
    len_output = len(alignment.index1)
    output = query[alignment.index1, :]
    output_time = None
    if track_time:
        output_time = [query_time[i] for i in alignment.index1]
    # and now fix the deletions. We already have the insertions.
    for region in deletion_regions:
        region_min = region[0]
        region_max = region[1]
        output[region_min:region_max, :] = template[alignment.index2[region_min:region_max], :]
        if track_time:
            output_time[region_min:region_max] = [template_time[i] for i in alignment.index2[region_min:region_max]]
    # and remove the repetitions due to different sampling intervals in the query and template
    pts_diff = output[0:-1, :] - output[1:, :]
    pts_dist = np.linalg.norm(pts_diff, axis=1)
    pts_include = pts_dist > 0
    # include the first point and offset
    pts_include = np.insert(pts_include, 0, True)
    output = output[pts_include, :]
    if track_time:
        output_time = [output_time[i] for i in np.where(pts_include)[0]]
    return output, output_time


def gpx_to_lat_lon(file_name):
    ''' see https://towardsdatascience.com/build-interactive-gps-activity-maps-from-gpx-files-using-folium-cf9eebba1fe7 '''
    gf = open(file_name, 'r')
    gfp = gp.parse(gf)
    gf.close()
    points = []
    for track in gfp.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    return points


def get_point_stats(points, do_plots=True):
    # compute outlier-robust point stats for misalignment detection
    delta = points[1:, :] - points[0:-1, :]
    delta_dist = np.linalg.norm(delta, axis=1)
    # use MAD/SMAD to account for outliers
    delta_dist_median = np.median(delta_dist)
    delta_dist_smad = sci_stats.median_abs_deviation(delta_dist, scale='normal')
    x = np.arange(0, len(delta_dist))
    y_med = np.ones(shape=(len(x),)) * delta_dist_median
    y_plus = y_med + delta_dist_smad * 5
    if do_plots:
        print(delta_dist_median, delta_dist_smad)
        plt.figure()
        plt.plot(x, delta_dist)
        plt.plot(x, y_med, 'r')
        plt.plot(x, y_plus, 'r--')
        plt.title('distance increments along query')
        plt.xlabel('index')
        plt.ylabel('dist')
        plt.show()
    return delta_dist_median, delta_dist_smad


def gpx_to_points2(gfp_points, mean_point=None) -> np.array:
    points = np.zeros(shape=(len(gfp_points), 2), dtype=float)
    pt_ind = 0
    for pt in gfp_points:
        points[pt_ind, 0] = pt.latitude
        points[pt_ind, 1] = pt.longitude
        pt_ind += 1
    # compute the mean point for various uses
    if mean_point is None:
        mean_point = np.mean(points, axis=0, keepdims=True)
    # apply local flat earth correction
    flat_earth_correction = np.array([[1.0*gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE]])
    corrected_points = (points - mean_point) * flat_earth_correction
    return corrected_points, mean_point


def gpx_to_time_points(gfp_points) -> list:
    time_points = []
    for pt in gfp_points:
        time_points.append(pt.time)
    return time_points


def gpx_to_points3(gfp_points, mean_point=None) -> (np.array, np.array):
    points = np.zeros(shape=(len(gfp_points), 3), dtype=float)
    for pt_ind, pt in enumerate(gfp_points):
        points[pt_ind, 0] = pt.latitude
        points[pt_ind, 1] = pt.longitude
        points[pt_ind, 2] = pt.elevation
    # compute the mean point for various uses
    if mean_point is None:
        mean_point = np.mean(points, axis=0, keepdims=True)
    # apply local flat earth correction
    flat_earth_correction = np.array([[1.0*gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE, 1.0]])
    corrected_points = (points - mean_point) * flat_earth_correction
    return corrected_points, mean_point


def points_to_lat_lon_elev(points, mean_point) -> np.array:
    # correct points back to lat,lon, elevation
    flat_earth_correction = np.array([[1.0*gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE, 1.0]])
    corrected_points = points / flat_earth_correction + mean_point
    return corrected_points


def points_to_lat_lon(points, mean_point) -> np.array:
    if points.shape[1] == 2:
        # correct points back to lat,lon, elevation
        flat_earth_correction = np.array([[1.0*gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE]])
    elif points.shape[1] == 3:
        # correct points back to lat,lon, elevation
        flat_earth_correction = np.array([[1.0*gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE, 1.0]])
    else:
        raise ValueError("unknown points shape!")
    corrected_points = points / flat_earth_correction + mean_point
    # and lop off the elevation, if it is there
    corrected_points = corrected_points[:, 0:2]
    return corrected_points


def points_to_gpx(
        name: str,
        gfp_copy: gp.gpx.GPX,
        points: np.ndarray,
        mean_point: np.ndarray,
        points_time: list) -> gp.gpx.GPX:
    # update the points in gfp_query_copy
    lat_lon_elev = points_to_lat_lon_elev(points, mean_point)
    track_points = []
    for ind_pt, pt in enumerate(lat_lon_elev):
        track_points.append(gp.gpx.GPXTrackPoint(pt[0], pt[1], pt[2], points_time[ind_pt]))
    # slap this into the GPX
    gfp_copy.tracks[0].segments[0].points = track_points
    gfp_copy.tracks[0].name = name
    return gfp_copy




