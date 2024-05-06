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


def get_day_positions(year):
    """
    Given a year, return an array of dict with x, y and month attibutes,
    representing the position of days on a grid representing the calendar
    """

    week_num = 0
    month = 1
    weekday = date(year, 1, 1).weekday()
    days_in_month = _get_day_in_month(year, month)

    day_positions = []
    while month <= 12:
        day_positions.append({
            'x': week_num,
            'y': weekday,
            'month': month
        })

        # Move to the next day of the week
        weekday += 1
        if weekday > 6:
            weekday = 0
            week_num += 1

        # Count down to see if we reach the end of the month
        days_in_month -= 1
        if days_in_month == 0:
            month += 1
            if month > 12:
                break
            days_in_month = _get_day_in_month(year, month)

    return day_positions


def draw_calendar(day_positions, size):
    margin_x = size * 2
    margin_y = size * 5
    width = (day_positions[-1]['x'] + 1) * size + margin_x * 2
    height = 8 * size + margin_y * 2
    viewbox = f"0 0 {width} {height}"

    svg = SVG({ 'viewBox': viewbox })
    svg.addStyle('.month-1', { 'fill': '#e2e2e2' })
    svg.addStyle('.month-2', { 'fill': '#ccc' })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.axis-label', { 'font-size': '24px', 'dominant-baseline': 'middle' })

    # svg.rect(0, 0, width, height, fill = '#ddd')

    label_group = svg.add('g', {'class': 'axis-label'})

    # Write days of the week as y-axis label
    for y, day in enumerate('MTWTFSS'):
        tx = margin_x - size / 2
        ty = (y + 0.5) * size + margin_y
        label_group.add('text', {'x': tx, 'y': ty}, child=day)

    # Collect months to find mean position
    months = defaultdict(list)

    # Draw a rect per day, coloured by month
    for day in day_positions:
        x = day['x'] * size + margin_x
        y = day['y'] * size + margin_y
        classname = f"month-{1 + day['month'] % 2}"
        svg.rect(x, y, size - 1, size - 1, classname=classname)

        if day['y'] == 0:
            months[day['month']].append(x)

    # Write month names as x-axis labels
    svg.groups = {}
    for month, x_values in months.items():
        mean_x = round(sum(x_values) / len(x_values)) + size / 2
        month_str = month_abbr[month]
        transform = f"translate({mean_x} {margin_y - size})"
        month_group = label_group.add('g', {'transform': transform })
        month_group.add('text', {}, child=month_str)
        svg.groups[month_str] = month_group

    return svg


def add_runs(svg, run_data, year, size, target_dist=5):
    margin_x = size * 2
    margin_y = size * 5

    # Styles
    svg.addStyle('circle', {'fill-opacity': 0.7, 'stroke': 'white'})
    svg.addStyle('.cross', {'opacity': 0.7, 'stroke': 'rgb(60, 52, 52)', 'stroke-width': 3, 'stroke-linecap': 'round'})
    svg.addStyle('.count', {'font-size': '17px', 'dominant-baseline': 'middle'})
    svg.addStyle('.title', {'font-size': '40px', 'dominant-baseline': 'middle', 'fill': '#222'})
    svg.addStyle('.subtitle', {'font-size': '24px', 'dominant-baseline': 'middle', 'fill': '#777'})

    # Title
    mid_x = 26.5 * size + margin_x
    svg.add('text', {'x': mid_x, 'y': 20 + size / 2, 'class': 'title'}, child=year)

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
    svg.add('text', {'x': mid_x, 'y': 40 + size, 'class': 'subtitle'}, child=subtitle)    

    count_group = svg.add('g', {'class': 'count'})
    day_of_week_count = defaultdict(int)
    week_num_count = defaultdict(int)
    month_count = defaultdict(int)
    month_dist = defaultdict(int)

    # Find number of first week, which will be 52 unless the first day is a Monday
    first_week = datetime.strptime(f'1 Jan {year}', '%d %b %Y').isocalendar()[1]
    offset = 1 if first_week == 1 else 0

    # Draw circles on chart
    run_data.sort(key = lambda x: x['distance'], reverse = True)
    for data in run_data:
        run_date = datetime.strptime(f"{data['day']} {data['month']} {year}", '%d %b %Y')
        position = run_date.isocalendar()

        # At the beginning of the year the iso week can be in the previous year
        if position[0] < year:
            week = 0
        else:
            week = position[1] - offset

        day_of_week = position[2]
        x = (week + 0.5) * size + margin_x
        y = (day_of_week - 0.5) * size + margin_y

        if data['pace']:
            colour = _get_colour(data['pace'])
            fill = f"rgb({colour[0]}, {colour[1]}, {colour[2]})"
            r = data['distance'] / target_dist * size / 2
            svg.circle(x, y, r, fill=fill)
        else:
            r = size * 0.2
            d = f"M{x - r} {y - r}l{r * 2} {r * 2}"
            d += f"M{x - r} {y + r}l{r * 2} {r * -2}"
            svg.add('path', {'d': d, 'class': 'cross'})

        day_of_week_count[day_of_week] += 1
        week_num_count[week] += 1
        month_count[data['month']] += 1
        month_dist[data['month']] += data['distance']

    # Write count of runs by day of week
    x = 53.5 * size + margin_x
    for day, count in day_of_week_count.items():
        y = margin_y + (day - 0.5) * size
        count_group.add('text', {'x': x, 'y': y}, child=count)

    # Add total runs for the year
    y = margin_y + 7.5 * size
    count_group.add('text', {'x': x, 'y': y}, child=sum(day_of_week_count.values()))

    # Write count of runs by week
    y = 7.5 * size + margin_y
    for week_num, count in week_num_count.items():
        x = margin_x + (week_num + 0.5) * size
        count_group.add('text', {'x': x, 'y': y}, child=count)

    # Write count of runs by month
    for month in month_count:
        count = month_count.get(month)
        if count:
            text = f"{count} runs | {round(month_dist[month])} km"
            svg.groups[month].add('text', {'y': size * 0.7, 'class': 'count'}, child=text)

    # Distance key
    # Shortest, median and longest distances
    distanceTypes = _get_stats(distances)

    value_y = 11 * size + margin_y

    cx = margin_x
    for x, (name, d) in enumerate(distanceTypes):
        r = d / target_dist * size / 2
        dx = max(r, size / 2) + 5
        cx += dx
        cy = value_y - r - 16
        svg.circle(cx, cy, r, fill="rgb(140, 140, 140)")
        svg.add('text', {'x': cx, 'y': value_y}, child=round(d, 2))
        svg.add('text', {'x': cx, 'y': value_y + 16}, child=name)
        cx += dx

    svg.add('text', {'x': (margin_x + cx) / 2, 'y': value_y + 48, 'font-size': '24px'}, child="Distance (km)")

    # Pace key
    # Fastest, median and slowest distances
    paces = [d['pace'] for d in run_data]
    paceTypes = _get_stats(paces)
    
    min_seconds = round(paceTypes[0][1] * 60)
    med_seconds = round(paceTypes[1][1] * 60)
    max_seconds = round(paceTypes[2][1] * 60)

    cx = size * 10
    cy = 9.25 * size + margin_y
    max_width = size * 6
    med_drawn = False

    svg.add('text', {'x': cx, 'y': value_y}, child=_seconds_to_time(max_seconds))
    svg.add('text', {'x': cx, 'y': value_y + 16}, child='Max')

    for dx in range(max_width):
        p = dx / (max_width - 1)
        seconds = p * min_seconds + (1 - p) * max_seconds
        colour = _get_colour(seconds / 60)
        fill = f"rgb({colour[0]}, {colour[1]}, {colour[2]})"
        svg.rect(cx + dx, cy, 1.1, size, fill=fill)

        if not med_drawn and seconds <= med_seconds:
            med_drawn = True
            svg.add('text', {'x': cx + dx, 'y': value_y}, child=_seconds_to_time(med_seconds))
            svg.add('text', {'x': cx + dx, 'y': value_y + 16}, child='Med')

    svg.add('text', {'x': cx + max_width, 'y': value_y}, child=_seconds_to_time(min_seconds))
    svg.add('text', {'x': cx + max_width, 'y': value_y + 16}, child='Min')
    svg.add('text', {'x': cx + max_width / 2, 'y': value_y + 48, 'font-size': '24px'}, child="Pace (min / km)")


if __name__ == '__main__':
    year = 2024 if len(sys.argv) == 1 else int(sys.argv[1])
    size = 32
    filename = os.path.join('data', f"{year}.txt")
    run_data = read_data(filename)

    day_positions = get_day_positions(year)
    svg = draw_calendar(day_positions, size)
    add_runs(svg, run_data, year, size)

    svg.write(f"Running {year}")
