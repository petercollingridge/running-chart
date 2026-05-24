from draw_svg import SVG
from utils import get_all_runs, get_pace_colour


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def days_between(run1, run2):
    """ Return the number of days between two runs. """
    day1 = int(run1['day'])
    day2 = int(run2['day'])
    month1 = MONTHS.index(run1['month']) + 1
    month2 = MONTHS.index(run2['month']) + 1

    if month1 == month2:
        return day2 - day1

    # Handle month change
    if month2 > month1:
        for month in range(month1, month2):
            day2 += DAYS_IN_MONTH[month - 1]
        return day2 - day1

    # Handle year change
    # if (month1 == 12 and month2 == 1) or (month2 == 12 and month1 == 1):
    #     days_in_months = sum(DAYS_IN_MONTH)
    #     return day2 + days_in_months - day1

    return float('inf')


def is_consecutive(date1, date2):
    """ Return True if date2 is within two days of date1. """
    day1, month1 = int(date1[0]), MONTHS.index(date1[1]) + 1
    day2, month2 = int(date2[0]), MONTHS.index(date2[1]) + 1

    if month1 == month2:
        return day2 - day1 <= 2

    # Handle month change
    if month2 == month1 + 1 or (month1 == 12 and month2 == 1):
        days_in_month1 = DAYS_IN_MONTH[month1 - 1]
        return day2 + days_in_month1 - day1 <= 2

    return False


def split_into_consecutive_runs(runs):
    """
    Return a list of lists of consecutive runs,
    where a run is considered consecutive it is within two days of a previous run.
    """

    consecutive_runs = []
    current_run = []
    current_date = (runs[0]['day'], runs[0]['month'])

    for run in runs:
        run_date = (run['day'], run['month'])
        if is_consecutive(current_date, run_date):
            current_run.append(run)
        else:
            consecutive_runs.append(current_run)
            current_run = [run]

        current_date = run_date

    if current_run:
        consecutive_runs.append(current_run)

    return consecutive_runs


def draw_run_streak(svg, runs, x1, y1, dx, scale_distance):
    """ Draw a single run streak as a row of circles. """

    label = f"{runs[0]['day']} {runs[0]['month']} - {runs[-1]['day']} {runs[-1]['month']}"
    svg.add('text', {'x': x1 / 2, 'y': y1 - 10, 'class': 'axis-label'}, label)
    svg.add('text', {'x': x1 / 2, 'y': y1 + 10, 'class': 'axis-label'}, runs[0]['year'])

    streak_days = days_between(runs[0], runs[-1])
    x2 = x1 + streak_days * dx
    svg.add('line', {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y1, 'class': 'axis'})
    svg.add('text', {'x': x2 + scale_distance * runs[-1]['distance'] + 15, 'y': y1, 'class': 'axis-label'}, len(runs))

    current_day = int(runs[0]['day'])
    current_month_index = MONTHS.index(runs[0]['month'])
    current_run_index = 0

    for i in range(streak_days + 1):
        x = x1 + i * dx
        run = runs[current_run_index]

        if int(run['day']) == current_day and run['month'] == MONTHS[current_month_index]:
            radius = run['distance'] * scale_distance
            colour = get_pace_colour(run['pace'])
            svg.add('circle', { 'cx': x, 'cy': y1, 'r': radius, 'fill': colour })
            current_run_index += 1
        else:
            svg.add('line', {'x1': x, 'y1': y1 - 3, 'x2': x, 'y2': y1 + 3, 'class': 'axis'})

        # Get the next date
        current_day += 1
        if current_day > DAYS_IN_MONTH[current_month_index]:
            current_day = 1
            current_month_index += 1


def draw_consecutive_runs(runs, filename='consecutive_runs.svg'):
    max_length = len(runs[0])
    max_distance = max(max(run['distance'] for run in runs) for runs in runs)
    scale_distance = 2
    max_r = max_distance * scale_distance / 2
    dx = scale_distance * 16
    dy = max_r * scale_distance + 50
    x1 = 160
    y1 = max_r + 20

    svg_width = max_length * dx * 2 + x1
    svg_height = 40 + dy * (len(runs) - 1) + max_r * 2
    svg = SVG({ 'viewBox': f"0 0 {svg_width} {svg_height}" })
    svg.addStyle('text', { 'font-family': 'Arial', 'text-anchor': 'middle', 'alignment-baseline': 'middle' })
    svg.addStyle('circle', {'fill-opacity': 0.7, 'stroke': 'white'})
    svg.addStyle('.axis', { 'stroke-width': '1px', 'stroke': '#888' })

    svg.rect(0, 0, svg_width, svg_height, fill=  '#f9f9f9')

    for index, run_streak in enumerate(runs):
        y = y1 + index * dy 
        draw_run_streak(svg, run_streak, x1, y, dx, scale_distance)

    svg.write(filename)


if __name__ == '__main__':
    all_runs = get_all_runs()
    consequtive_runs = split_into_consecutive_runs(all_runs)
    consequtive_runs.sort(key=len, reverse=True)

    draw_consecutive_runs(consequtive_runs[:10])
