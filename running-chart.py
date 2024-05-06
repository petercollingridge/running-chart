import os
import sys
from collections import defaultdict
from calendar import month_abbr
from datetime import date, datetime
from draw_svg import SVG
from math import floor

colours = (
    (6.25, (0, 0, 0)),      # Black
    (5.75, (200, 0, 0)),    # Red
    (5, (250, 240, 0)),     # Yellow
    (4.75, (0, 200, 0)),    # Green
    (4.5, (0, 0, 200)),     # Blue
    (4, (0, 0, 50)),        # Dark blue
)

def _get_day_in_month(year, month):
    """ Given a year and month, return the number of days in the month. """
    if month == 12:
        return 31
    return (datetime(year, month + 1, 1) - datetime(year, month, 1)).days


def _get_colour(x):
    for i, colour in enumerate(colours):
        if x > colour[0]:
            # Propotion of the way through this band
            t1, c1 = colour
            t2, c2 = colours[i - 1]
            p = (x - t1) / (t2 - t1)
            return [round(c2[n] * p + c1[n] * (1 - p)) for n in range(3)]


def _get_stats(arr):
    """ Given an array of numbers return a tuple of minimum, median, and maximum. """
    filtered_arr = [item for item in arr if item]
    return (
        ('Min', min(filtered_arr)),
        ('Med', sorted(filtered_arr)[len(filtered_arr) // 2]),
        ('Max', max(filtered_arr)),
    )


def _seconds_to_time(s):
    minutes = floor(s / 60)
    seconds = s % 60
    return f"{minutes}:{seconds:02d}"


def _seconds_to_duration(s):
    hours = floor(s / 3600)
    minutes = floor((s % 3600) / 60)
    return f"{hours}hrs {minutes} mins"


def read_data(filename):
    run_data = []
    with open(filename, 'r') as f:
        for line in f:
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


def get_week_data(run_data, year):
    # Find number of first week, which will be 52 unless the first day is a Monday
    first_week = datetime.strptime(f'1 Jan {year}', '%d %b %Y').isocalendar()[1]
    offset = 1 if first_week == 1 else 0

    for data in run_data:
        run_date = datetime.strptime(f"{data['day']} {data['month']} {year}", '%d %b %Y')
        position = run_date.isocalendar()

        # At the beginning of the year the iso week can be in the previous year
        if position[0] < year:
            data['week'] = 0
        else:
            data['week'] = position[1] - offset

        data['day_of_week'] = position[2]


def get_day_positions(year):
    """
    Given a year, return an array of dict with x, y and month attibutes,
    representing the position of days on a grid representing the calendar
    """

    week_num = 0
    month = 1
    weekday = date(year, 1, 1).weekday()

    positions_by_month = []

    while month <= 12:
        if month > len(positions_by_month):
            days = []
            days_in_month = _get_day_in_month(year, month)
            positions_by_month.append({
                'name': month_abbr[month],
                'days': days
            })

        days.append({'x': week_num, 'y': weekday })

        # Move to the next day of the week
        weekday += 1
        if weekday > 6:
            weekday = 0
            week_num += 1

        # Count down to see if we reach the end of the month
        days_in_month -= 1
        if days_in_month == 0:
            month += 1

    return positions_by_month


def get_counts(run_data):
    # Write count of runs each week and for each day of the week
    day_of_week_count = defaultdict(int)
    week_num_count = defaultdict(int)
    month_count = defaultdict(int)
    month_dist = defaultdict(int)

    for data in run_data:
        day_of_week_count[data['day_of_week']] += 1
        week_num_count[data['week']] += 1
        month_count[data['month']] += 1
        month_dist[data['month']] += data['distance']

    return {
        'day_of_week': day_of_week_count,
        'week_num': week_num_count,
        'month': month_count,
        'month_dist': month_dist
    }


def get_svg(chart_params):
    svg = SVG({
        'viewBox': f"0 0 {chart_params['width']} {chart_params['height']}"
    })
    svg.addStyle('.month-1', { 'fill': '#ccc' })
    svg.addStyle('.month-2', { 'fill': '#e2e2e2' })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.axis-label', { 'font-size': '24px', 'dominant-baseline': 'middle' })

    svg.addStyle('circle', {'fill-opacity': 0.7, 'stroke': 'white'})
    svg.addStyle('.cross', {'opacity': 0.7, 'stroke': 'rgb(60, 52, 52)', 'stroke-width': 3, 'stroke-linecap': 'round'})
    svg.addStyle('.count', {'font-size': '17px', 'dominant-baseline': 'middle'})
    svg.addStyle('.title', {'font-size': '40px', 'dominant-baseline': 'middle', 'fill': '#222'})
    svg.addStyle('.subtitle', {'font-size': '24px', 'dominant-baseline': 'middle', 'fill': '#777'})

    # svg.rect(0, 0, chart_params['width'], chart_params['height'], fill = '#ddd')
    return svg


def write_title(svg, x, y, run_data):
    # Subtitle
    distances = [d['distance'] for d in run_data]
    total_distance = sum(distances)
    total_time = sum(d['time'] for d in run_data)
    mean_pace = round(total_time / total_distance)

    subtitle = ' | '.join([
        f"{len(distances)} runs",
        f"{round(total_distance)} km",
        f"{_seconds_to_duration(total_time)}",
        f"{_seconds_to_time(mean_pace)}",
    ])

    svg.add('text', {'x': x, 'y': y, 'class': 'title'}, child=year)
    svg.add('text', {'x': x, 'y': y + 36, 'class': 'subtitle'}, child=subtitle)   


def draw_calendar(svg, chart_params, day_positions):
    # Draw a rect per day, coloured by month
    rect_size = chart_params['size'] - 1
    for i, month in enumerate(day_positions):
        classname = f"month-{1 + i % 2}"

        for day in month['days']:
            x, y = chart_params['coords'](day['x'], day['y'])
            svg.rect(x, y, rect_size, rect_size, classname=classname)


def draw_runs(svg, chart_params, run_data):
    # Draw circles on chart
    run_data.sort(key = lambda x: x['distance'], reverse = True)
    for data in run_data:
        x, y = chart_params['coords'](data['week'] + 0.5, data['day_of_week'] - 0.5)

        if data['pace']:
            colour = _get_colour(data['pace'])
            fill = f"rgb({colour[0]}, {colour[1]}, {colour[2]})"
            r = chart_params['radius'](data['distance'])
            svg.circle(x, y, r, fill=fill)
        else:
            r = size * 0.2
            d = f"M{x - r} {y - r}l{r * 2} {r * 2}"
            d += f"M{x - r} {y + r}l{r * 2} {r * -2}"
            svg.add('path', {'d': d, 'class': 'cross'})


def write_labels(svg, chart_params, counts):
    count_group = svg.add('g', {'class': 'count'})
    label_group = svg.add('g', {'class': 'axis-label'})
    coords = chart_params['coords']

    # Write days of the week as y-axis label
    for index, day in enumerate('MTWTFSS'):
        x, y = coords(-0.5, index + 0.5)
        label_group.add('text', {'x': x, 'y': y}, child=day)

    # Write count of runs by week
    for week_num, count in counts['week_num'].items():
        x, y = coords(week_num + 0.5, 7.5)
        count_group.add('text', {'x': x, 'y': y}, child=count)

    # Write count of runs by day of week
    for day, count in counts['day_of_week'].items():
        x, y = coords(53.5, day - 0.5)
        count_group.add('text', {'x': x, 'y': y}, child=count)

    # Add total runs for the year
    total = sum(counts['day_of_week'].values())
    x, y = coords(53.5, 7.5)
    count_group.add('text', {'x': x, 'y': y}, child=total)


def write_months(svg, chart_params, day_positions, counts):
    label_group = svg.add('g', {'class': 'axis-label'})

    for month in day_positions:
        # Align month based on the mid-point of the days along the top of the grid
        first_day = month['days'][0]
        x1 = first_day['x'] if first_day['y'] == 0 else first_day['x'] + 1
        x2 = month['days'][-1]['x']

        mid_x = (x1 + x2 + 1) * 0.5
        x, y = chart_params['coords'](mid_x, -1)

        transform = f"translate({x} {y})"
        month_group = label_group.add('g', {'transform': transform })
        month_group.add('text', {}, child=month['name'])

        count = counts['month'].get(month['name'])
        dist = counts['month_dist'].get(month['name'])
        if count:
            text = f"{count} runs | {round(dist)} km"
            month_group.add('text', {'y': size * 0.7, 'class': 'count'}, child=text)


def draw_distance_key(svg, chart_params, run_data, x, y):
    # Shortest, median and longest distances
    distances = [d['distance'] for d in run_data]
    distance_stats = _get_stats(distances)

    cx = x
    for _, (name, d) in enumerate(distance_stats):
        r = chart_params['radius'](d)
        dx = max(r, size / 2) + 5
        cx += dx
        cy = y - r - 16
        svg.circle(cx, cy, r, fill="rgb(140, 140, 140)")
        svg.add('text', {'x': cx, 'y': y}, child=round(d, 2))
        svg.add('text', {'x': cx, 'y': y + 16}, child=name)
        cx += dx

    svg.add('text', {'x': (x + cx) / 2, 'y': y + 48, 'font-size': '24px'}, child="Distance (km)")


def draw_pace_key(svg, chart_params, run_data, x, y):
    # Fastest, median and slowest distances
    paces = [d['pace'] for d in run_data]
    paceTypes = _get_stats(paces)
    
    min_seconds = round(paceTypes[0][1] * 60)
    med_seconds = round(paceTypes[1][1] * 60)
    max_seconds = round(paceTypes[2][1] * 60)

    cy = y - chart_params['size'] * 1.5
    max_width = size * 6
    med_drawn = False

    svg.add('text', {'x': x, 'y': y}, child=_seconds_to_time(max_seconds))
    svg.add('text', {'x': x, 'y': y + 16}, child='Max')

    for dx in range(max_width):
        p = dx / (max_width - 1)
        seconds = p * min_seconds + (1 - p) * max_seconds
        colour = _get_colour(seconds / 60)
        fill = f"rgb({colour[0]}, {colour[1]}, {colour[2]})"
        svg.rect(x + dx, cy, 1.1, size, fill=fill)

        if not med_drawn and seconds <= med_seconds:
            med_drawn = True
            svg.add('text', {'x': x + dx, 'y': y}, child=_seconds_to_time(med_seconds))
            svg.add('text', {'x': x + dx, 'y': y + 16}, child='Med')

    svg.add('text', {'x': x + max_width, 'y': y}, child=_seconds_to_time(min_seconds))
    svg.add('text', {'x': x + max_width, 'y': y + 16}, child='Min')
    svg.add('text', {'x': x + max_width / 2, 'y': y + 48, 'font-size': '24px'}, child="Pace (min / km)")


def draw_chart(filename, size, year):
    target_dist = 5

    run_data = read_data(filename)
    get_week_data(run_data, year)
    day_positions = get_day_positions(year)
    counts = get_counts(run_data)

    # Chart parameters for layout
    margin_x = size * 2
    chart_y = size * 5
    key_y = chart_y + 7 * size + size * 4.5
    width = (day_positions[-1]['days'][-1]['x'] + 1) * size + margin_x * 2
    height = key_y + size

    chart_params = {
        'size': size,
        'margin_x': margin_x,
        'chart_y': chart_y,
        'width': width,
        'height': height,
        'coords': lambda x, y: (margin_x + x * size, chart_y + y * size),
        'radius': lambda x: x / target_dist * size / 2,
    }

    # svg = draw_calendar(day_positions, size)
    # add_runs(svg, run_data, year, size)
    # svg.write(f"Running {year}")

    svg = get_svg(chart_params)

    write_title(svg, width * 0.5, 36, run_data)
    draw_calendar(svg, chart_params, day_positions)
    draw_runs(svg, chart_params, run_data)
    write_labels(svg, chart_params, counts)
    write_months(svg, chart_params, day_positions, counts)
    draw_distance_key(svg, chart_params, run_data, margin_x, key_y)
    draw_pace_key(svg, chart_params, run_data, margin_x + size * 8, key_y)

    svg.write('test')


if __name__ == '__main__':
    year = 2024 if len(sys.argv) == 1 else int(sys.argv[1])
    size = 32
    filename = os.path.join('data', f"{year}.txt")

    draw_chart(filename, size, year)
