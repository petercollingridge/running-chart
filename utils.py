import os
from math import floor

import xml.etree.ElementTree as ET
from datetime import datetime

# colours = (
#     (6.25, (0, 0, 0)),      # Black
#     (5.75, (200, 0, 0)),    # Red
#     (5, (250, 240, 0)),     # Yellow
#     (4.75, (0, 200, 0)),    # Green
#     (4.5, (0, 0, 160)),     # Dark blue
#     (4, (160, 160, 255)),   # Light blue
# )

colours = (
    (6.25, (0, 0, 0)),      # Black
    (5.75, (200, 0, 0)),    # Red
    (5, (250, 240, 0)),     # Yellow
    (4.75, (0, 200, 0)),    # Green
    (4.5, (60, 120, 255)),   # Light blue
    (4, (0, 0, 120)),     # Dark blue
)

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

GPX_NAMESPACE = {"gpx": "http://www.topografix.com/GPX/1/1"}

def get_pace_colour(x):
    for i, colour in enumerate(colours):
        if x > colour[0]:
            # Propotion of the way through this band
            t1, c1 = colour
            t2, c2 = colours[i - 1]
            p = (x - t1) / (t2 - t1)
            colour = [round(c2[n] * p + c1[n] * (1 - p)) for n in range(3)]
            return f"rgb({colour[0]}, {colour[1]}, {colour[2]})"


def read_data(filename):
    run_data = []
    with open(filename, 'r') as f:
        for line in f:
            if line[0] == '#':
                continue

            data = line.strip().split()
            day = data[0]
            month = data[1]

            if len(data) > 2 and data[2]:
                run_time = data[2].split(':')
                run_time_seconds = sum(int(t) * 60 ** (2 - i) for i, t in enumerate(run_time))
            else:
                run_time_seconds = 0

            if len(data) > 3 and data[3]:
                distance = float(data[3])
                pace = run_time_seconds / float(distance) / 60
            else:
                distance = 0
                pace = None

            run_data.append({
                'day': day,
                'month': month,
                'distance': distance,
                'time': run_time_seconds,
                'pace': pace,
            })
    return run_data


def seconds_to_time(s):
    minutes = floor(s / 60)
    seconds = floor(s) % 60
    return f"{minutes}:{seconds:02d}"


def get_colours_for_year(years):
    """ Return a dict mapping year to colour. """
    colours = {}
    blue_step = 255 // len(years)
    green_step = 200 // (len(years) - 1)

    for i, year in enumerate(years):
        blue = 255 - i * blue_step
        green = 200 - i * green_step
        colours[year] = f'rgb(0, {green}, {blue})'

    return colours


def get_runs_by_year(folder = 'data'):
    """ Return a dict mapping year (str) to list run dicts. """
    runs_by_year = {}
    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            year = filename[:-4]
            filepath = os.path.join(folder, filename)
            runs_by_year[year] = read_data(filepath)
    return runs_by_year


def get_all_runs(folder = 'data'):
    """ Return a list of all runs as dicts. """
    all_runs = []
    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(folder, filename)
            year = filename[:-4]
            data = read_data(filepath)
            for run in data:
                run['year'] = year
            all_runs.extend(data)
    return all_runs


def get_coords(file_path):
    """Open a gpx file and extract the longitude and latitude data."""

    tree = ET.parse(file_path)
    root = tree.getroot()

    data = []
    for trk in root.findall("gpx:trk", GPX_NAMESPACE):
        for pt in trk.findall(".//gpx:trkpt", GPX_NAMESPACE):
            data.append((float(pt.get("lat")), float(pt.get("lon"))))

    return data


def get_coords_and_time(file_path):
    """Open a gpx file and extract the longitude, latitude, and time data."""

    tree = ET.parse(file_path)
    root = tree.getroot()

    metadata = root.findall("gpx:metadata", GPX_NAMESPACE)
    start_time_string = metadata[0].find("gpx:time", GPX_NAMESPACE).text if metadata else None
    start_time = datetime.fromisoformat(start_time_string.replace("Z", "+00:00")) if start_time_string else None

    data = []
    last_lat = None
    last_lon = None

    for trk in root.findall("gpx:trk", GPX_NAMESPACE):
        for pt in trk.findall(".//gpx:trkpt", GPX_NAMESPACE):
            lon = float(pt.get("lon"))
            lat = float(pt.get("lat"))

            # Filter out points that are too close together to reduce noise
            if last_lon is not None and last_lat is not None:
                d_lon = lon - last_lon
                d_lat = lat - last_lat
                if d_lon * d_lon + d_lat * d_lat < 0.00000001:
                    continue

            time_string = pt.find("gpx:time", GPX_NAMESPACE)
            if time_string is not None and time_string.text:
                time = datetime.fromisoformat(time_string.text.replace("Z", "+00:00"))
            else:
                time = None

            d_time = (time is not None and start_time is not None) and (time - start_time).total_seconds() or 0
            data.append((lon, lat, int(d_time)))
            last_lon = lon
            last_lat = lat

    return data


def get_gpx_data(folder, get_data_func):
    """
    Get all gpx run data from the specified folder.
    Returns a dict mapping filename to the data returned by get_data_func.
    """

    runs = {}
    for filename in os.listdir(folder):
        if filename.endswith('.gpx'):
            if filename.startswith('2026'):
                # print(f"Processing {filename}...")
                filepath = os.path.join(folder, filename)
                data = get_data_func(filepath)
                runs[filename] = data
    return runs


def get_extent_for_run(run_data):
    """Get the extent of the data as (min_lon, max_lon, min_lat, max_lat)."""
    min_lon = min(d[0] for d in run_data)
    max_lon = max(d[0] for d in run_data)
    min_lat = min(d[1] for d in run_data)
    max_lat = max(d[1] for d in run_data)
    return min_lon, max_lon, min_lat, max_lat


def get_extent_for_runs(runs):
    """Get the extent of multiple runs as (min_lon, max_lon, min_lat, max_lat)."""
    min_lon = min(get_extent_for_run(run)[0] for run in runs.values())
    max_lon = max(get_extent_for_run(run)[1] for run in runs.values())
    min_lat = min(get_extent_for_run(run)[2] for run in runs.values())
    max_lat = max(get_extent_for_run(run)[3] for run in runs.values())
    return min_lon, max_lon, min_lat, max_lat
