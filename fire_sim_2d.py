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
BURN_RATE = 0.01 # Explore variable burn rates based on terrain types

N, NE, E, SE, S, SW, W, NW = 0, 45, 90, 135, 180, 225, 270, 315
WIND_DIRECTION = SE
WIND_SPEED = 3

# Diagonal neighbours are further away (sqrt(2) cells), so they are less likely to ignite
DIAGONAL_FACTOR = 1 / math.sqrt(2)

SPREAD_DIRECTIONS = [SE, S, SW, E, W, NE, N, NW]
DIAGONAL = [True, False, True, False, False, True, False, True]

P0 = 0.58 # Alexandridis et al. (2008) base spread probability

# Alexandridis et al. (2008) vegetation factors (literature range -0.4..+0.4).
# p_veg = vegetation type, p_den = vegetation density. -1 makes p = 0 (non-flammable).
# Forest p_veg extended to -0.6 so dense forest "doesn't ignite very easily" (brief).
# Canyon uses chaparral values: its steepness is handled by the elevation/slope map below.
#                   water chaparral grass forest canyon town
P_VEG    = np.array([-1.0, 0.0,      0.4,  -0.6,  0.0,   -1.0])
P_DEN    = np.array([0.0,  0.0,      0.0,  0.3,   0.0,   0.0])

# Base ignition probability per terrain (before wind, slope and diagonal factor):
# water 0, chaparral 0.58, grass 0.812, forest 0.302, canyon 0.58, town 0
IGNITION = P0 * (1 + P_VEG) * (1 + P_DEN)

# Fuel only controls how long a cell burns (FUEL / BURN_RATE steps), NOT how easily it ignites
FUEL     = np.array([0.0,  0.3,      0.1,   1.5,    0.3,   0.0])

CANYON_DEPTH = 5

# Row -1 is up (north), column -1 is left (west).
# NW N NE
# W [X] E
# SW S SE
OFFSETS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]

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

    fire_start[START_ROW:START_ROW + 3, START_COL:START_COL + 3] = BURNING
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
        (124/255, 252/255, 0/255), # Canyon wall
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

def gen_elevation_map(shape):
    """Return the height of every cell.

    The land is flat at height 0 everywhere except the canyon, which is a sunken valley (CANYON_DEPTH):
      - the canyon floor sits at -CANYON_DEPTH
      - the canyon walls slope evenly from -CANYON_DEPTH at the floor's edge back up to 0 at the outer edge
    """
    # Row and column index of every cell, as two 2D arrays
    rows, cols = np.indices(shape)

    # Calculates the greatest distance from the floor of canyon for each cell
    # dr is vertical distance, and dc is horizontal distance
    dr = np.maximum.reduce([225 - rows, np.zeros(shape), rows - 249])
    dc = np.maximum.reduce([250 - cols, np.zeros(shape), cols - 449])

    # Largest distance to the floor of the canyon
    d = np.maximum(dr, dc)

    # Clips heights between 0 (on floor) and 1 (top of wall)
    # Calcs how far up the canyon wall (CANYON_WIDTH) the cell is and multiplies by depth
    # Halfway up the wall would be 0.5*-4 = -2 height
    return -CANYON_DEPTH * np.clip(1 - d / CANYON_WIDTH, 0, 1)

def gen_slope_angles(elevation):
    """Return 8 arrays (one per neighbour, in capyle's order) of slope angles in degrees.

    Positive = this cell is higher than the neighbour, so fire spreads UPHILL (faster).
    Negative = this cell is lower, so fire spreads DOWNHILL (slower).
    Zero     = flat ground, so slope has no effect.
    """
    # Add 1 cell padding so edge cells have neighbours to compare with
    padded = np.pad(elevation, 1, mode='edge')
    h, w = elevation.shape
    angles = []

    for dr, dc in OFFSETS:
        # Shift padded map so we get the value of the current OFFSET direction
        # (E.g. N, S, E, W)
        neighb_elev = padded[1+dr:1+dr+h, 1+dc:1+dc+w]

        # If diagonal adjust distance using Pythag, side neighbours are 1
        dist = math.sqrt(2) if dr and dc else 1.0

        # Convert height difference into an angle
        angles.append(np.degrees(np.arctan((elevation - neighb_elev) / dist)))
    return angles

def decamara_function(ignition_prob, slope_angle, c1=0.045, c2=0.131, a=0.078, wind_speed=WIND_SPEED, wind_angle=0):
    """Alexandridis et al. (2008) spread probability, as used by Freire & DaCamara (2019):
    p_burn = p0 * (1 + p_veg) * (1 + p_den) * p_wind * p_slope
    ignition_prob is the precomputed p0 * (1 + p_veg) * (1 + p_den) for each cell (see IGNITION).
    Fuel is NOT used here: it controls how long a cell burns, not how easily it ignites."""
    wind = math.exp(wind_speed * (c1 + c2 * (math.cos(wind_angle) - 1)))
    slope = np.exp(a * slope_angle)
    p = ignition_prob * wind * slope
    return np.clip(p, 0.0, 1.0)

def calculate_wind_angle(wind_direction, spread_direction):
    diff = wind_direction - spread_direction
    return math.radians(diff)

def transition_function(grid, neighbourstates, neighbourcounts, ignition_prob, fuel, slope_angles):
    flammable = (grid > WATER) & (grid < TOWN)

    not_ignited = np.ones(grid.shape)
    for neighbour, direction, diagonal, slope_angle in zip(neighbourstates, SPREAD_DIRECTIONS, DIAGONAL, slope_angles):
        wind_angle = calculate_wind_angle(WIND_DIRECTION, direction)
        p = decamara_function(ignition_prob, slope_angle, wind_angle=wind_angle)
        if diagonal:
            p = p * DIAGONAL_FACTOR
        not_ignited *= np.where(neighbour == BURNING, 1 - p, 1.0)
    ignite = flammable & (np.random.rand(*grid.shape) < 1 - not_ignited)

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

    ignition_prob = IGNITION[map].astype(float)
    fuel = FUEL[map].astype(float)

    slope_angles = gen_slope_angles(gen_elevation_map(map.shape))

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, (transition_function, ignition_prob, fuel, slope_angles))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
