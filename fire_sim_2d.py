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

CHAPARRAL, WATER, GRASS, FOREST, TOWN, BURNING, BURNT =  range(7)

def setup(args):
    """Set up the config object used to interact with the GUI"""
    config_path = args[0]
    config = utils.load(config_path)
    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --
    config.title = "Modelling a Forest Fire using Cellular Automata"
    config.dimensions = 2

    config.states = (CHAPARRAL, WATER, GRASS, FOREST, TOWN, BURNING, BURNT)
    gen_map(500, 500)
    # -------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----

    # config.state_colors = [(0,0,0),(1,1,1)]
    # config.grid_dims = (200,200)

    # ----------------------------------------------------------------------

    # the GUI calls this to pass the user defined config
    # into the main system with an extra argument
    # do not change
    if len(args) == 2:
        config.save()
        sys.exit()
    return config

def gen_map(rows, cols):
    map = np.array((rows, cols), CHAPARRAL)
    map = np.full((rows, cols), CHAPARRAL)
    map[50:75, 0:250] = FOREST
    map[75:300, 50:125] = FOREST
    map[300:350, 50:250] = FOREST
    map[100:150, 325:450] = FOREST
    map[125:225, 175:225] = WATER
    map[275:400, 375:400] = WATER
    map[225:250, 250:450] = GRASS
    map[437:462, 187:212] = TOWN
    return map


def transition_function(grid, neighbourstates, neighbourcounts):
    """Function to apply the transition rules
    and return the new grid"""
    # YOUR CODE HERE
    return grid


def main():
    """ Main function that sets up, runs and saves CA"""
    # Get the config object from set up
    config = setup(sys.argv[1:])

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, transition_function)

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
