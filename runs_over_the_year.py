from math import ceil

from utils import get_colours_for_year, get_runs_by_year
from draw_svg import SVG

SVG_WIDTH = 1200
SVG_HEIGHT = 800
MARGIN_X1 = 50
MARGIN_X2 = 50
MARGIN_Y1 = 10
MARGIN_Y2 = 40

DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def date_to_day_of_year(month, day):
    """ Convert month and day to day of year (0-365). """
    month_n = MONTHS.index(month)
    return sum(DAYS[:month_n]) + day


def get_svg(chart_params):
    """ Return an SVG object with some default styles applied. """
    svg = SVG({
        'viewBox': f"0 0 {chart_params['width']} {chart_params['height']}"
    })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.plot-line', { 'fill': 'none', 'stroke-width': '3px', 'opacity': '0.8', 'stroke': 'currentColor' })
    svg.addStyle('.plot-area', { 'fill': 'currentColor', 'opacity': '0.25' })
    svg.addStyle('.plot-point', { 'opacity': '0.8', 'fill': 'currentColor', 'stroke': 'white', 'stroke-width': '1px' })
    svg.addStyle('.axis', { 'stroke-width': '1px', 'stroke': 'black', 'opacity': '0.1' })
    svg.addStyle('.series-label', { 'font-size': '16px', 'dominant-baseline': 'middle', 'text-anchor': 'start', 'color': 'currentColor' })
    svg.addStyle('.y-axis-label', { 'font-size': '16px', 'dominant-baseline': 'middle', 'text-anchor': 'end' })

    return svg


def draw_axes(svg, max_distance):
    x1 = MARGIN_X1
    x2 = SVG_WIDTH - MARGIN_X2
    y1 = MARGIN_Y1
    y2 = SVG_HEIGHT - MARGIN_Y2

    step_distance = 50
    max_distance_rounded = ceil(max_distance / step_distance) * step_distance
    step = (y2 - y1) / max_distance_rounded

    scale_y = lambda d: y2 - d * step

    for distance in range(0, max_distance_rounded + 1, step_distance):
        y = scale_y(distance)

        svg.add('line', {'x1': x1 - 4, 'y1': y, 'x2': x2, 'y2': y, 'class': 'axis'})
        svg.add('text', {'x': x1 - 8, 'y': y, 'class': 'y-axis-label'}, distance)

    for month in range(12):
        days_before = sum(DAYS[:month])
        x = (x2 - x1) * days_before / 366 + x1

        svg.add('line', {'x1': x, 'y1': y1, 'x2': x, 'y2': y2 + 4, 'class': 'axis'})
        svg.add('text', {'x': x + (DAYS[month] * (x2 - x1) / 366) / 2, 'y': y2 + 20, 'class': 'axis-label'}, MONTHS[month])

    svg.add('line', {'x1': x1, 'y1': y1, 'x2': x1, 'y2': y2, 'class': 'axis'})

    return scale_y


def draw_year_line(svg, data, colour, scale_y, year, this_year):
    total_distance = 0
    points = [MARGIN_X1, scale_y(0)]
    scale_x = (SVG_WIDTH - MARGIN_X1 - MARGIN_X2) / 366

    for run in data:
        month = run['month']
        day = int(run['day'])
        days_since_start = date_to_day_of_year(month, day)
        x = scale_x * days_since_start + MARGIN_X1

        points.extend([x, scale_y(total_distance)])
        total_distance += run['distance']
        points.extend([x, scale_y(total_distance)])

    if not this_year:
        points.extend([SVG_WIDTH - MARGIN_X2, scale_y(total_distance)])

    svg.add('polyline', { 'points': ' '.join(map(str, points)), 'class': 'plot-line', 'color': colour })
    svg.add('text', { 'x': SVG_WIDTH - MARGIN_X2 + 5, 'y': scale_y(total_distance), 'class': 'series-label', 'color': colour }, year)


def draw_chart(data, filename):
    svg = get_svg({ 'width': SVG_WIDTH, 'height': SVG_HEIGHT })

    max_distance = max(
        sum((run['distance'] for run in runs))
        for runs in data.values()
    )

    scale_y = draw_axes(svg, max_distance)

    years = sorted(data.keys())
    colours = get_colours_for_year(years)

    for year in years:
        runs = data[year]
        draw_year_line(svg, runs, colours[year], scale_y, year, year == max(years))

    svg.write(filename)


if __name__ == '__main__':
    runs_by_year = get_runs_by_year()
    draw_chart(runs_by_year, "Runs by year.svg")
