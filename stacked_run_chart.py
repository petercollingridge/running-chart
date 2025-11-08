from math import ceil
from utils import get_runs_by_year, get_pace_colour
from draw_svg import SVG

SVG_WIDTH = 1200
SVG_HEIGHT = 800
MARGIN_X1 = 50
MARGIN_X2 = 10
MARGIN_Y1 = 10
MARGIN_Y2 = 45
BAR_HEIGHT = 5
BAR_GAP = 40


def get_svg(chart_params):
    """ Return an SVG object with some default styles applied. """
    svg = SVG({
        'viewBox': f"0 0 {chart_params['width']} {chart_params['height']}"
    })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.axis', { 'stroke-width': '1px', 'stroke': '#ddd' })
    svg.addStyle('.axis-label', { 'font-size': '24px', 'dominant-baseline': 'middle' })
    svg.addStyle('.y-axis-label', { 'font-size': '16px', 'dominant-baseline': 'middle', 'text-anchor': 'end' })

    return svg


def draw_axes(svg, max_runs):
    x1 = MARGIN_X1
    x2 = SVG_WIDTH - MARGIN_X2
    step = 20
    axis_max = (ceil((max_runs + step - 1) / step)) * step

    for i in range(0, axis_max + 1, step):
        y = SVG_HEIGHT - MARGIN_Y2 - i * BAR_HEIGHT
        svg.add('line', {'x1': x1, 'y1': y, 'x2': x2, 'y2': y, 'class': 'axis'})
        svg.add('text', {'x': x1 - 5, 'y': y, 'class': 'y-axis-label'}, i)


def draw_year_stack(svg, data, x, y, scale_width):

    bar_y = y - BAR_HEIGHT
    for run in data:
        run_width = run['distance'] * scale_width

        if not run_width:
            svg.circle(x, bar_y + BAR_HEIGHT / 2, BAR_HEIGHT / 2, fill='rgb(100, 100, 100)')
        else:
            fill = get_pace_colour(run['pace']) if run['pace'] else (200, 200, 200)
            svg.rect(x - run_width / 2, bar_y, run_width, BAR_HEIGHT, fill=fill)
        bar_y -= BAR_HEIGHT


def add_bar_labels(svg, data, year, x, y):
    data_with_pace = [run['pace'] for run in data if run['pace'] is not None]
    data_with_distance = [run['distance'] for run in data if run['distance']]
    mean_pace = sum(data_with_pace) / len(data_with_pace)
    min_distance = min(data_with_distance)
    max_distance = max(data_with_distance)
    mean_distance = sum(data_with_distance) / len(data_with_distance)

    bar_height = len(data) * BAR_HEIGHT
    svg.add('text', {'x': x, 'y': y - bar_height - 3, 'font-size': '20px', 'fill': get_pace_colour(mean_pace) }, year)

    svg.add('text', {'x': x, 'y': y + 12, 'font-size': '12px' }, f"{min_distance:.1f}km")
    svg.add('text', {'x': x, 'y': y + 25, 'font-size': '12px' }, f"{mean_distance:.1f}km")
    svg.add('text', {'x': x, 'y': y + 38, 'font-size': '12px' }, f"{max_distance:.1f}km")


def draw_year_stacks(svg, data, y, bar_gap):
    """ Draw a series of year bars. """

    chart_width = SVG_WIDTH - MARGIN_X1 - MARGIN_X2
    num_years = len(data)
    max_dist_for_year = sum(max(run['distance'] for run in year_data) for year_data in data.values()) 
    scale_width = (chart_width - bar_gap * (num_years + 1)) / max_dist_for_year

    x = MARGIN_X1 + bar_gap

    years = sorted(data.keys())
    for year in years:
        year_data = data[year]
        max_dist = max(run['distance'] for run in year_data) if year_data else 0
        bar_width = max_dist * scale_width
        x += bar_width / 2

        # Draw axis lines
        for d in range(5, int(max_dist) + 1, 5):
            dx = scale_width * d / 2
            svg.add('line', {'x1': x - dx, 'y1': y, 'x2': x - dx, 'y2': MARGIN_Y1, 'class': 'axis'})
            svg.add('line', {'x1': x + dx, 'y1': y, 'x2': x + dx, 'y2': MARGIN_Y1, 'class': 'axis'})

        add_bar_labels(svg, year_data, year, x, y)

        # Draw bars
        draw_year_stack(svg, year_data, x, y, scale_width)
        x += bar_width / 2 + bar_gap


def draw_stacked_runs(runs_by_year, filename):
    """ Draw a chart of runs by year. """

    svg = get_svg({ 'width': SVG_WIDTH, 'height': SVG_HEIGHT })
    max_runs = max(len(runs) for runs in runs_by_year.values())

    draw_axes(svg, max_runs)
    draw_year_stacks(svg, runs_by_year, SVG_HEIGHT - MARGIN_Y2, BAR_GAP)

    svg.write(filename)


if __name__ == '__main__':
    runs_by_year = get_runs_by_year()
    draw_stacked_runs(runs_by_year, "Stacked run chart.svg")
