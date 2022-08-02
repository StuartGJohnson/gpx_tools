import gpxpy as gp


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

