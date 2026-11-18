# Name: Team 24 Fire Model (terrain)
# Dimensions: 2

# --- Set up executable path, do not edit ---
import sys
import inspect
this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('ca_descriptions')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')
sys.path.append(main_dir_loc + 'ca_descriptions')
# ---

from capyle.ca import Grid2D, Neighbourhood, CAConfig, randomise2d
import capyle.utils as utils
import numpy as np
import random
from terrains import Chaparral, BodyOfWater, Grassland, DenseForest

# ---- State codes -----------------------------------------------------------
CHAPARRAL, WATER, GRASS, FOREST, BURNING, BURNT = range(6)

TERRAIN = {
    CHAPARRAL: Chaparral(0, 0),
    WATER:     BodyOfWater(0, 0),
    GRASS:     Grassland(0, 0),
    FOREST:    DenseForest(0, 0),
}

GRID_DIMS = (400, 400)
IGNITION_POINT = (5, 5)
BURN_RATE = 0.1
RECOVERY_RATE = 0.01
REGROWTH_PROBABILITY = 0.001
PROBABILITY_CONSTANT = 0.5


def build_terrain_map(dims):
    """Return a 2D array of terrain codes. Draw the map here.

    Must be deterministic: setup() runs once in the GUI process and again
    in main(), and both must produce the same map.
    """
    rows, cols = dims
    t = np.full(dims, CHAPARRAL, dtype=int)
    # Placeholder layout
    t[int(rows * 0.10):int(rows * 0.15), int(cols * 0):int(cols * 0.5)] = FOREST
    t[int(rows * 0.15):int(rows * 0.60), int(cols * 0.1):int(cols * 0.25)] = FOREST
    t[int(rows * 0.60):int(rows * 0.70), int(cols * 0.1):int(cols * 0.5)] = FOREST
    t[int(rows * 0.20):int(rows * 0.30), int(cols * 0.65):int(cols * 0.90)] = FOREST
    t[int(rows * 0.25):int(rows * 0.45), int(cols * 0.35):int(cols * 0.45)] = WATER
    t[int(rows * 0.45):int(rows * 0.50), int(cols * 0.50):int(cols * 0.90)] = GRASS
    t[int(rows * 0.55):int(rows * 0.80), int(cols * 0.75):int(cols * 0.80)] = WATER
    return t


def build_property_layers(terrain):
    """Build the 'under' grids from the terrain map:
    per-cell ignition probability and per-cell fuel."""
    ignition = np.zeros(terrain.shape)
    fuel = np.zeros(terrain.shape)
    for code, t in TERRAIN.items():
        mask = terrain == code
        ignition[mask] = t.ignition_probability
        fuel[mask] = t.fuel_resource
    return ignition, fuel


def transition_func(grid, neighbourstates, neighbourcounts, ignition, fuel):
    burning_neighbours = neighbourcounts[BURNING]
    unburnt = grid < BURNING
    burning = grid == BURNING
    burnt = grid == BURNT

    p = PROBABILITY_CONSTANT * (1 - (1 - ignition) ** burning_neighbours)
    birth = unburnt & (np.random.random(grid.shape) < p)

    fuel[burning] -= BURN_RATE
    death = burning & (fuel <= 0)

    grid[birth] = BURNING
    grid[death] = BURNT
    fuel[burnt] += RECOVERY_RATE * 0.6 * np.random.random(np.count_nonzero(burnt))
    reborn = burnt & (fuel >= 0.6) & (burning_neighbours == 0) & (np.random.random(grid.shape) < REGROWTH_PROBABILITY)
    grid[reborn] = CHAPARRAL
    return grid


def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    # ---THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED---
    config.title = "Team 24 Fire Model (terrain)"
    config.dimensions = 2
    config.states = (CHAPARRAL, WATER, GRASS, FOREST, BURNING, BURNT)
    # ------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----

    # terrains.py colours are 0-255; CAPyLE expects 0-1
    config.state_colors = [tuple(c / 255 for c in TERRAIN[k].color)
                           for k in (CHAPARRAL, WATER, GRASS, FOREST)] \
        + [(1, 0, 0), (0, 0, 0)]  # burning = red, burnt = black
    config.grid_dims = GRID_DIMS
    config.wrap = False  # fire shouldn't wrap around the edges

    # Initial grid is the terrain map plus the ignition point.
    # Note: this overrides anything drawn in the GUI's initial grid editor.
    initial = build_terrain_map(config.grid_dims)
    initial[IGNITION_POINT] = BURNING
    config.initial_grid = initial

    # ----------------------------------------------------------------------

    if len(args) == 2:
        config.save()
        sys.exit()

    return config


def main():
    # Open the config object
    config = setup(sys.argv[1:])

    # Build the terrain property layers that sit "under" the state grid
    terrain = build_terrain_map(config.grid_dims)
    ignition, fuel = build_property_layers(terrain)

    # Pass the layers as extra args: CAPyLE calls
    # transition_func(grid, ns, nc, ignition, fuel) each step
    grid = Grid2D(config, (transition_func, ignition, fuel))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)


if __name__ == "__main__":
    main()
