import os
from math import ceil, floor
from utils import get_runs_by_year, get_pace_colour, seconds_to_time
from collections import defaultdict
from draw_svg import SVG

SCATTER_WIDTH = 1000
SCATTER_HEIGHT = 160
MARGIN_X1 = 100
MARGIN_X2 = 10
MARGIN_Y1 = 20
MARGIN_Y2 = 20
DOT_RADIUS = 4


def get_svg(chart_params):
    """ Return an SVG object with some default styles applied. """
    svg = SVG({
        'viewBox': f"0 0 {chart_params['width']} {chart_params['height']}"
    })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.axis', { 'stroke-width': '1px', 'stroke': 'black', 'opacity': '0.4' })
    svg.addStyle('.axis-2', { 'stroke-width': '1px', 'stroke': 'black', 'opacity': '0.1' })
    svg.addStyle('.count-label', { 'font-size': '12px', 'dominant-baseline': 'hanging'})
    svg.addStyle('circle', { 'fill-opacity': 0.5 })
    svg.addStyle('text.x-axis-label-top', { 'font-size': '12px', 'dominant-baseline': 'baseline' })
    svg.addStyle('text.x-axis-label-bot', { 'font-size': '12px', 'dominant-baseline': 'hanging' })
    svg.addStyle('text.y-axis-label-big', { 'font-size': '20px', 'dominant-baseline': 'middle', 'text-anchor': 'start' })
    svg.addStyle('text.y-axis-label-small', { 'font-size': '12px', 'dominant-baseline': 'middle', 'text-anchor': 'end' })

    return svg


def group_runs_by_distance(runs):
    """ Group runs by distance (rounded down to nearest 5). """

    grouped_runs = defaultdict(list)
    for run in runs:
        if run['distance']:
            distance = int(run['distance']) // 5 * 5  # Round down to nearest 5
            grouped_runs[distance].append(run)

    return grouped_runs


def draw_run_scatter_plots(runs_by_year, filename):
    svg_width = SCATTER_WIDTH + MARGIN_X1 + MARGIN_X2
    svg_height = SCATTER_HEIGHT * len(runs_by_year) + MARGIN_Y1 + MARGIN_Y2
    svg = get_svg({ 'width': svg_width, 'height': svg_height })
    # svg.add('rect', {'x': 0, 'y': 0, 'width': svg_width, 'height': svg_height, 'fill': '#f8f8f8'})

    x2 = svg_width - MARGIN_X2

    max_dist = max(run['distance'] for runs in runs_by_year.values() for run in runs if run['distance'])
    max_dist = ceil(max_dist / 5) * 5  # Round up to nearest 5
    scale_x = lambda distance: round(MARGIN_X1 + (distance / max_dist) * SCATTER_WIDTH)

    min_pace = min(run['pace'] for runs in runs_by_year.values() for run in runs if run['pace'])
    min_pace = floor(min_pace * 4) / 4  # Round down to nearest 15s
    min_pace_2 = ceil(min_pace * 2) / 2  # Round up to nearest 30s
    max_pace = max(run['pace'] for runs in runs_by_year.values() for run in runs if run['pace'])
    max_pace = ceil(max_pace * 4) / 4  # Round up to nearest 15s
    max_pace_2 = floor(max_pace * 2) / 2  # Round down to nearest 30s
    scale_y = lambda pace: round((max_pace - pace) / (max_pace - min_pace) * SCATTER_HEIGHT)
    
    # print(f"Min pace: {min_pace}, Max pace: {max_pace}")
    # print(f"Min pace: {seconds_to_time(min_pace*60)}, Max pace: {seconds_to_time(max_pace*60)}")

    axis_group_2 = svg.add('g')
    axis_group_1 = svg.add('g')

    axis_group_1.add('line', {'x1': MARGIN_X1, 'y1': MARGIN_Y1, 'x2': x2, 'y2': MARGIN_Y1, 'class': 'axis'})

    # Plot runs
    for i, year in enumerate(sorted(runs_by_year.keys())):
        runs_for_year = runs_by_year[year]
        y1 = MARGIN_Y1 + i * SCATTER_HEIGHT
        y2 = y1 + SCATTER_HEIGHT

        grouped_runs = group_runs_by_distance(runs_for_year)
        for distance, runs_for_dist in grouped_runs.items():
            x = (scale_x(distance) + scale_x(distance + 5)) / 2
            count = len(runs_for_dist)
            median_pace = sorted(run['pace'] for run in runs_for_dist if run['pace'])[count // 2]
            text = f"{count} | {seconds_to_time(median_pace * 60)}"
            svg.add('text', {'x': x + 3, 'y': y1 + 3, 'class': 'count-label'}, text)

        # axis lines
        axis_group_1.add('line', {'x1': MARGIN_X1, 'y1': y2, 'x2': x2, 'y2': y2, 'class': 'axis'})
        for pace in range(int(min_pace_2 * 60), int(max_pace_2 * 60) + 1, 30):
            y = y1 + scale_y(pace / 60)
            axis_group_2.add('line', {'x1': MARGIN_X1, 'y1': y, 'x2': x2, 'y2': y, 'class': 'axis-2'})
            axis_group_2.add('text', {'x': MARGIN_X1 - 3, 'y': y, 'class': 'y-axis-label-small'}, str(seconds_to_time(pace)))

        # Draw year label
        svg.add('text', {'x': 10, 'y': y1 + SCATTER_HEIGHT / 2, 'class': 'y-axis-label-big'}, str(year))

        # Draw runs as circles
        for run in runs_for_year:
            if run['pace'] is None:
                continue  # Skip runs with missing pace or distance
            x = scale_x(run['distance'])
            y = y1 + scale_y(run['pace'])
            colour = get_pace_colour(run['pace'])
            svg.add('circle', {'cx': x, 'cy': y, 'r': DOT_RADIUS, 'fill': colour})

    # Axis lines and labels
    for i, distance in enumerate(range(max_dist + 1)):
        axis = 'axis' if distance % 5 == 0 else 'axis-2'
        axis_group = axis_group_1 if distance % 5 == 0 else axis_group_2
        x = scale_x(distance)
        if axis:
            axis_group.add('line', {'x1': x, 'y1': MARGIN_Y1, 'x2': x, 'y2': svg_height - MARGIN_Y2, 'class': axis})
            axis_group.add('text', {'x': x, 'y': MARGIN_Y1 - 5, 'class': 'x-axis-label-top'}, str(distance))
            axis_group_1.add('text', {'x': x, 'y': svg_height - MARGIN_Y2 + 5, 'class': 'x-axis-label-bot'}, str(distance))

    # Save the SVG to a file
    svg.write(filename)


if __name__ == '__main__':
    runs_by_year = get_runs_by_year()
    filename = os.path.join("images", "Run scatter plots.svg")
    draw_run_scatter_plots(runs_by_year, filename)
