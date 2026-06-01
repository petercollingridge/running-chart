import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from draw_svg import SVG

# Namespace for GPX files
ns = {"gpx": "http://www.topografix.com/GPX/1/1"}


def get_coords(file_path):
    """Open a gpx file and extract the longitude and latitude data."""

    tree = ET.parse(file_path)
    root = tree.getroot()

    data = []
    for trk in root.findall("gpx:trk", ns):
        for pt in trk.findall(".//gpx:trkpt", ns):
            data.append((float(pt.get("lat")), float(pt.get("lon"))))

    return data


def get_coords_and_time(file_path):
    """Open a gpx file and extract the longitude, latitude, and time data."""

    tree = ET.parse(file_path)
    root = tree.getroot()

    metadata = root.findall("gpx:metadata", ns)
    start_time_string = metadata[0].find("gpx:time", ns).text if metadata else None
    start_time = datetime.fromisoformat(start_time_string.replace("Z", "+00:00")) if start_time_string else None

    data = []
    last_lat = None
    last_lon = None

    for trk in root.findall("gpx:trk", ns):
        for pt in trk.findall(".//gpx:trkpt", ns):
            lat = float(pt.get("lat"))
            lon = float(pt.get("lon"))
            time_string = pt.find("gpx:time", ns)
            if time_string is not None and time_string.text:
                time = datetime.fromisoformat(time_string.text.replace("Z", "+00:00"))
            else:
                time = None

            # Filter out points that are too close together to reduce noise
            if last_lat is not None and last_lon is not None:
                d_lat = lat - last_lat
                d_lon = lon - last_lon
                if d_lat * d_lat + d_lon * d_lon < 0.00000001:
                    continue

            d_time = (time is not None and start_time is not None) and (time - start_time).total_seconds() or 0
            data.append((lat, lon, int(d_time)))
            last_lat = lat
            last_lon = lon

    return data


def get_data_for_runs(folder, get_data_func):
    """
    Get all run data from the specified folder.
    Returns a dict mapping filename to the data returned by get_data_func.
    """

    runs = {}
    for filename in os.listdir(folder):
        if filename.endswith('.gpx'):
            if filename.startswith('2026'):
                print(f"Processing {filename}...")
                filepath = os.path.join(folder, filename)
                data = get_data_func(filepath)
                runs[filename] = data
    return runs


def extract_to_json(folder):
    """Extract run data from gpx files and save it as json."""

    data = get_data_for_runs(folder, get_coords_and_time)

    # Convert list of list to list of dicts
    output_data = {}
    for filename, run_data in data.items():
        date = filename.removesuffix('.gpx')
        output_data[date] = [{'x': d[0], 'y': d[1], 't': d[2]} for d in run_data]

    with open(os.path.join(folder, "summary.json"), "w") as f:
        json.dump(output_data, f, indent=2)


def get_extent_for_run(run_data):
    """Get the extent of the data as (min_lat, max_lat, min_lon, max_lon)."""
    min_lat = min(d[0] for d in run_data)
    max_lat = max(d[0] for d in run_data)
    min_lon = min(d[1] for d in run_data)
    max_lon = max(d[1] for d in run_data)
    return min_lat, max_lat, min_lon, max_lon


def get_extent_for_runs(runs):
    """Get the extent of multiple runs as (min_lat, max_lat, min_lon, max_lon)."""
    min_lat = min(get_extent_for_run(run)[0] for run in runs.values())
    max_lat = max(get_extent_for_run(run)[1] for run in runs.values())
    min_lon = min(get_extent_for_run(run)[2] for run in runs.values())
    max_lon = max(get_extent_for_run(run)[3] for run in runs.values())
    return min_lat, max_lat, min_lon, max_lon


def plot_route(runs):
    """Plot the route using matplotlib."""
    width = 800
    margin = 10

    min_lat, max_lat, min_lon, max_lon = get_extent_for_runs(runs)
    scale = (width - margin * 2) / (max_lon - min_lon)

    def scale_x(lon):
        return round((lon - min_lon) * scale + margin, 2)

    def scale_y(lat):
        return round((max_lat - lat) * scale + margin, 2)

    height = scale * (max_lat - min_lat) + margin * 2
    svg = SVG({ 'width': '100%', 'viewBox': f"0 0 {width} {height}" })
    svg.addStyle('.route', { 'fill': 'none', 'stroke': '#2d7d7a', 'stroke-width': 2, 'opacity': 0.05 })

    # svg.add('rect', { 'x': 0, 'y': 0, 'width': width, 'height': height, 'fill': '#f0f0f0' })

    for run in runs.values():
        points = " ".join(f"{scale_x(d[1])},{scale_y(d[0])}" for d in run)
        svg.add('polyline', { 'points': points, 'class': 'route' })

    svg.write("route.svg")


def main(folder):
    # runs = get_data_for_runs(folder, get_coords)
    # plot_route(runs)

    # runs = get_data_for_runs(folder, get_coords_and_time)
    # print(list(runs.values())[0])
    # plot_route(runs)

    extract_to_json(folder)


if __name__ == "__main__":
    folder = os.path.join(os.path.dirname(__file__), "gpx")
    main(folder)
