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

WATER, CHAPARRAL, GRASS, FOREST, CANYON, TOWN, BURNING, BURNT, WATERLOGGED = range(9)
CANYON_WIDTH = 10

# Fire sources from the brief: top-left corner of the 3x3 block of cells set alight at step 0
POWER_PLANT = (0, 0)      # north-west corner
INCINERATOR = (0, 497)    # north-east corner
FIRE_START = POWER_PLANT

# Town as (first row, last row + 1, first col, last col + 1). The town can't burn, so the fire has
# "reached the town" when any cell touching it is burning.
TOWN_AREA = (437, 462, 187, 212)

# --- Time scale ---
# One step = 20 minutes of real time, the same step as Freire & DaCamara (2019) used with 100 m cells.
# So 3 steps = 1 hour and 72 steps = 1 day. Use steps_to_hours() to convert results.
STEP_MINUTES = 20
STEPS_PER_HOUR = 60 // STEP_MINUTES

RECOVERY_RATE = 0.004
REGROWTH_PROBABILITY = 0.001

N, NE, E, SE, S, SW, W, NW = 0, 45, 90, 135, 180, 225, 270, 315
WIND_DIRECTION = NW
# Wind speed (m/s); 8 m/s is the wind-driven threshold in Freire & DaCamara (2019).
WIND_SPEED = 8

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

# How long each terrain burns once alight, from the brief. This does NOT affect how easily it ignites.
#   grass (canyon scrubland): "several hours" -> 6 h
#   chaparral:                "several days"  -> 3 days
#   forest:                   "up to one month" -> 30 days
#   canyon walls are chaparral-covered, so they burn like chaparral
#                      water chaparral grass forest   canyon town
BURN_HOURS = np.array([0,    3 * 24,   6,    30 * 24, 3 * 24, 0])
BURN_STEPS = BURN_HOURS * STEPS_PER_HOUR   # grass 18, chaparral 216, forest 2160 steps

CANYON_DEPTH = 5

# Bodies of water as (row_start, row_end, col_start, col_end) rectangles
WATER_BODIES = [
    (125, 225, 175, 225),
    (275, 400, 375, 400),
]
# Each body of water is surrounded by a wall of waterlogged ground this many cells wide
WATER_BANK_WIDTH = 10

# --- Intervention: water drops ---
# The 500x500 grid covers 50km x 50km, so each cell is 100m x 100m (0.01 km^2)
CELL_SIZE_M = 100
DROP_WIDTH_M = 200                 # every drop is a 100m wide strip (1 cell)
MAX_DROP_AREA_KM2 = 12.5           # total budget, e.g. one 500m x 25000m line
DROP_WIDTH_CELLS = DROP_WIDTH_M // CELL_SIZE_M
MAX_DROP_CELLS = int(round(MAX_DROP_AREA_KM2 * 1e6 / CELL_SIZE_M ** 2))

INITIAL_MOISTURE = 5              # moisture given to a cell when water is dropped on it
BANK_MOISTURE = INITIAL_MOISTURE     # starting moisture of the waterlogged ground around water
HEAT_EVAPORATION_RATE = 0.05       # extra moisture lost per burning neighbour (steam)

# Each drop is a 500m wide rectangle:
#   row, col    - top-left cell of the rectangle
#   length_m    - length of the strip in metres
#   orientation - 'H' (runs east-west) or 'V' (runs north-south)
#   generation  - generation the water is dropped on
# The total area of all drops must not exceed MAX_DROP_AREA_KM2.
WATER_DROPS = [
    dict(row=345, col=0, length_m=5000, orientation='H', generation=0),
    dict(row=347, col=0, length_m=5000, orientation='H', generation=0),
    dict(row=75, col=0, length_m=5000, orientation='H', generation=0),
    dict(row=77, col=0, length_m=5000, orientation='H', generation=0),
    dict(row=345, col=250, length_m=12500, orientation='H', generation=0),
    dict(row=347, col=250, length_m=12500, orientation='H', generation=0),
    dict(row=347, col=400, length_m=10000, orientation='H', generation=0),
    dict(row=349, col=400, length_m=7500, orientation='H', generation=0)
]

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

    config.states = (WATER, CHAPARRAL, GRASS, FOREST, CANYON, TOWN, BURNING, BURNT, WATERLOGGED)
    fire_start = gen_initial_grid(gen_map())

    # Apply the waterlogged banks and any drops scheduled for generation 0 so they
    # appear in the initial grid (the moisture/terrain grids are rebuilt identically in main)
    validate_water_drops(WATER_DROPS)
    apply_water_banks(fire_start, np.zeros(fire_start.shape), fire_start.copy())
    apply_water_drops(fire_start, np.zeros(fire_start.shape), fire_start.copy(), 0)
    config.initial_grid = fire_start

    config.wrap = False
    # -------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----

    # config.state_colors = [(0,0,0),(1,1,1)]
    # config.grid_dims = (200,200)

    config.grid_dims = fire_start.shape
    config.state_colors = [
        (0/255, 0/255, 255/255), # Water
        (101/255, 85/255, 33/255), # Chaparral
        (124/255, 252/255, 0/255), # Grass
        (34/255, 139/255, 34/255), # Forest
        (160/255, 110/255, 60/255), # Canyon wall
        (0/255, 0/255, 0/255), # Town
        (255/255, 0/255, 0/255), # Burning
        (50/255, 50/255, 50/255), # Burnt
        (135/255, 206/255, 250/255), # Waterlogged
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
    for r0, r1, c0, c1 in WATER_BODIES:
        map[r0:r1, c0:c1] = WATER

    map[225 - CANYON_WIDTH:250 + CANYON_WIDTH, 250 - CANYON_WIDTH:450 + CANYON_WIDTH] = CANYON
    map[225:250, 250:450] = GRASS
    r0, r1, c0, c1 = TOWN_AREA
    map[r0:r1, c0:c1] = TOWN
    return map

def gen_initial_grid(map):
    """Return the map with the starting fire placed on it"""
    fire_start = map.copy()
    row, col = FIRE_START
    fire_start[row:row + 3, col:col + 3] = BURNING
    return fire_start

def fire_at_town(grid):
    """True if any cell in the ring around the town is burning"""
    r0, r1, c0, c1 = TOWN_AREA
    return (grid[max(r0 - 1, 0):r1 + 1, max(c0 - 1, 0):c1 + 1] == BURNING).any()

def drop_cells(drop):
    """Return the (row_start, row_end, col_start, col_end) bounds covered by a drop.

    The end bounds are exclusive.
    """
    length_cells = drop['length_m'] // CELL_SIZE_M
    r, c = drop['row'], drop['col']
    if drop['orientation'] == 'H':
        return r, r + DROP_WIDTH_CELLS, c, c + length_cells
    if drop['orientation'] == 'V':
        return r, r + length_cells, c, c + DROP_WIDTH_CELLS
    raise ValueError("Drop orientation must be 'H' or 'V', got %r" % drop['orientation'])

def validate_water_drops(drops):
    """Check the drops do not exceed the total water budget"""
    total_cells = sum(DROP_WIDTH_CELLS * (d['length_m'] // CELL_SIZE_M) for d in drops)
    if total_cells > MAX_DROP_CELLS:
        raise ValueError("Water drops cover %.2f km^2, the maximum is %.2f km^2"
                         % (total_cells * CELL_SIZE_M ** 2 / 1e6, MAX_DROP_AREA_KM2))

def apply_water_drops(grid, moisture, terrain, generation):
    """Waterlog every unburnt vegetation cell under a drop scheduled for this generation.

    The cell's current state is remembered in `terrain` so it can be restored once dry.
    Water, towns, burning and burnt cells are left unchanged.
    Cells that are already waterlogged are topped back up to INITIAL_MOISTURE.
    """
    for drop in WATER_DROPS:
        if drop['generation'] != generation:
            continue
        r0, r1, c0, c1 = drop_cells(drop)
        g = grid[r0:r1, c0:c1]
        wet = moisture[r0:r1, c0:c1]
        ter = terrain[r0:r1, c0:c1]

        vegetation = (g > WATER) & (g < TOWN)
        ter[vegetation] = g[vegetation]
        g[vegetation] = WATERLOGGED

        wet[g == WATERLOGGED] = INITIAL_MOISTURE

def apply_water_banks(grid, moisture, terrain):
    """Waterlog a WATER_BANK_WIDTH wide wall of ground around every body of water.

    Like a water drop, the cell's original terrain is remembered in `terrain` so it
    returns to it once dry. Only vegetation is waterlogged (water, towns, burning and
    burnt cells are left unchanged).
    """
    h, w = grid.shape
    for r0, r1, c0, c1 in WATER_BODIES:
        rows = slice(max(r0 - WATER_BANK_WIDTH, 0), min(r1 + WATER_BANK_WIDTH, h))
        cols = slice(max(c0 - WATER_BANK_WIDTH, 0), min(c1 + WATER_BANK_WIDTH, w))
        g, wet, ter = grid[rows, cols], moisture[rows, cols], terrain[rows, cols]

        vegetation = (g > WATER) & (g < TOWN)
        ter[vegetation] = g[vegetation]
        g[vegetation] = WATERLOGGED
        wet[vegetation] = BANK_MOISTURE

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
    Burn time (BURN_STEPS) is NOT used here: it controls how long a cell burns, not how easily it ignites."""
    wind = math.exp(wind_speed * (c1 + c2 * (math.cos(wind_angle) - 1)))
    slope = np.exp(a * slope_angle)
    p = ignition_prob * wind * slope
    return np.clip(p, 0.0, 1.0)

def steps_to_hours(steps):
    """Convert a number of simulation steps into hours of real time."""
    return steps / STEPS_PER_HOUR

def calculate_wind_angle(wind_direction, spread_direction):
    diff = wind_direction - spread_direction
    return math.radians(diff)

def transition_function(grid, neighbourstates, neighbourcounts, ignition_prob, burn_time_left, regrowth,
                        slope_angles, moisture, terrain, generation, town_arrival):
    # generation is a 1-element array so the count persists between calls
    generation[0] += 1
    apply_water_drops(grid, moisture, terrain, generation[0])

    burning_neighbours = neighbourcounts[BURNING]
    unburnt = grid < BURNING
    burning = grid == BURNING
    burnt = grid == BURNT

    # Waterlogged cells sit outside this range, so they have 0% flammability until dry
    flammable = (grid > WATER) & (grid < TOWN)

    not_ignited = np.ones(grid.shape)
    for neighbour, direction, diagonal, slope_angle in zip(neighbourstates, SPREAD_DIRECTIONS, DIAGONAL, slope_angles):
        wind_angle = calculate_wind_angle(WIND_DIRECTION, direction)
        p = decamara_function(ignition_prob, slope_angle, wind_angle=wind_angle)
        if diagonal:
            p = p * DIAGONAL_FACTOR
        not_ignited *= np.where(neighbour == BURNING, 1 - p, 1.0)
    ignite = flammable & (np.random.rand(*grid.shape) < 1 - not_ignited)

    # Each burning cell counts down its remaining burn time (in steps) and goes out at 0
    burn_time_left[burning] -= 1
    burnt_out = burning & (burn_time_left <= 0)

    grid[ignite] = BURNING
    grid[burnt_out] = BURNT

    # Record the first step the fire touches the town (0 = not reached yet)
    if town_arrival[0] == 0 and fire_at_town(grid):
        town_arrival[0] = generation[0]

    # Regrowth: burnt cells slowly build up new vegetation, then may regrow as chaparral
    regrowth[burnt] += RECOVERY_RATE * 0.6 * np.random.random(np.count_nonzero(burnt))
    reborn = burnt & (regrowth >= 0.6) & (np.random.random(grid.shape) < REGROWTH_PROBABILITY)
    grid[reborn] = CHAPARRAL
    # A regrown cell behaves like fresh chaparral: chaparral ignition chance and a full burn timer
    ignition_prob[reborn] = IGNITION[CHAPARRAL]
    burn_time_left[reborn] = BURN_STEPS[CHAPARRAL]
    regrowth[reborn] = 0

    # Waterlogged cells dry out slowly, and faster next to fire as the water turns to steam.
    # Once the moisture reaches 0 the cell returns to its original terrain and can burn again.
    waterlogged = grid == WATERLOGGED
    moisture[waterlogged] -= HEAT_EVAPORATION_RATE * burning_neighbours[waterlogged] + (0.5 * HEAT_EVAPORATION_RATE * burnt[waterlogged])
    dried = waterlogged & (moisture <= 0)
    moisture[dried] = 0
    grid[dried] = terrain[dried]

    return grid

def main():
    """ Main function that sets up, runs and saves CA"""
    # Get the config object from set up
    config = setup(sys.argv[1:])
    map = gen_map()

    ignition_prob = IGNITION[map].astype(float)
    burn_time_left = BURN_STEPS[map].astype(int)   # steps each cell will burn for once alight
    regrowth = np.zeros(map.shape)                 # vegetation regrown on burnt cells (regrows at 0.6)

    slope_angles = gen_slope_angles(gen_elevation_map(map.shape))

    # Same-sized grids for the intervention: how wet each cell is, and what terrain
    # it should go back to once dry. Rebuild the banks and generation 0 drops exactly as in setup.
    validate_water_drops(WATER_DROPS)
    moisture = np.zeros(map.shape)
    terrain = map.copy()
    initial = gen_initial_grid(map)
    apply_water_banks(initial, moisture, terrain)
    apply_water_drops(initial, moisture, terrain, 0)
    generation = np.zeros(1, dtype=int)
    town_arrival = np.zeros(1, dtype=int)   # step the fire first touches the town (0 = not yet)

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, (transition_function, ignition_prob, burn_time_left, regrowth, slope_angles,
                           moisture, terrain, generation, town_arrival))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # CAPyLE prints this in the terminal once the run finishes
    source = {POWER_PLANT: "power plant", INCINERATOR: "incinerator"}.get(FIRE_START, str(FIRE_START))
    if town_arrival[0]:
        hours = steps_to_hours(town_arrival[0])
        print(f"Fire from the {source} reached the town at step {town_arrival[0]} "
              f"({hours:.0f} hours, {hours / 24:.1f} days)")
    else:
        print(f"Fire from the {source} did not reach the town within {config.num_generations} steps")

    # Save updated config to file
    config.save()
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
