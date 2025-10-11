colours = (
    (6.25, (0, 0, 0)),      # Black
    (5.75, (200, 0, 0)),    # Red
    (5, (250, 240, 0)),     # Yellow
    (4.75, (0, 200, 0)),    # Green
    (4.5, (0, 0, 160)),     # Dark blue
    (4, (160, 160, 255)),   # Light blue
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
