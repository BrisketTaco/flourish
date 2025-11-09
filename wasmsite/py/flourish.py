# Import required modules
import js
import numpy as np
from js import document, requestAnimationFrame
from pyodide.ffi import create_proxy
import random
#import numpy as np
from harmonograph import Harmonograph
from spirograph import Spirograph, Gear
from render import ElegantLine, ColorLine
import pythonrender
import math


# main.py
def get_points(style, dt, spirogears, main_circle_radius, random_seed, num_pendulums=2):
    """Original code used numpy's RNG. This had hiccups in Pyodide: it was an easy switch to `random`, but not sure if important
    or useful to reconsider.  """

    if random_seed == 0 or random_seed is None or math.isnan(random_seed):
        # Since we can't get random_seed back out, let's generate one and print it to console
        print("Since we can't retrieve the default seed, let's generate a seed so we can print it")
        
        random_seed = random.random()
        document.getElementById('randomSeed').value = random_seed

    print(f"{random_seed=}")
    random.seed(random_seed)

    print("get_points: Started")
    if style == "spirograph" or style is False:
        print("Drawing Spirograph")
        print(f"{type(main_circle_radius)}")
        if main_circle_radius is None or math.isnan(main_circle_radius):
            main_circle_radius = random.random()

        has_gears = spirogears is not None and hasattr(spirogears, '__len__')
        if not has_gears or len(spirogears) == 0:
            print("Generating random Spirograph")
            curve = Spirograph.make_random(random)
            # some seeds are slow bc they generate many cycles/points
            # this caps it so browser doesn't hang
            natural_cycles = curve._cycles()
            curve.max_cycles = min(natural_cycles, 150)
            print(f"{main_circle_radius=}")
            print(f"Generated gears: {curve.gears[0].teeth}, {curve.gears[1].teeth}")
            print(f"Cycles: {natural_cycles} capped to {curve.max_cycles}")
        else:
            curve = Spirograph()
            curve.outer_teeth = 144

            gears_to_use = spirogears[:2] if len(spirogears) >= 2 else spirogears

            for i in range(2):
                if i < len(gears_to_use):
                    g = gears_to_use[i]
                    if i == 0:
                        parent_teeth = curve.outer_teeth
                    else:
                        parent_teeth = curve.gears[i-1].teeth

                    teeth = int(g.gearRadius * parent_teeth)
                    teeth = max(5, min(teeth, parent_teeth - 1))  # Ensure valid range

                    inside = 1 if g.inside else 0  # Convert boolean to int
                    curve.gears.append(Gear(name=f"g{chr(97+i)}", teeth=teeth, inside=inside))
                else:
                    # Add a random gear to reach 2 gears
                    if i == 0:
                        parent_teeth = curve.outer_teeth
                    else:
                        parent_teeth = curve.gears[i-1].teeth

                    gear_ratio = random.random() * random.random()
                    teeth = int(gear_ratio * parent_teeth)
                    teeth = max(5, min(teeth, parent_teeth - 1))
                    inside = random.choice([0, 1])
                    curve.gears.append(Gear(name=f"g{chr(97+i)}", teeth=teeth, inside=inside))

            if spirogears:
                curve.pen_extra = spirogears[-1].penRadius * 10  # Scale back up from /10
            else:
                curve.pen_extra = random.random() * 0.5
            curve.last_speed = 1
            curve.last_speed_denom = 1

            natural_cycles = curve._cycles()
            curve.max_cycles = min(natural_cycles, 100)
            print(f"Cycles: {natural_cycles} capped to {curve.max_cycles}")
    elif style == "random1":
        # Not used, experimenting with different parameters
        curve = Harmonograph.make_random(random, npend=num_pendulums, syms=['R', 'X', 'Y', 'N'])
    else:
        curve = Harmonograph.make_random(random, npend=num_pendulums, syms=['X', 'Y', 'R'])
        
    xs = []
    ys = []

    # TODO: Change points() so it returns the points, rather than going from a List to a Generator and back to a List
    scale = main_circle_radius if style == "spirograph" or style is False else 1.0
    for x,y in curve.points(["x", "y"], scale, dt):
        xs.append(x)
        ys.append(y)
    print("get_points: Done")
    return xs, ys

def generate(style = "harmonograph", canvas_element = "harmonographCanvas", scale_ratio = 1, dt = .002, spirogears = None, main_circle_radius = None, random_seed = None, num_pendulums = 2):
    print("Generating: Started")
    print(f"{style=}")
    xs, ys = get_points(style=style, dt=dt, spirogears=spirogears, main_circle_radius=main_circle_radius, random_seed = random_seed, num_pendulums=num_pendulums)

    if spirogears is not None:
        print(spirogears)
        
    print("Generating: Done")
    if canvas_element is None or not canvas_element:
        # Pass the objects back to Javascript
        # In JS, these will be .toJS'd to js elements
        # instead of proxies... this could also be done here:

        # Normalize first
        stacked_vals = np.vstack((xs, ys))

        min_val = np.min(stacked_vals)
        max_val = np.max(stacked_vals)

        # Giving a little margin
        desired_min = 0.025
        desired_max = 0.975

        xs = desired_min + (desired_max - desired_min) * (xs - min_val) / (max_val - min_val)
        ys = desired_min + (desired_max - desired_min) * (ys - min_val) / (max_val - min_val)
        
        return xs, ys
    else:
        # If we have a canvas_element, we can draw the points directly here
        pythonrender.draw_points(xs, ys, scale_ratio, canvas_element)
        return None, None
    
