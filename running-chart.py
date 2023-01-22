import os
from collections import defaultdict
from calendar import month_abbr
from datetime import date, datetime
from draw_svg import SVG

colours = (
    (6, (0, 0, 0)),         # Black
    (5.5, (200, 0, 0)),     # Red
    (5, (250, 240, 0)),     # Yellow
    (4.75, (0, 200, 0)),    # Green
    (4.5, (0, 0, 200)),     # Blue
    (4, (0, 0, 50)),        # Dark blue
)

def _get_day_in_month(year, month):
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

def read_data(filename):
    run_data = []
    with open(filename, 'r') as f:
        for line in f:
            run_data.append(line.strip().split('\t'))
    return run_data


def get_day_positions(year):
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
    margin = size * 2
    width = (day_positions[-1]['x'] + 1) * size + margin * 2
    height = 7 * size + margin * 2
    viewbox = f"0 0 {width} {height}"

    svg = SVG({ 'viewBox': viewbox })
    svg.addStyle('.month-1', { 'fill': '#e2e2e2' })
    svg.addStyle('.month-2', { 'fill': '#ccc' })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle' })
    svg.addStyle('.axis-label', { 'font-size': '24px', 'dominant-baseline': 'middle' })

    label_group = svg.add('g', {'class': 'axis-label'})

    # Write days of the week as y-axis label
    for y, day in enumerate('MTWTFSS'):
        tx = margin - size / 2
        ty = (y + 0.5) * size + margin
        label_group.add('text', {'x': tx, 'y': ty}, child=day)

    # Collect months to find mean position
    months = defaultdict(list)

    # Draw a rect per day, coloured by month
    for day in day_positions:
        x = day['x'] * size + margin
        y = day['y'] * size + margin
        classname = f"month-{1 + day['month'] % 2}"
        svg.rect(x, y, size - 1, size - 1, classname=classname)

        if day['y'] == 0:
            months[day['month']].append(x)

    # Write month names as x-axis labels
    for month, x_values in months.items():
        mean_x = round(sum(x_values) / len(x_values)) + size / 2
        month_str = month_abbr[month]
        label_group.add('text', {'x': mean_x, 'y': margin - size / 2}, child=month_str)

    return svg


def add_runs(svg, run_data, year, size, target_dist=5):
    margin = size * 2
    svg.addStyle('circle', {'fill-opacity': 0.6, 'stroke': 'white'})

    count_group = svg.add('g', {'class': 'count'})
    svg.addStyle('.count', {'font-size': '16px', 'dominant-baseline': 'middle'})
    day_of_week_count = defaultdict(int)
    week_num_count = defaultdict(int)

    for day, month, run_time, distance in run_data:
        run_date = datetime.strptime(f"{day} {month} {year}", '%d %b %Y')
        position = run_date.isocalendar()
        week = position[1]
        day_of_week = position[2]

        run_time_seconds = sum(int(t) * 60 ** (2 - i) for i, t in enumerate(run_time.split(':')))
        pace = run_time_seconds / float(distance) / 60
        colour = _get_colour(pace)

        fill = f"rgb({colour[0]}, {colour[1]}, {colour[2]})"

        x = (week + 0.5) * size + margin
        y = (day_of_week - 0.5) * size + margin
        r = float(distance) / target_dist * size / 2
        svg.circle(x, y, r, fill=fill)

        day_of_week_count[day_of_week] += 1
        week_num_count[week] += 1

    # Write count of run by day of week
    x = 53.5 * size + margin
    for day, count in day_of_week_count.items():
        y = margin + (day - 0.5) * size
        count_group.add('text', {'x': x, 'y': y}, child=count)

    y = 7.5 * size + margin
    for week_num, count in week_num_count.items():
        x = margin + (week_num + 0.5) * size
        count_group.add('text', {'x': x, 'y': y}, child=count)


if __name__ == '__main__':
    year = 2022
    size = 40
    filename = os.path.join('data', f"{year}.txt")
    run_data = read_data(filename)

    day_positions = get_day_positions(year)
    svg = draw_calendar(day_positions, size)
    add_runs(svg, run_data, year, size)

    svg.write(f"Running {year}")
