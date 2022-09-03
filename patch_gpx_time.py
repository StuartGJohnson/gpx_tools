import gpxpy as gp
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as sci_stats
from gpxpy import geo as gp_geo
from gpxpy import utils as gp_utils
import folium
import os
import argparse
import sys
import datetime as mod_datetime
import copy

from typing import List


def gpx_to_lat_lon(gfp_points) -> np.ndarray:
    points = np.zeros(shape=(len(gfp_points), 2), dtype=float)
    for pt_ind, pt in enumerate(gfp_points):
        points[pt_ind, 0] = pt.latitude
        points[pt_ind, 1] = pt.longitude
    return points


def gpx_to_time_seconds(gfp_points: List[gp.gpx.GPXTrackPoint]) -> (np.ndarray, mod_datetime.datetime):
    points = np.zeros(shape=(len(gfp_points), 1), dtype=float)
    base_time = gfp_points[0].time
    for pt_ind, pt in enumerate(gfp_points):
        points[pt_ind, 0] = diff_seconds(pt.time, base_time)
    return points, base_time


def diff_seconds(time1: mod_datetime.datetime, time2: mod_datetime.datetime):
    """much like what gpxpy provides, but signed"""
    time_diff = time1 - time2
    return gp_utils.total_seconds(time_diff)


def filter_point(src: gp.gpx.GPXTrackPoint):
    """ copy the track point and delete the extensions -
    this typically contains source-specific information"""
    new_point = copy.deepcopy(src)
    new_point.extensions = []
    return new_point


def patch_gpx(
        query: gp.gpx.GPX,
        template: gp.gpx.GPX,
        max_time_gap_seconds: float) -> gp.gpx.GPX:
    """ patch time gaps in the query with the template """
    query_track = query.tracks[0].segments[0].points
    template_track = template.tracks[0].segments[0].points
    output_track = query.clone()
    track_points = []
    template_index = 0
    query_index = 0
    max_query_index = len(query_track)
    max_template_index = len(template_track)
    # handle times in the template before the query starts
    if diff_seconds(query_track[0].time, template_track[0].time) >= max_time_gap_seconds:
        while template_index < max_template_index and \
                template_track[template_index].time < query_track[query_index].time:
            track_points.append(filter_point(template_track[template_index]))
            template_index += 1
    # copy in the query until we get a time gap
    while query_index < max_query_index:
        if query_index == max_query_index - 1:
            # the last query value has no succeeding interval
            track_points.append(query_track[query_index])
        elif diff_seconds(query_track[query_index + 1].time, query_track[query_index].time) < max_time_gap_seconds:
            # query trackpoint is fine
            track_points.append(query_track[query_index])
        else:
            # if there is any data left in the template, let's try to patch the query
            if template_index < max_template_index:
                # advance to this time gap in the template
                while template_index < max_template_index and \
                        template_track[template_index].time < query_track[query_index].time:
                    template_index += 1
                while template_index < max_template_index and \
                        template_track[template_index].time < query_track[query_index+1].time:
                    track_points.append(filter_point(template_track[template_index]))
                    template_index += 1
        query_index += 1
    # copy in any template data after the query data, if there is a time gap
    if diff_seconds(template_track[max_template_index-1].time, query_track[max_query_index-1].time) \
            >= max_time_gap_seconds:
        while template_index < max_template_index and \
                template_track[template_index].time < query_track[max_query_index-1].time:
            template_index += 1
        while template_index < max_template_index and \
                template_index < max_template_index:
            track_points.append(filter_point(template_track[template_index]))
            template_index += 1
    # insert the new points into the output
    output_track.tracks[0].segments[0].points = track_points
    output_track.tracks[0].name += ' patched (simple time algo)'
    return output_track


def patch_gpx_file(query_file, template_file, output_file, time_thresh=30, do_plots=False, folium_output=False):
    # run the gpx data through the patching process
    gf = open(query_file, 'r')
    gfp_query = gp.parse(gf)
    gf.close()
    gf = open(template_file, 'r')
    gfp_template = gp.parse(gf)
    gf.close()
    output = patch_gpx(gfp_query, gfp_template, time_thresh)

    with open(output_file, 'w') as f:
        f.write(output.to_xml())

    if folium_output:
        # Unpack gfp points into numpy arrays.
        qp_lat_lon = gpx_to_lat_lon(gfp_query.tracks[0].segments[0].points)
        tp_lat_lon = gpx_to_lat_lon(gfp_template.tracks[0].segments[0].points)
        fp_lat_lon = gpx_to_lat_lon(output.tracks[0].segments[0].points)
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

    return output


def main(args):
    parser = argparse.ArgumentParser(
        description='patch_gpx_time - patch gpx file with another similar gpx file using timestamp data')
    parser.add_argument('query_gpx',
                        help='the name of the gpx file to be patched - it''s contents are preferred')
    parser.add_argument('template_gpx',
                        help='the name of the gpx file to patch the query_gpx with')
    parser.add_argument('output_gpx',
                        help='the name of the output gpx file')
    parser.add_argument('--time', default=30,
                        help='the time threshold for patching time gaps in the query (in seconds) default=30')
    args = parser.parse_args(args)
    patch_gpx_file(args.query_gpx, args.template_gpx, args.output_gpx, args.time)


if __name__ == '__main__':
    main(sys.argv[1:])
