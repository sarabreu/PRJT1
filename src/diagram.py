import pandas as pd
import matplotlib.pyplot as plt
from data import Timeline, save_gantt
import plotly.figure_factory as ff
import colorsys
from typing import Optional

def generate_hex_colors(n: int) -> list:
    """
    Generate a list of n distinct and distinguishable hex colors.
    """
    # Initialize the list of colors
    colors = []
    
    # Generate n colors using the colorsys library
    for i in range(n):
        hue = (i / n) % 1
        saturation = 1.0
        value = 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        color = f"#{r:02x}{g:02x}{b:02x}"
        colors.append(color)
    
    return colors


def display_gantt(schedule, instance: Optional[int]):
    unique_resources: list = schedule["Resource"].unique().tolist()

    unique_colors = generate_hex_colors(len(unique_resources))

    colors = {}
    for resource,color in zip(unique_resources, unique_colors):
        colors[resource] = color

    colors["Setup"] = "#FFFFFF"

    fig = ff.create_gantt(schedule, colors=colors, index_col='Resource', show_colorbar=True,
                        group_tasks=True, title=f'Gantt Chart {instance}')

    if instance is not None:
        save_gantt(fig, f"gantt_{instance}.html")

    fig.show()