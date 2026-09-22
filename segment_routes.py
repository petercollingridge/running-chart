import os
from utils import get_gpx_data, get_coords, get_extent_for_runs
from math import cos, radians

from draw_svg import SVG

FOLDER = 'gpx'
# Define the grid size we snap to in metres
GRID_SIZE = 12


def to_xy(lat, lon, lat0):
    """Approximate lat/lon as metres relative to lat0."""

    y = round(lat * 111_320)
    x = round(lon * 111_320 * cos(radians(lat0)))
    return x, y


def grid_point(lat, lon, lat0):
    """Convert GPS point to a grid cell."""
    x, y = to_xy(lat, lon, lat0)
    return (
        round(x / GRID_SIZE),
        round(y / GRID_SIZE),
    )


def runs_to_meters(runs):
    """Convert all runs from lat/lon to x/y in metres relative to the reference latitude."""

    lat0 = sum(p[0] for run in runs.values() for p in run) / \
           sum(len(run) for run in runs.values())

    runs_in_meters = {}
    for run_id, run in runs.items():
        runs_in_meters[run_id] = [to_xy(lat, lon, lat0) for lat, lon in run]

    return runs_in_meters


def compress_run(run):
    """Compress a run by removing consecutive points that are within 10 metres."""

    threshold = GRID_SIZE ** 2

    compressed = []

    def find_existing_point(coord):
        for prev in compressed:
            dx = coord[0] - prev['x']
            dy = coord[1] - prev['y']
            if dx * dx + dy * dy <= threshold:
                return prev
        return None

    for coord in run:
        exisiting_point = find_existing_point(coord)
        if exisiting_point:
            # Update the existing point with the new coordinate and recalculate its average position.
            exisiting_point['x'] = sum(p[0] for p in exisiting_point['points']) // len(exisiting_point['points'])
            exisiting_point['y'] = sum(p[1] for p in exisiting_point['points']) // len(exisiting_point['points'])
            exisiting_point['points'].append(coord)
        else:
            compressed.append({'x': coord[0], 'y': coord[1], 'points': [coord]})

    return compressed


def snap_runs_to_grid(runs):
    """Snap GPS coords of all runs to the nearest grid cell."""

    # Calculate the reference latitude (lat0) for converting lat/lon to x/y coordinates.
    lat0 = sum(p[1] for run in runs.values() for p in run) / \
           sum(len(run) for run in runs.values())

    # Snap all runs to the grid.
    snapped_runs = {}
    for run_id, run in runs.items():
        snapped_runs[run_id] = [grid_point(lat, lon, lat0) for lat, lon in run]

    return snapped_runs


def draw_compressed_points(run):
    """ Draw all the points of a run, plus it's compressed version. """

    width = 800
    margin = 10
    min_x = min(p['x'] for p in run)
    min_y = min(p['y'] for p in run)
    max_x = max(p['x'] for p in run)
    max_y = max(p['y'] for p in run)

    scale = (width - margin * 2) / (max_x - min_x)
    r = round(scale * GRID_SIZE * 10) / 10

    def scale_x(x):
        return round((x - min_x) * scale + margin, 2)

    def scale_y(y):
        return round((max_y - y) * scale + margin, 2)

    height = scale * (max_y - min_y) + margin * 2
    svg = SVG({ 'width': '100%', 'viewBox': f"0 0 {width} {height}" })
    svg.add('rect', { 'x': 0, 'y': 0, 'width': width, 'height': height, 'fill': '#f0f0f0' })

    g = svg.add('g', { 'opacity': 0.5 })

    for coord in run:
        g.add('circle', {
            'cx': scale_x(coord['x']),
            'cy': scale_y(coord['y']),
            'r': r,
            'stroke': '#ff0000',
            'fill': 'none'
        })
        for p in coord['points']:
            g.add('circle', {
                'cx': scale_x(p[0]),
                'cy': scale_y(p[1]),
                'r': 3,
                'fill': '#000000',
            })

    filename = os.path.join("images", "compressed_run.svg")
    svg.write(filename)


def plot_runs(runs, filename='route.svg'):
    """Plot the route using draw_svg."""
    width = 800
    margin = 10

    min_lon, max_lon , min_lat, max_lat = get_extent_for_runs(runs)
    print(min_lat, max_lat, min_lon, max_lon)
    scale = (width - margin * 2) / (max_lon - min_lon)

    def scale_x(lon):
        return round((lon - min_lon) * scale + margin, 2)

    def scale_y(lat):
        return round((max_lat - lat) * scale + margin, 2)

    height = scale * (max_lat - min_lat) + margin * 2
    svg = SVG({ 'width': '100%', 'viewBox': f"0 0 {width} {height}" })
    svg.addStyle('.route', { 'fill': 'none', 'stroke': '#2d7d7a', 'stroke-width': 2, 'opacity': 0.25 })
    svg.addStyle('.village-name', { 'fill': '#112', 'font-size': '10px', 'text-anchor': 'start', 'dominant-baseline': 'baseline' })
    svg.addStyle('.distance-circle', { 'fill': 'none', 'stroke': '#e8e8f0', 'stroke-width': 0.5, 'stroke-dasharray': '4 2' })

    svg.add('rect', { 'x': 0, 'y': 0, 'width': width, 'height': height, 'fill': '#f0f0f0' })

    for run in runs.values():
        points = " ".join(f"{scale_x(d[0])},{scale_y(d[1])}" for d in run)
        svg.add('polyline', { 'points': points, 'class': 'route' })

    filename = os.path.join("images", filename)
    svg.write(filename)


if __name__ == "__main__":
    runs = get_gpx_data(FOLDER, get_coords)
    # print(list(runs.values())[0])

    runs_in_meters = runs_to_meters(runs)

    # snapped_runs = snap_runs_to_grid(runs)
    # print(list(snapped_runs.values())[0])

    first_run = list(runs_in_meters.keys())[10]
    first_run_data = runs_in_meters[first_run]
    # first_run_dict = {first_run: first_run_data}
    # print(first_run_dict)

    compressed_run = compress_run(first_run_data)
    print(len(first_run_data))
    print(len(compressed_run))
    draw_compressed_points(compressed_run)

    # plot_runs(runs_in_meters, 'snapped_route.svg')


