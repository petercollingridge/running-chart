import os
from running_chart import draw_chart as draw_running_chart
from stacked_run_chart import draw_stacked_runs
from run_scatter_plot import draw_run_scatter_plots
from runs_by_month import draw_runs_by_month, draw_year_line
from runs_over_the_year import draw_chart as draw_runs_over_year
from runs_by_distance import draw_runs_by_distance
from utils import get_runs_by_year

if __name__ == '__main__':
    runs_by_year = get_runs_by_year()
    year = 2026

    draw_running_chart(runs_by_year, year, os.path.join("images", f"Running {year}.svg"))
    draw_stacked_runs(runs_by_year, os.path.join("images", "Stacked run chart.svg"))
    draw_runs_over_year(runs_by_year, os.path.join("images", "Runs by year.svg"))
    draw_runs_by_month(runs_by_year, os.path.join("images", "Runs by month line chart.svg"), draw_year_line)
    draw_runs_by_distance(runs_by_year, os.path.join("images", "Runs by distance.svg"))
    draw_run_scatter_plots(runs_by_year, os.path.join("images", "Run scatter plots.svg"))
