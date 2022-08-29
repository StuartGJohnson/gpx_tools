import gpxpy as gp
import numpy as np
import dtw
import skimage.measure as measure
import matplotlib.pyplot as plt
import scipy.stats as sci_stats
from gpxpy import geo as gp_geo
import folium
import os
import argparse
import sys


def patch_deletions_with_template(
        query: np.ndarray,
        template: np.ndarray,
        dist_thresh: float,
        query_time=None,
        template_time=None,
        do_plots=False,
        do_plots_output_name=None) -> (np.ndarray, list):
    # compute distance along the template as a reference length
    track_time = False
    if query_time is not None and template_time is not None:
        track_time = True
    alignment = dtw.dtw(query, template, keep_internals=True)
    if do_plots:
        ax = alignment.plot(type="threeway")
        # since it seems a bit difficult to tidy up the plots with labels,
        # lets dump a few values via print() so we can make some notes in text
        # or figure captions
        for i in range(0, query.shape[1]):
            print('first query value on index ', i, ' is:', query[0, i])
        if do_plots_output_name:
            plot_file = os.path.splitext(do_plots_output_name)[0] + '.alignment.png'
            ax.get_figure().savefig(plot_file)
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
        if (alignment.index2[region_max - 1] - alignment.index2[region_min]) \
                > (alignment.index1[region_max - 1] - alignment.index1[region_min]):
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


def get_point_stats(points, smad_factor, do_plots=True):
    # compute outlier-robust point stats for misalignment detection
    delta = points[1:, :] - points[0:-1, :]
    delta_dist = np.linalg.norm(delta, axis=1)
    # use MAD/SMAD to account for outliers
    delta_dist_median = np.median(delta_dist)
    delta_dist_smad = sci_stats.median_abs_deviation(delta_dist, scale='normal')
    x = np.arange(0, len(delta_dist))
    y_med = np.ones(shape=(len(x),)) * delta_dist_median
    y_plus = y_med + delta_dist_smad * smad_factor
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
    flat_earth_correction = np.array([[1.0 * gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE]])
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
    flat_earth_correction = np.array([[1.0 * gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE, 1.0]])
    corrected_points = (points - mean_point) * flat_earth_correction
    return corrected_points, mean_point


def points_to_lat_lon_elev(points, mean_point) -> np.array:
    # correct points back to lat,lon, elevation
    flat_earth_correction = np.array([[1.0 * gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE, 1.0]])
    corrected_points = points / flat_earth_correction + mean_point
    return corrected_points


def points_to_lat_lon(points, mean_point) -> np.array:
    if points.shape[1] == 2:
        # correct points back to lat,lon, elevation
        flat_earth_correction = np.array([[1.0 * gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE]])
    elif points.shape[1] == 3:
        # correct points back to lat,lon, elevation
        flat_earth_correction = np.array([[1.0 * gp_geo.ONE_DEGREE, np.cos(mean_point[0, 0]) * gp_geo.ONE_DEGREE, 1.0]])
    else:
        raise ValueError("unknown points shape!")
    corrected_points = points / flat_earth_correction + mean_point
    # and lop off the elevation, if it is there
    corrected_points = corrected_points[:, 0:2]
    return corrected_points


def points_to_gpx(
        name_append: str,
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
    gfp_copy.tracks[0].name += name_append
    return gfp_copy


def edit_gpx(query_file, template_file, output_file, dist_thresh=50, do_plots=False, folium_output=False):
    # run the gpx data through the patching process
    gf = open(query_file, 'r')
    gfp_query = gp.parse(gf)
    gf.close()
    gfp_query_copy = gfp_query.clone()
    gf = open(template_file, 'r')
    gfp_template = gp.parse(gf)
    gf.close()
    # Hmm, should we assert that each gfp has a single track and segment?
    # Or, perhaps perform the analysis on each track/segment?
    # Do strava gpx tracks ever have more than one track/segment?
    # assume we have a single track and segment!
    gfp_query_points = gfp_query.tracks[0].segments[0].points
    gfp_template_points = gfp_template.tracks[0].segments[0].points
    # Unpack gfp points into numpy arrays.
    query_points, mean_point = gpx_to_points3(gfp_query_points)
    # Also unpack time of track points separately
    qp_time = gpx_to_time_points(gfp_query_points)
    template_points, _ = gpx_to_points3(gfp_template_points, mean_point)
    tp_time = gpx_to_time_points(gfp_template_points)
    # patch the query - 50 meters seems a good number for mountain biking!
    fixed_points, fixed_points_time = patch_deletions_with_template(
        query_points,
        template_points,
        dist_thresh,
        query_time=qp_time,
        template_time=tp_time,
        do_plots=do_plots,
        do_plots_output_name=output_file)
    # and generate a proper gpx object, and write to file
    gpx = points_to_gpx(' patched', gfp_query_copy, fixed_points, mean_point,
                        fixed_points_time)
    with open(output_file, 'w') as f:
        f.write(gpx.to_xml())

    if folium_output:
        # convert all values back to lat/lon for plotting
        qp_lat_lon = points_to_lat_lon(query_points, mean_point)
        tp_lat_lon = points_to_lat_lon(template_points, mean_point)
        fp_lat_lon = points_to_lat_lon(fixed_points, mean_point)
        # build map
        map_center = np.mean(np.array(fp_lat_lon), axis=0)
        mymap = folium.Map(location=map_center, zoom_start=14, tiles=None)
        folium.TileLayer().add_to(mymap)
        # add lines; note the dashes help distinguish trajectories which are typically on top
        # of each other
        folium.PolyLine(list(fp_lat_lon), color='green', weight=4.5, opacity=0.5).add_to(mymap)
        folium.PolyLine(list(qp_lat_lon), color='red', weight=4.5, opacity=0.5, dash_array='10').add_to(mymap)
        folium.PolyLine(list(tp_lat_lon), color='blue', weight=4.5, opacity=0.5, dash_array='10').add_to(mymap)
        folium_file = os.path.splitext(output_file)[0] + '.html'
        mymap.save(folium_file)
    # for unit testing
    return gpx


def main(args):
    parser = argparse.ArgumentParser(description='edit_gpx - patch gpx file with another similar gpx file')
    parser.add_argument('query_gpx',
                        help='the name of the gpx file to be patched - it''s contents are preferred')
    parser.add_argument('template_gpx',
                        help='the name of the gpx file to patch the query_gpx with')
    parser.add_argument('output_gpx',
                        help='the name of the output gpx file')
    parser.add_argument('--dist', default=50,
                        help='the distance threshold for query vs template misalignment (in meters) default=50')
    args = parser.parse_args(args)
    edit_gpx(args.query_gpx, args.template_gpx, args.output_gpx, args.dist)


if __name__ == '__main__':
    main(sys.argv[1:])

