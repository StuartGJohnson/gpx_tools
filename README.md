# gpx_tools
<p>
Tools and background on fusing GPX files for the purpose of correcting missing parts of the track. Especially useful for mending a Strava activity when you have stopped for a snack, and forgotten to restart your GPS tracking device - and you are with someone who has not done this! This seems to happen to me all the time.
</p>

<p>
Note: this file may use LaTex support recently provided by Github. Sometimes these equations do not render, and you will see strange things with backslashes and odd looking bits (raw LaTex). If this is the case, reload the page in your browser.
</p>

## Installation

## Usage


### Usage model

Scenario: a Strava activity shows that you have missed a section of your route. Examples are that you have forgotten to restart your GPS device after a break at a nice park bench, or that you have forgotten to start your GPS device at the beginning of an activity. However, you were with someone else, and chances are they are not absent-minded in exactly the same way you are. You need to patch the gap(s) in your activity using their data. In order to do so, you use the 'export GPX' functionality of strava to generate a GPX file of your activity. In order to get someone else's activity, you ask them to export their activity as a GPX file (to insure complete data). Afterwards, you use tools provided here to generate a new - patched - GPX file. You upload this patched file to Strava and delete your original activity.

### Design preferences
For the purposes of repairing Strava activities, there are several design preferences:
<ol>
<li>one of the trajectories needs to be preferred in the result. For example, if I am correcting my activity, I would prefer that the output is composed of the original data from my activity as much as possible. </li>
<li>when using data from either activity, I would prefer that data to be unchanged from the original. </li>
<li>the algorithm should handle fairly complex trajectories which might pass through the same points - in any order or number of times.</li>
<li>the algorithm should assume that points could be missing in either activity at the beginning and end of the activity.</li>
<li>the correction process should not include certain data from the non-preferred activity in the output. Examples would be heart rate and cadence - which pertain to the other individual, not the course.</li>
</ol>

### Two correction algorithms

#### patch_gpx_spatial

An algorithm which only uses location data (latitude, longitude and elevation) is <b>patch_gpx_spatial</b>:
<ol>
<li> Compute the dynamic time warping between the query trajectory and the reference trajectory. </li>
<li> Assign the query to the output trajectory via the DTW alignment index for the query.</li>
<li> Assign portions of the reference to the output when the reference trajectory is missing in the query via the DTW alignment index for the reference. This corresponds to sections of the alignment which are vertical in figure 1.</li>
<li>Eliminate repeated points in the output. Different spatial sampling intervals (and misaligned points) in the reference and query trajectories will result in points in one trajectory mapping to multiple points in the other trajectory.</li>
</ol>

<p>
Some experimentation with this process with real GPX data (see below), suggests that deciding on when the reference trajectory points are missing from the alignment merely by looking at the alignment index is problematic and results in fidgety identification of missing regions of one trajectory. Part of the problem is that GPX trajectories can have very different spatial sampling - due to device settings - and this smears out the beginnings and ends of missing regions. One solution is to choose a distance threshold - and find the connected regions in the alignment where the two trajectories exceed this threshold. Then, for each connected region, choose to insert the reference points in the output only if the reference sampling is more than the query sampling in that region.
</p>

#### patch_gpx_time

A second, much simpler algorithm is to simply find missing time intervals in the query trajectory and insert reference trajectory data present in those missing time intervals into the corrected output. This is slightly more complex due to possible data overhangs at the ends. The algorithm is <b>patch_gpx_time</b>:

<ol>
<li> establish a time threshold, <i>max_time_gap</i>, above which time gaps in the query data are considering missing data - i.e. the user is not sampling the trajectory when he should.</li>
<li> If the earliest timestamp in the reference is before the earliest timestamp in the query, and the difference is greater than <i>max_time_gap</i>, include the reference data before the query data in the output. </li>
<li> For each point in the query:
<ol>
<li>If this is the last point in the query: append the query point to the output and exit step 3.</li>
<li>Compute the time gap to the next query point.</li>
<li>If the time gap is >= <i>max_time_gap</i>: append all reference points within the time gap to the output.</li>
<li>If the time gap is < <i>max_time_gap</i>: append the query point to the output.</li>
</ol>
<li> If the latest timestamp in the reference is after the latest timestamp in the query, and the difference is greater that <i>max_time_gap</i>, append the reference data with timestamps after the query data to the output. </li>
</ol>

## GPX example

The typical usage model for the patch_gpx tools is to mend GPX files obtained from Strava - when I am using this, I download my own GPX file of a damaged activity, and then ask whomever I rode or ran the activity with to send me the GPX file of their corresponding activity. Although Strava settings can be adjusted, I have found that typically a complete GPX file is only produced by the owner of the activity on Strava.

An example of the repair of an activity at Calero County Park in California is shown in the following links (I suggest you open it in another tab or window so that you can read along with the comments here. At the time of writing it did not seem possible to get the README.md rendered page to render this interactive folium map). The first link uses the <b>patch_gpx_spatial</b> algorithm:

[patched_gpx_spatial example](https://stuartgjohnson.github.io/gpx_tools/test/calero_patched_spatial.html)

and the second link uses the <b>patch_gpx_time</b> algorithm:

[patched_gpx_time example](https://stuartgjohnson.github.io/gpx_tools/test/calero_patched_time.html)

In this example, there are three routes plotted. My route, the query, is in dashed red. My friend's route (provided here with his permission) is dashed blue. The corrected route is solid green. Note you should be able to zoom in and out on this map/route in your browser. You should see that the route is almost always showing the red dashes and the green together - recall the query (my route) is preferred. The primary fix is in the section near Bald Peaks - where I forgot to restart my device at the snack stop at the top of the climb up Longwall Canyon Trail. In that section the fixed route tracks my friend's ride along Bald Peaks Trail.

Note the two algorithms give very similar results for this data, but there is a peculiar difference in the trajectories at the beginning and end (at the Rancho San Vicente Entrance Parking Lot). This probably needs to be investigated a bit.

