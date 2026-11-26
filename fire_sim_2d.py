# Name: Modelling a Forest Fire using Cellular Automata
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
# ---

from capyle.ca import Grid2D, Neighbourhood, randomise2d
import capyle.utils as utils
import numpy as np
import math

WATER, CHAPARRAL, GRASS, FOREST, CANYON, TOWN, BURNING, BURNT = range(8)
CANYON_WIDTH = 10
START_ROW = 0
START_COL = 0
BURN_RATE = 0.1 # Explore variable burn rates based on terrain types
P0 = 0.58 # Alexandridis et al. (2008) base spread probability


def setup(args):
    """Set up the config object used to interact with the GUI"""
    config_path = args[0]
    config = utils.load(config_path)
    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --
    config.title = "Modelling a Forest Fire using Cellular Automata"
    config.dimensions = 2

    config.states = (WATER, CHAPARRAL, GRASS, FOREST, CANYON, TOWN, BURNING, BURNT)
    map = gen_map()
    fire_start = map.copy()
    fire_start[START_ROW, START_COL] = BURNING
    config.initial_grid = fire_start

    config.wrap = False
    # -------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----

    # config.state_colors = [(0,0,0),(1,1,1)]
    # config.grid_dims = (200,200)

    config.grid_dims = map.shape
    config.state_colors = [
        (0/255, 0/255, 255/255), # Water
        (101/255, 85/255, 33/255), # Chaparral
        (124/255, 252/255, 0/255), # Grass
        (34/255, 139/255, 34/255), # Forest
        (160/255, 110/255, 60/255), # Canyon wall
        (0/255, 0/255, 0/255), # Town
        (255/255, 0/255, 0/255), # Burning
        (50/255, 50/255, 50/255), # Burnt
    ]

    # ----------------------------------------------------------------------

    # the GUI calls this to pass the user defined config
    # into the main system with an extra argument
    # do not change
    if len(args) == 2:
        config.save()
        sys.exit()
    return config

def gen_map():
    map = np.full((500, 500), CHAPARRAL)
    map[50:75, 0:250] = FOREST
    map[75:300, 50:125] = FOREST
    map[300:350, 50:250] = FOREST
    map[100:150, 325:450] = FOREST
    map[125:225, 175:225] = WATER
    map[275:400, 375:400] = WATER

    map[225 - CANYON_WIDTH:250 + CANYON_WIDTH, 250 - CANYON_WIDTH:450 + CANYON_WIDTH] = CANYON
    map[225:250, 250:450] = GRASS
    map[437:462, 187:212] = TOWN
    return map

def decamara_function(ignition_prob, slope_angle, c1=0.045, c2=0.131, a=0.078, wind_speed=3, wind_angle=0):
    """Alexandridis et al. (2008) spread probability, as used by Freire & DaCamara (2019):
    p_burn = p0 * (1 + p_veg) * (1 + p_den) * p_wind * p_slope
    ignition_prob is the precomputed p0 * (1 + p_veg) * (1 + p_den) for each cell (see main).
    Fuel is NOT used here: it controls how long a cell burns, not how easily it ignites."""
    wind = math.exp(wind_speed * (c1 + c2 * (math.cos(wind_angle) - 1)))
    slope = np.exp(a * slope_angle)
    p = ignition_prob * wind * slope
    return np.clip(p, 0.0, 1.0)

def calculate_wind_angle(wind_direction, spread_direction):
    diff = wind_direction - spread_direction
    return math.radians(diff)

def transition_function(grid, neighbourstates, neighbourcounts, ignition_prob, fuel, slope_angle):
    burning_neighbours = neighbourcounts[BURNING]
    flammable = (grid > WATER) & (grid < TOWN)
    ignite =  flammable & (burning_neighbours > 0) & (np.random.rand(*grid.shape) < decamara_function(ignition_prob, slope_angle))

    fuel[grid == BURNING] -= BURN_RATE
    burnt_out = (grid == BURNING) & (fuel <= 0)

    grid[ignite] = BURNING
    grid[burnt_out] = BURNT
    return grid

def main():
    """ Main function that sets up, runs and saves CA"""
    # Get the config object from set up
    config = setup(sys.argv[1:])
    map = gen_map()

    # Alexandridis et al. (2008) vegetation factors (literature range -0.4..+0.4).
    # p_veg = vegetation type, p_den = vegetation density. -1 makes p = 0 (non-flammable).
    # Forest p_veg extended to -0.6 so dense forest "doesn't ignite very easily" (brief).
    # Resulting p (no slope, wind factor 1.14): grass 0.93 > chaparral 0.66 > forest 0.34
    #                   water chaparral grass forest canyon town
    P_VEG    = np.array([-1.0, 0.0,      0.4,  -0.6,  0.0,   -1.0])
    P_DEN    = np.array([0.0,  0.0,      0.0,  0.3,   -0.4,  0.0])
    FUEL     = np.array([0.0,  0.6,      0.15, 1.0,   0.6,   0.0])
    SLOPE    = np.array([0.0,  0.0,      0.0,  0.0,   70.0,  0.0])

    # Base ignition probability per terrain (before wind and slope):
    # water 0, chaparral 0.58, grass 0.812, forest 0.302, canyon 0.348, town 0
    IGNITION = P0 * (1 + P_VEG) * (1 + P_DEN)

    ignition_prob = IGNITION[map].astype(float)
    fuel = FUEL[map].astype(float)
    slope_angle = SLOPE[map].astype(float)

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, (transition_function, ignition_prob, fuel, slope_angle))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
