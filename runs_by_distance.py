import os
from math import ceil
from utils import get_runs_by_year, get_pace_colour, seconds_to_time
from draw_svg import SVG

DISTANCES = [0, 5, 6, 10]
SVG_HEIGHT = 800
MARGIN_X1 = 50
MARGIN_X2 = 10
MARGIN_Y1 = 20
MARGIN_Y2 = 50

BAR_GAP = 50
BAR_WIDTH = 50
STEP_SIZE = 20


def group_runs_by_distance(runs):
    """ Return a dict mapping distance to list of runs. """
    runs_by_distance = [[] for _ in DISTANCES]
    for run in runs:
        distance = run['distance']
        for i in range(len(DISTANCES) - 1, -1, -1):
            if distance > DISTANCES[i]:
                runs_by_distance[i].append(run)
                break
    return runs_by_distance


def get_svg(chart_params):
    """ Return an SVG object with some default styles applied. """
    svg = SVG({
        'viewBox': f"0 0 {chart_params['width']} {chart_params['height']}"
    })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.axis', { 'stroke-width': '1px', 'stroke': '#ddd' })
    svg.addStyle('.x-axis-label', { 'font-size': '14px', 'dominant-baseline': 'middle' })
    svg.addStyle('.x-axis-label-2', { 'font-size': '24px', 'dominant-baseline': 'middle' })
    svg.addStyle('.y-axis-label', { 'font-size': '20px', 'dominant-baseline': 'middle', 'text-anchor': 'end' })

    return svg


def draw_axes(svg, width, years, max_value, dx):
    x1 = MARGIN_X1
    x2 = width - MARGIN_X2
    y = SVG_HEIGHT - MARGIN_Y2 + 10
    section_size = BAR_WIDTH * len(years)

    # Labels for distances
    for i, distance in enumerate(DISTANCES):
        x = x1 + i * (section_size + BAR_GAP)
        label = f"{distance}"
        if i + 1 < len(DISTANCES):
            label += f" to {DISTANCES[i + 1]} km"
        else:
            label += "+ km"

        svg.add('text', {'x': x + section_size / 2, 'y': y + 24, 'class': 'x-axis-label-2'}, label)

        for j, year in enumerate(years):
            svg.add('text', {'x': x + j * BAR_WIDTH + BAR_WIDTH / 2,'y': y, 'class': 'x-axis-label'}, year)


    # Gridlines
    for i in range(0, max_value + 1, STEP_SIZE):
        y = SVG_HEIGHT - MARGIN_Y2 - i * dx
        svg.add('line', {'x1': x1, 'y1': y, 'x2': x2, 'y2': y, 'class': 'axis'})
        svg.add('text', {'x': x1 - 5, 'y': y, 'class': 'y-axis-label'}, i)


def draw_bars(svg, runs, x_start, y_base, dx):
    years = sorted(runs.keys())
    for i, year in enumerate(years):
        for j, dist in enumerate(runs[year]):
            total_pace = 0
            count = 0

            x = x_start + j * (len(years) * BAR_WIDTH + BAR_GAP) + i * BAR_WIDTH + BAR_WIDTH / 2
            bar_y = y_base
            for run in dist:
                if run['distance']:
                    if run['pace']:
                        count += 1
                        total_pace += run['pace']
                    fill = get_pace_colour(run['pace']) if run['pace'] else (200, 200, 200)
                    svg.rect(x - BAR_WIDTH / 2, bar_y - dx, BAR_WIDTH, dx, fill=fill)
                bar_y -= dx

            if count:
                mean_pace = seconds_to_time(total_pace / count * 60)
                svg.add('text', {'x': x, 'y': bar_y - 8, 'class': 'x-axis-label'}, mean_pace)


def draw_runs_by_distance(run_data, filename):
    """ Draw a chart of runs by year. """

    # Map year to array of runs by distance
    grouped_data = {year: group_runs_by_distance(runs) for year, runs in run_data.items()}

    years = sorted(run_data.keys())
    max_count = max(max(len(runs) for runs in grouped_runs) for grouped_runs in grouped_data.values())
    max_value = (ceil(max_count / STEP_SIZE)) * STEP_SIZE
    dx = (SVG_HEIGHT - MARGIN_Y1 - MARGIN_Y2) / max_value

    width = MARGIN_X1 + MARGIN_X2 + len(DISTANCES) * (len(run_data) * BAR_WIDTH + BAR_GAP)

    svg = get_svg({ 'width': width, 'height': SVG_HEIGHT })
    draw_axes(svg, width, years, max_value, dx)
    draw_bars(svg, grouped_data, MARGIN_X1, SVG_HEIGHT - MARGIN_Y2, dx)

    svg.write(filename)


if __name__ == '__main__':
    runs_by_year = get_runs_by_year()
    filename = os.path.join("images", "Runs by distance.svg")
    draw_runs_by_distance(runs_by_year, filename)
