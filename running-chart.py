from datetime import date
from draw_svg import SVG


def _get_day_in_month(year, month):
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def get_day_positions(year):
    row = 0
    month = 1
    weekday = date(year, 1, 1).weekday()
    days_in_month = _get_day_in_month(year, month)

    day_positions = []
    while month <= 12:
        day_positions.append({
            'x': weekday,
            'y': row,
            'month': month
        })

        # Move to the next day of the week
        weekday += 1
        if weekday > 6:
            weekday = 0
            row += 1

        # Count down to see if we reach the end of the month
        days_in_month -= 1
        if days_in_month == 0:
            month += 1
            if month > 12:
                break
            days_in_month = _get_day_in_month(year, month)

    return day_positions


def draw_calendar(day_positions, size):
    margin = size
    width = 7 * size + margin * 2
    height = day_positions[-1]['y'] * size + margin * 2
    
    svg = SVG({ 'viewBox': f"0 0 {width} {height}" })

    for day in day_positions:
        x = day['x'] * size + margin
        y = day['y'] * size + margin
        svg.rect(x, y, size - 1, size - 1)

    return svg


if __name__ == '__main__':
    year = 2022
    size = 20

    day_positions = get_day_positions(year)
    svg = draw_calendar(day_positions, size)

    svg.write(f"Running {year}")
