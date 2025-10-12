import os
from calendar import month_abbr

from utils import read_data, seconds_to_time
from draw_svg import SVG

SVG_WIDTH = 1200
SVG_HEIGHT = 800
MARGIN_X1 = 30
MARGIN_X2 = 10
MARGIN_Y1 = 10
MARGIN_Y2 = 40
BAR_HEIGHT = 5
MIN_PACE = 4.0
MAX_PACE = 6.5


def get_runs_by_year(folder = 'data'):
    """ Return a dict mapping year (str) to list run dicts. """
    runs_by_year = {}
    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            year = filename[:-4]
            filepath = os.path.join(folder, filename)
            runs_by_year[year] = read_data(filepath)
    return runs_by_year


def get_svg(chart_params):
    """ Return an SVG object with some default styles applied. """
    svg = SVG({
        'viewBox': f"0 0 {chart_params['width']} {chart_params['height']}"
    })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.plot-line', { 'fill': 'none', 'stroke-width': '3px', 'opacity': '0.8', 'stroke': 'currentColor' })
    svg.addStyle('.plot-area', { 'fill': 'currentColor', 'opacity': '0.25' })
    svg.addStyle('.plot-point', { 'opacity': '0.8', 'fill': 'currentColor', 'stroke': 'white', 'stroke-width': '1px' })
    svg.addStyle('.axis', { 'stroke-width': '1px', 'stroke': '#ddd' })
    svg.addStyle('.series-label', { 'font-size': '16px', 'dominant-baseline': 'middle', 'text-anchor': 'start' })
    svg.addStyle('.y-axis-label', { 'font-size': '16px', 'dominant-baseline': 'middle', 'text-anchor': 'end' })

    return svg


def scale_pace(pace, min_pace=MIN_PACE, max_pace=MAX_PACE):
    """ Scale pace (min/km) to y coordinate. """
    return MARGIN_Y1 + (max_pace - pace) / (max_pace - min_pace) * (SVG_HEIGHT - MARGIN_Y1 - MARGIN_Y2)


def get_colours(years):
    """ Return a dict mapping year to colour. """
    colours = {}
    blue_step = 255 // len(years)
    green_step = 200 // (len(years) - 1)

    for i, year in enumerate(years):
        blue = 255 - i * blue_step
        green = 200 - i * green_step
        colours[year] = f'rgb(0, {green}, {blue})'

    return colours


def draw_axes(svg):
    x1 = MARGIN_X1
    x2 = SVG_WIDTH - MARGIN_X2
    y1 = MARGIN_Y1
    y2 = SVG_HEIGHT - MARGIN_Y2

    scale_x = (x2 - x1) / 11
    svg.add('line', {'x1': x1, 'y1': y2, 'x2': x2, 'y2': y2, 'class': 'axis'})

    # Months
    for month in range(12):
        x = x1 + month * scale_x
        svg.add('line', {'x1': x, 'y1': y1, 'x2': x, 'y2': y2 + 5, 'class': 'axis'})
        svg.add('text', {'x': x, 'y': y2 + 20, 'class': 'axis-label'}, month_abbr[month + 1])

    # Pace
    pace = MIN_PACE
    while pace <= MAX_PACE:
        y = scale_pace(pace)
        svg.add('line', {'x1': x1 - 5, 'y1': y, 'x2': x2, 'y2': y, 'class': 'axis'})
        svg.add('text', {'x': x1 - 10, 'y': y, 'class': 'y-axis-label'}, seconds_to_time(pace*60))
        pace += 0.25


def draw_year_line(svg, data, year):
    """ Draw a line for a single year. """

    x1 = MARGIN_X1
    x2 = SVG_WIDTH - MARGIN_X2
    chart_width = x2 - x1
    scale_x = chart_width / 11
    scale_dist = 0.16

    points = []
    for month in range(1, 13):
        month_name = month_abbr[month]
        month_runs = [run for run in data if run['month'] == month_name]
        total_distance = sum(run['distance'] for run in month_runs)
        runs_with_pace = [run for run in month_runs if run['pace']]
        mean_pace = (sum(run['pace'] for run in runs_with_pace) / len([run for run in runs_with_pace])) if runs_with_pace else None

        if mean_pace:
            x = x1 + (month - 1) * scale_x
            y = scale_pace(mean_pace)
            points.append((x, y, total_distance))

    path_data = "M " + " L ".join(f"{x},{y}" for x, y, _ in points)
    svg.add('path', { 'd': path_data, 'class': f"year-{year} plot-line" })
    svg.add('text', {'x': points[-1][0] + 5, 'y': points[-1][1], 'class': 'series-label'}, year)

    for x, y, d in points:
        r = d * scale_dist
        svg.circle(x, y, r, classname = f"year-{year} plot-point")


def draw_year_area(svg, data, year):
    """ Draw a filled area for a single year. """

    x1 = MARGIN_X1
    x2 = SVG_WIDTH - MARGIN_X2
    chart_width = x2 - x1
    scale_x = chart_width / 11

    min_values = []
    max_values = []
    med_values = []
    for month in range(1, 13):
        x = x1 + (month - 1) * scale_x
        month_name = month_abbr[month]
        month_runs = [run for run in data if run['month'] == month_name]
        runs_with_pace = [run for run in month_runs if run['pace']]
        n = len(runs_with_pace)
        sorted_paces = sorted(run['pace'] for run in runs_with_pace)

        median_pace = sorted_paces[n // 2] if n % 2 == 1 else (sorted_paces[n // 2 - 1] + sorted_paces[n // 2]) / 2 if n > 0 else None
        # min_pace = min(run['pace'] for run in runs_with_pace) if runs_with_pace else None
        # max_pace = max(run['pace'] for run in runs_with_pace) if runs_with_pace else None
        min_pace = sorted_paces[n // 4] if n >= 4 else (sorted_paces[0] if n > 0 else None)
        max_pace = sorted_paces[(3 * n) // 4] if n >= 4 else (sorted_paces[-1] if n > 0 else None)

        if min_pace:
            min_values.append((x, scale_pace(min_pace)))
        if max_pace:
            max_values.append((x, scale_pace(max_pace)))
        if median_pace:
            med_values.append((x, scale_pace(median_pace)))

    path_data = "M " + " L ".join(f"{x},{y}" for x, y in min_values + list(reversed(max_values))) + " Z"
    svg.add('path', { 'd': path_data, 'class': f"year-{year} plot-area" })
    
    path_data = "M " + " L ".join(f"{x},{y}" for x, y in med_values)
    svg.add('path', { 'd': path_data, 'class': f"year-{year} plot-line" })
    svg.add('text', {'x': med_values[-1][0] + 5, 'y': med_values[-1][1], 'class': 'series-label'}, year)


def draw_runs_by_month(runs_by_year, filename, draw_func):
    """ Draw a chart of runs by month. """

    svg = get_svg({ 'width': SVG_WIDTH, 'height': SVG_HEIGHT })
    draw_axes(svg)

    years = sorted(runs_by_year.keys())
    colours = get_colours(years)

    for year in years:
        svg.addStyle(f".year-{year}", { 'color': colours[year] })
        draw_func(svg, runs_by_year[year], year)

    svg.write(filename)


if __name__ == '__main__':
    runs_by_year = get_runs_by_year()
    # draw_runs_by_month(runs_by_year, "Runs by month line chart.svg", draw_year_line)
    draw_runs_by_month(runs_by_year, "Runs by month area chart.svg", draw_year_area)
