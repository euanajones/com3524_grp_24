# COM3524 Bioinspired Computing - Group 24 Project

A cellular automaton (CA) model of a forest fire spreading towards a town, built on the CAPyLE tool.
It estimates how long a fire from the power plant or the incinerator takes to reach the town. It also
tests the effect of wind direction, an aerial water drop, extra forest and firebreaks.

## Team Members

- Ben Lamb
- Euan Jones
- Harry James
- James Okolie


## Files

| File | What it is |
|---|---|
| `fire_sim_2d.py` | **The model.** Run this one. |
| `team24_terrain.py`, `terrains.py` | An early prototype. These files are not used by the final model. |

## Requirements

- The CAPyLE tool (`CA_tool`) from the module's Blackboard page.
- The `COM3524` conda environment, created from `environment_COM3524.yml`. Follow the module's CAPyLE
  install instructions (Option 1).

## How to run

1. Copy `fire_sim_2d.py` into the tool's `ca_descriptions` folder:

   ```text
   CA_tool/ca_descriptions/fire_sim_2d.py
   ```

2. Open an Anaconda Prompt and start the tool:

   ```bash
   conda activate COM3524
   cd <path>/CA_tool
   python main.py
   ```

3. In the tool, choose **File → Open**, then select `ca_descriptions/fire_sim_2d.py`.
4. Set **Generations** so the fire has time to reach the town:
   - about **1000** is enough with the default settings, from either incinerator or power plant fire
   - use **1500** if you change the wind to blow away from the town (for example `N` or `NE` with an
     incinerator fire).
5. Click **Apply configuration & run CA**, then **Play**. You can also drag the slider to move through
   the steps.

When the run finishes, the model prints how long the fire took to reach the town in the terminal you
started the tool from. The message appears when you close the tool's window. For example, with the
default settings:

```text
Fire from the power plant reached the town at step 484 (161 hours, 6.7 days)
```

The exact step changes a little from run to run, because the fire spreads randomly.

If the fire never reaches the town, it prints `did not reach the town within N steps` instead.

**Changing a setting:** edit the constant near the top of `fire_sim_2d.py` and save. Then copy the file
into `ca_descriptions` again and reopen it in the tool (step 3). The tool only reads the file when it
is opened.

## Map and time scale

- **Grid:** 500 × 500 cells. Each cell is 100 m × 100 m, so the grid covers 50 km × 50 km.
- **Coordinates:** `(row, column)`. Row 0 is the north edge and column 0 is the west edge.
- **Time:** one step is 20 minutes (Freire & DaCamara, 2019). So 3 steps = 1 hour and 72 steps = 1 day.

| Colour | State |
|---|---|
| Dark blue | Lake |
| Olive brown | Chaparral (burns for 3 days) |
| Bright green | Grass in the canyon (burns for 6 hours) |
| Dark green | Dense forest (burns for 30 days, hard to ignite) |
| Light brown | Canyon walls |
| Black | Town |
| Red | Burning |
| Dark grey | Burnt out |
| Light blue | Waterlogged ground (lake banks and water drops); cannot burn until it dries |
| Pale sand | Firebreak (cleared ground that never burns) |

## Settings for each client question

All settings are constants near the top of `fire_sim_2d.py`.

| Question | Setting | How to use it |
|---|---|---|
| 1. Time to reach the town from each source | `FIRE_START` | `POWER_PLANT` (north-west corner) or `INCINERATOR` (north-east corner) |
| 2. Effect of wind direction | `WIND_DIRECTION` | One of `N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW` |
| 2. Wind strength | `WIND_SPEED` | In m/s (default 8) |
| 3. Water drop (12.5 km²) | `WATER_DROPS` | A list of strips; see below |
| 4. Extra forest | `FOREST_EXTENSIONS` | A list of rectangles; see below |
| 4. Firebreaks | `FIREBREAKS` | A list of rectangles; see below |

**Wind direction is the direction the wind blows *towards*.** For example, `WIND_DIRECTION = SW` is a
wind blowing towards the south-west, which weather reports call a north-easterly wind. The town is
south-west of the incinerator, so `SW` brings the fire to the town fastest.

**Rectangles** (`FOREST_EXTENSIONS`, `FIREBREAKS`) are written as
`(row_start, row_end, col_start, col_end)`. The end values are not included. For example, this ring of
firebreak round the town stops the fire reaching it:

```python
FIREBREAKS = [(417, 418, 167, 232), (481, 482, 167, 232), (417, 482, 167, 168), (417, 482, 231, 232)]
```

Leave both lists empty (`[]`) to run the original map.

**Water drops** (`WATER_DROPS`) are strips, each written as
`dict(row=..., col=..., length_m=..., orientation='H' or 'V', generation=...)`:

- `row`, `col`: the top-left cell of the strip.
- `length_m`: the strip's length in metres. Each strip is 200 m wide.
- `orientation`: `'H'` runs east–west and `'V'` runs north–south.
- `generation`: the step on which the water is dropped. Use 0 for the start of the fire.

If the strips cover more than 12.5 km² in total, the model refuses to run and shows an error.

## How the model works

Each step, an unburnt cell next to a burning cell catches fire with a probability from the spread
equation of Alexandridis et al. (2008), as used by Freire & DaCamara (2019):

```text
p = P0 × (1 + p_veg) × (1 + p_den) × p_wind × p_slope
```

- `P0` is the base spread probability (0.58).
- `p_veg` and `p_den` set how easily each type of vegetation ignites.
- `p_wind` is calculated separately for each of the 8 neighbours, from the wind speed and the angle
  between the wind and the direction the fire would spread.
- `p_slope` comes from a height map. It makes fire spread faster uphill, for example up the canyon walls.
- Diagonal neighbours are further away, so their probability is multiplied by 1/√2.

The chances from all burning neighbours are combined as `1 − Π(1 − p)`. A cell keeps burning for the
time its terrain burns for, given in the brief, and then becomes burnt out. Burnt cells can slowly
regrow as chaparral.
