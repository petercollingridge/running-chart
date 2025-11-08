import os
from math import floor

# colours = (
#     (6.25, (0, 0, 0)),      # Black
#     (5.75, (200, 0, 0)),    # Red
#     (5, (250, 240, 0)),     # Yellow
#     (4.75, (0, 200, 0)),    # Green
#     (4.5, (0, 0, 160)),     # Dark blue
#     (4, (160, 160, 255)),   # Light blue
# )

colours = (
    (6.25, (0, 0, 0)),      # Black
    (5.75, (200, 0, 0)),    # Red
    (5, (250, 240, 0)),     # Yellow
    (4.75, (0, 200, 0)),    # Green
    (4.5, (60, 120, 255)),   # Light blue
    (4, (0, 0, 120)),     # Dark blue
)


def get_pace_colour(x):
    for i, colour in enumerate(colours):
        if x > colour[0]:
            # Propotion of the way through this band
            t1, c1 = colour
            t2, c2 = colours[i - 1]
            p = (x - t1) / (t2 - t1)
            colour = [round(c2[n] * p + c1[n] * (1 - p)) for n in range(3)]
            return f"rgb({colour[0]}, {colour[1]}, {colour[2]})"


def read_data(filename):
    run_data = []
    with open(filename, 'r') as f:
        for line in f:
            if line[0] == '#':
                continue

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


def seconds_to_time(s):
    minutes = floor(s / 60)
    seconds = floor(s) % 60
    return f"{minutes}:{seconds:02d}"


def get_colours_for_year(years):
    """ Return a dict mapping year to colour. """
    colours = {}
    blue_step = 255 // len(years)
    green_step = 200 // (len(years) - 1)

    for i, year in enumerate(years):
        blue = 255 - i * blue_step
        green = 200 - i * green_step
        colours[year] = f'rgb(0, {green}, {blue})'

    return colours


def get_runs_by_year(folder = 'data'):
    """ Return a dict mapping year (str) to list run dicts. """
    runs_by_year = {}
    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            year = filename[:-4]
            filepath = os.path.join(folder, filename)
            runs_by_year[year] = read_data(filepath)
    return runs_by_year
