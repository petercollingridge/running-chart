import os
from math import cos, radians
from collections import defaultdict

from draw_svg import SVG
from utils import get_gpx_data, get_coords

FOLDER = 'gpx'
# Define the grid size we snap to in metres
GRID_SIZE = 32


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


class CompressedPoint:
    """Represents a set of GPS points that are close enough to be compressed into a single point."""

    def __init__(self, x, y, point_id, run_name):
        self.x = x
        self.y = y
        self.points = [(x, y)]
        self.id = point_id
        self.runs = set([run_name])

    def add_point(self, coord, name):
        """Add new coordinate and recalculate the average position."""

        self.points.append(coord)
        self.runs.add(name)
        n = len(self.points)
        self.x = sum(p[0] for p in self.points) // n
        self.y = sum(p[1] for p in self.points) // n


def compress_runs(runs):
    """
    Compress runs by combining points that are within GRID_SIZE metres.
    """

    # Map run name to list of grouped point ids.
    compressed_runs = {}

    # List of grouped points across all runs.
    # These are dicts with keys 'x', 'y', 'points', and 'id'.
    # Where points is a list of the original coordinates in the group,
    # and x, y are the averaged coordinates of the group.
    grouped_points = []
    threshold = GRID_SIZE ** 2

    def find_existing_point(coord):
        for prev in grouped_points:
            dx = coord[0] - prev.x
            dy = coord[1] - prev.y
            if dx * dx + dy * dy <= threshold:
                return prev
        return None

    for name, run in runs.items():
        compressed_run = []
        for coord in run:
            if existing_point := find_existing_point(coord):
                existing_point.add_point(coord, name)
                if len(compressed_run) == 0 or compressed_run[-1] != existing_point.id:
                    # Add this point to the run unless its the same as the last one
                    compressed_run.append(existing_point.id)
            else:
                new_point = CompressedPoint(coord[0], coord[1], len(grouped_points), name)
                grouped_points.append(new_point)
                compressed_run.append(new_point.id)

        compressed_runs[name] = compressed_run

    return compressed_runs, grouped_points


def segment_runs(runs):
    """
    Given a dict mapping a name to a run represented by a list of point ids,
    segment each run into segments that are common across runs.
    Returns a dict mapping a tuple of points ids to a count of the runs that include that segment.
    """

    # Build a mapping from each edge (a, b) to the set of run IDs that include that edge.
    edges = defaultdict(set)
    for run_id, run in runs.items():
        for a, b in zip(run, run[1:]):
            edges[(a, b)].add(run_id)

    # Convert consecutive edges with the same set of runs into larger segments.
    segments = []

    for run in runs.values():
        i = 0

        while i < len(run) - 1:
            a, b = run[i], run[i + 1]
            run_set = edges[(a, b)]

            j = i + 1

            while j < len(run) - 1:
                next_edge = (run[j], run[j + 1])

                if edges[next_edge] != run_set:
                    break

                j += 1

            segments.append(tuple(run[i:j + 1]))

            i = j

    # Count segments
    result = defaultdict(int)
    for segment in segments:
        result[segment] += 1

    return result


def run_test(test):
    segments = segment_runs(test['runs'])
    try:
        assert segments == test['expected_counts']
    except AssertionError:
        print(f"Test failed. Got: {segments}, Expected: {test['expected_counts']}")


def test_segmentation():
    test1 = {
        'runs': {
            1: (1, 2, 3, 4, 5, 6, 7),
            2: (1, 2, 3, 8, 9, 6, 7),
        },
        'expected_counts': {
            (1, 2, 3): 2,
            (3, 4, 5, 6): 1,
            (6, 7): 2,
            (3, 8, 9, 6): 1,
        }
    }
    run_test(test1)

    test2 = {
        'runs': {
            1: (1, 2, 3, 4, 5, 6),
            2: (7, 8, 9, 3, 4, 10, 11),
        },
        'expected_counts': {
            (1, 2, 3): 1,
            (3, 4): 2,
            (4, 5, 6): 1,
            (7, 8, 9, 3): 1,
            (4, 10, 11): 1,
        }
    }
    run_test(test2)

    test3 = {
        'runs': {
            1: (1, 2, 3, 4, 5),
            2: (2, 3, 4, 5, 6),
        },
        'expected_counts': {
            (1, 2): 1,
            (2, 3, 4, 5): 2,
            (5, 6): 1,
        }
    }
    run_test(test3)


def draw_compressed_points(run):
    """ Draw all the points of a run, plus it's compressed version. """

    width = 800
    margin = 16
    min_x = min(p.x for p in run)
    min_y = min(p.y for p in run)
    max_x = max(p.x for p in run)
    max_y = max(p.y for p in run)

    scale = (width - margin * 2) / (max_x - min_x)
    compress_r = round(scale * GRID_SIZE * 10) / 10
    true_r = round(scale * 4 * 10) / 10

    def scale_x(x):
        return round((x - min_x) * scale + margin, 2)

    def scale_y(y):
        return round((max_y - y) * scale + margin, 2)

    height = scale * (max_y - min_y) + margin * 2
    svg = SVG({ 'width': '100%', 'viewBox': f"0 0 {width} {height}" })
    svg.add('rect', { 'x': 0, 'y': 0, 'width': width, 'height': height, 'fill': '#f0f0f0' })

    g = svg.add('g')

    for coord in run:
        g.add('circle', {
            'cx': scale_x(coord.x),
            'cy': scale_y(coord.y),
            'r': compress_r,
            'fill': '#ff0000',
            'opacity': min(1, 0.1 * len(coord.runs))
        })
        for p in coord.points:
            g.add('circle', {
                'cx': scale_x(p[0]),
                'cy': scale_y(p[1]),
                'r': true_r,
                'opacity': 0.5,
                'fill': '#000000',
            })

    filename = os.path.join("images", "compressed_run.svg")
    svg.write(filename)


def draw_segments(segments, points):
    point_lookup = {p['id']: (p['x'], p['y']) for p in points}

    segment_coords = []
    for segment, count in segments.items():
        coords = [point_lookup[pid] for pid in segment if pid in point_lookup]
        if coords:
            segment_coords.append({'coords': coords, 'count': count})

    width = 800
    margin = 16
    min_x = min(coord[0] for segment in segment_coords for coord in segment['coords'])
    min_y = min(coord[1] for segment in segment_coords for coord in segment['coords'])
    max_x = max(coord[0] for segment in segment_coords for coord in segment['coords'])
    max_y = max(coord[1] for segment in segment_coords for coord in segment['coords'])
    scale = (width - margin * 2) / (max_x - min_x)

    # print(segment_coords)

    def scale_x(x):
        return round((x - min_x) * scale + margin, 2)

    def scale_y(y):
        return round((max_y - y) * scale + margin, 2)

    height = scale * (max_y - min_y) + margin * 2
    svg = SVG({ 'width': '100%', 'viewBox': f"0 0 {width} {height}" })
    svg.add('rect', { 'x': 0, 'y': 0, 'width': width, 'height': height, 'fill': '#f0f0f0' })
    for segment in segment_coords:
        svg.add('circle', {
            'cx': scale_x(segment['coords'][0][0]),
            'cy': scale_y(segment['coords'][0][1]),
            'r': 3,
            'fill': '#ff0000',
            'opacity': 0.5
        })
        svg.add('circle', {
            'cx': scale_x(segment['coords'][-1][0]),
            'cy': scale_y(segment['coords'][-1][1]),
            'r': 3,
            'fill': '#ff0000',
            'opacity': 0.5
        })

        points = " ".join(f"{scale_x(coord[0])},{scale_y(coord[1])}" for coord in segment['coords'])
        svg.add('polyline', { 'points': points, 'stroke': '#ff0000', 'fill': 'none', 'stroke-width': 2, 'opacity': 0.25 })

    filename = os.path.join("images", "segmented_runs.svg")
    svg.write(filename)


def main():
    runs = get_gpx_data(FOLDER, get_coords)
    # print(list(runs.keys())[0])

    runs_in_meters = runs_to_meters(runs)

    # snapped_runs = snap_runs_to_grid(runs)
    # print(list(snapped_runs.values())[0])

    limited_run_keys = (
        '2026-01-03.gpx',
        '2026-01-05.gpx',
        '2026-01-07.gpx',
        '2026-01-10.gpx',
        '2026-01-14.gpx',
        # '2026-01-24.gpx', # Two loops
        '2026-03-02.gpx', # Includes park
    )

    # limited_run_keys = list(runs_in_meters.keys())[:2]
    limited_runs = {k: runs_in_meters[k] for k in limited_run_keys}
    # print(limited_runs)

    compressed_runs, grouped_points = compress_runs(limited_runs)
    print(sum(len(run) for run in limited_runs.values()))
    print(len(grouped_points))
    # print(grouped_points)
    draw_compressed_points(grouped_points)

    # segment_counts = segment_runs(compressed_runs)
    # # print(segment_counts)
    # draw_segments(segment_counts, grouped_points)


if __name__ == "__main__":
    main()
    # test_segmentation()
