import os
import xml.etree.ElementTree as ET
from draw_svg import SVG

# Namespace for GPX files
ns = {"gpx": "http://www.topografix.com/GPX/1/1"}


def get_data(file_path):
    """Open a gpx file and extract the longitude and latitude data."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    data = []
    for trk in root.findall("gpx:trk", ns):
        for pt in trk.findall(".//gpx:trkpt", ns):
            data.append((float(pt.get("lat")), float(pt.get("lon"))))

    return data


def get_extent_for_run(run_data):
    """Get the extent of the data as (min_lat, max_lat, min_lon, max_lon)."""
    min_lat = min(lat for lat, _ in run_data)
    max_lat = max(lat for lat, _ in run_data)
    min_lon = min(lon for _, lon in run_data)
    max_lon = max(lon for _, lon in run_data)
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
    svg.addStyle('.route', { 'fill': 'none', 'stroke': '#2d7d7a', 'stroke-width': 2, 'opacity': 0.25 })

    svg.add('rect', { 'x': 0, 'y': 0, 'width': width, 'height': height, 'fill': '#f0f0f0' })

    for run in runs.values():
        points = " ".join(f"{scale_x(lon)},{scale_y(lat)}" for lat, lon in run)
        svg.add('polyline', { 'points': points, 'class': 'route' })

    svg.write("route.svg")


def main(folder):
    runs = {}
    for filename in os.listdir(folder):
        if filename.endswith('.gpx'):
            filepath = os.path.join(folder, filename)
            data = get_data(filepath)
            runs[filename] = data

    plot_route(runs)


if __name__ == "__main__":
    folder = os.path.join(os.path.dirname(__file__), "gpx")
    main(folder)
