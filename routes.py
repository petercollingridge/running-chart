import json
import os

from draw_svg import SVG
from utils import get_gpx_data, get_runs_by_year, get_coords_and_time, MONTHS

villages = {
    "Leafield": (51.8375, -1.54),
    "Ramsden": (51.8362, -1.486),
    "Finstock": (51.8405, -1.483),
    "Crawley": (51.8105, -1.515),
    "Hailey": (51.8095, -1.4918),
    "Minster Lovell": (51.799, -1.5465),
    "Shipton-under-Wychwood": (51.8585, -1.594),
    "Ascot-under-Wychwood": (51.867, -1.563),
    "New Yatt": (51.813, -1.465),
    "Swinbrook": (51.804, -1.595),
}


def extract_to_json(data, output_filename="summary.json", folder="data"):
    """Extract run data from gpx files and save it as json."""

    min_x, max_x, min_y, max_y = get_extent_for_runs(data)
    scale = 800 / (max_x - min_x)

    # Convert list of list to list of dicts
    output_data = {}
    for filename, run_data in data.items():
        date = filename.removesuffix('.gpx')
        output_data[date] = [[round((d[0] - min_x) * scale, 1), round((max_y - d[1]) * scale, 1), d[2]] for d in run_data]

    with open(os.path.join(folder, output_filename), "w") as f:
        f.write("{\n")
        for run in sorted(output_data.keys()):
            f.write(f'  "{run}": {json.dumps(output_data[run])}')
            if run != sorted(output_data.keys())[-1]:
                f.write(",\n")
        f.write("\n}\n")


def write_village_names(svg, scale_x, scale_y):
    """Write village names to the svg."""
    for village, (lat, lon) in villages.items():
        x = scale_x(lon)
        y = scale_y(lat)
        svg.add('text', {'x': x, 'y': y, 'class': 'village-name'}, village)


def plot_route(runs, filename='route.svg'):
    """Plot the route using matplotlib."""
    width = 800
    margin = 10

    min_lon, max_lon , min_lat, max_lat= get_extent_for_runs(runs)
    print(min_lat, max_lat, min_lon, max_lon)
    scale = (width - margin * 2) / (max_lon - min_lon)

    def scale_x(lon):
        return round((lon - min_lon) * scale + margin, 2)

    def scale_y(lat):
        return round((max_lat - lat) * scale + margin, 2)

    height = scale * (max_lat - min_lat) + margin * 2
    svg = SVG({ 'width': '100%', 'viewBox': f"0 0 {width} {height}" })
    svg.addStyle('.route', { 'fill': 'none', 'stroke': '#2d7d7a', 'stroke-width': 2, 'opacity': 0.1 })
    svg.addStyle('.village-name', { 'fill': '#112', 'font-size': '10px', 'text-anchor': 'start', 'dominant-baseline': 'baseline' })
    svg.addStyle('.distance-circle', { 'fill': 'none', 'stroke': '#e8e8f0', 'stroke-width': 0.5, 'stroke-dasharray': '4 2' })

    svg.add('rect', { 'x': 0, 'y': 0, 'width': width, 'height': height, 'fill': '#f0f0f0' })

    start_x = scale_x(-1.5393660)
    start_y = scale_y(51.8343140)
    radius_1k = scale_x(-1.5393660) - scale_x(-1.5539033)
    # svg.add('circle', { 'cx': start_x, 'cy': start_y, 'r': radius_1k, 'class': 'distance-circle' })
    # svg.add('circle', { 'cx': start_x, 'cy': start_y, 'r': radius_1k * 2, 'class': 'distance-circle' })
    # svg.add('circle', { 'cx': start_x, 'cy': start_y, 'r': radius_1k * 3, 'class': 'distance-circle' })
    # svg.add('circle', { 'cx': start_x, 'cy': start_y, 'r': radius_1k * 4, 'class': 'distance-circle' })
    # svg.add('circle', { 'cx': start_x, 'cy': start_y, 'r': radius_1k * 5, 'class': 'distance-circle' })

    for run in runs.values():
        points = " ".join(f"{scale_x(d[0])},{scale_y(d[1])}" for d in run)
        svg.add('polyline', { 'points': points, 'class': 'route' })

    write_village_names(svg, scale_x, scale_y)

    filename = os.path.join("images", filename)
    svg.write(filename)


def categorise_runs(gpx_folder):
    """Categorise runs based on their duration."""
    
    run_summaries = get_runs_by_year()
    gpx_data = get_data_for_runs(gpx_folder, get_coords_and_time)
    
    def is_5k_run(run, gpx_for_run):
        """Return True if the run is my standard 5k run."""
        # if run['distance'] <= 6:
        #     print(max(d[0] for d in gpx_for_run))
        return run['distance'] <= 6 and max(d[0] for d in gpx_for_run) < -1.527

    filtered_runs = {}
    for filename in gpx_data.keys():
        date = filename.removesuffix('.gpx')
        gpx_for_run = gpx_data[filename]
        year, month, day = date.split('-')

        if year in run_summaries:
            run_summary = run_summaries[year]
            month = MONTHS[int(month) - 1]
            day = day.lstrip('0')  # Remove leading zero from day
            run = next((r for r in run_summary if r['day'] == day and r['month'] == month), None)

            if run:
                if is_5k_run(run, gpx_for_run):
                    filtered_runs[filename] = gpx_for_run
            else:
                print(f"Warning: No run data found for {day} {month} {year}.")
        else:
            print(f"Warning: No run data found for year {year}.")

    return filtered_runs


def main(folder):
    runs = get_gpx_data(folder, get_coords_and_time)
    plot_route(runs)
    # extract_to_json(data)

    # filtered_runs = categorise_runs(folder)
    # print(f"Found {len(filtered_runs)} runs that match the criteria.")
    # plot_route(filtered_runs, filename='5k_routes.svg')
    # extract_to_json(filtered_runs, output_filename="5k_routes.json")



if __name__ == "__main__":
    folder = os.path.join(os.path.dirname(__file__), "gpx")
    main(folder)
