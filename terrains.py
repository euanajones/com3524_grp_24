class Terrain():
    """
    A class to represent a terrain in the fire simulation. Used as a superclass for specific terrain types. 
    Each terrain type has its own ignition probability and fuel resource value.

    Attributes
    ----------
    x: int
        The x-coordinate of the terrain.
    y: int
        The y-coordinate of the terrain.
    color: tuple
        The RGB color representation of the terrain.
    terrain_type: str
        The type of terrain (e.g., 'chaparral', 'body_of_water', 'grassland', 'dense_forest').
    near_water: bool
        Whether the terrain is near water, which can affect fire ignition probability.
    ignition_threshold: float
        The threshold value for fire ignition, used in calculating the probability of fire ignition.
    ignition_probability: float
        The probability of fire ignition for this terrain type.
    fuel_resource: float
        The amount of fuel available in this terrain type, which can affect fire spread.

    Methods
    -------
    catches_fire(self):
        Determines if the terrain catches fire based on its ignition probability and other factors.
    """

    def __init__(self, terrain_type):
        """
        Initializes a Terrain object with default attributes.

        Parameters
        ----------
        x: int
            The x-coordinate of the terrain.
        y: int
            The y-coordinate of the terrain.
        terrain_type: str
            The type of terrain (e.g., 'chaparral', 'body_of_water', 'grassland', 'dense_forest').
        near_water: bool
            Whether the terrain is near water, which can affect fire ignition probability.
        ignition_threshold: float
            The threshold value for fire ignition, used in calculating the probability of fire ignition.
        ignition_probability: float
            The probability of fire ignition for this terrain type.
        fuel_resource: float
            The amount of fuel available in this terrain type, which can affect fire spread.
        """
        self.x = 0
        self.y = 0
        self.color = (0, 0, 0)
        self.terrain_type = terrain_type
        self.near_water = False
        self.ignition_threshold = 1.0
        self.ignition_probability = 0.0
        self.fuel_resource = 0.0

    def catches_fire(self):
        """
        Determines if the terrain catches fire based on its ignition probability and other factors.

        Returns
        -------
        bool
            True if the terrain catches fire, False otherwise.
        """
        # Implement logic to determine if the terrain catches fire based on its attributes
        # For example, you could use a random number generator and compare it to the ignition probability
        import random
        return random.random() < self.ignition_probability

class Chaparral(Terrain):
    """
    A class to represent a chaparral terrain in the fire simulation. 
    Inherits from the Terrain class.

    Attributes
    ----------
    x: int
        The x-coordinate of the terrain.
    y: int
        The y-coordinate of the terrain.
    near_water: bool
        Whether the terrain is near water, which can affect fire ignition probability.
    color: tuple
        The RGB color representation of the chaparral terrain.
    ignition_probability: float
        The probability of fire ignition for the chaparral terrain type.
    fuel_resource: float
        The amount of fuel available in the chaparral terrain type, which can affect fire spread.
    """
    def __init__(self, x, y, near_water=False):
        super().__init__('chaparral')
        self.x = x
        self.y = y
        self.near_water = near_water

        # Fixed attributes for the chaparral terrain type, can be adjusted based on simulation needs
        self.color = (101, 67, 33)
        self.ignition_probability = 0.6
        self.fuel_resource = 0.6

class BodyOfWater(Terrain):
    """
    A class to represent a body of water terrain in the fire simulation.
    Inherits from the Terrain class.

    Attributes
    ----------
    x: int
        The x-coordinate of the terrain.
    y: int
        The y-coordinate of the terrain.
    near_water: bool
        Whether the terrain is near water, which can affect fire ignition probability.
    color: tuple
        The RGB color representation of the body of water terrain.
    ignition_probability: float
        The probability of fire ignition for the body of water terrain type.
    fuel_resource: float
        The amount of fuel available in the body of water terrain type, which can affect fire spread
    """
    def __init__(self, x, y, near_water=False):
        super().__init__('body_of_water')
        self.x = x
        self.y = y
        self.near_water = near_water
        
        # Fixed attributes for the body of water terrain type, can be adjusted based on simulation needs
        self.color = (0, 0, 255)
        self.ignition_probability = 0.0
        self.fuel_resource = 0.0

class Grassland(Terrain):
    """
    A class to represent a grassland terrain in the fire simulation.
    Inherits from the Terrain class.

    Attributes
    ----------
    x: int
        The x-coordinate of the terrain.
    y: int
        The y-coordinate of the terrain.
    near_water: bool
        Whether the terrain is near water, which can affect fire ignition probability.
    color: tuple
        The RGB color representation of the grassland terrain.
    ignition_probability: float
        The probability of fire ignition for the grassland terrain type.
    fuel_resource: float
        The amount of fuel available in the grassland terrain type, which can affect fire spread.
    """
    def __init__(self, x, y, near_water=False):
        super().__init__('grassland')
        self.x = x
        self.y = y
        self.near_water = near_water

        # Fixed attributes for the grassland terrain type, can be adjusted based on simulation needs
        self.color = (124, 252, 0)
        self.ignition_probability = 0.8
        self.fuel_resource = 0.15

class DenseForest(Terrain):
    """
    A class to represent a dense forest terrain in the fire simulation.
    Inherits from the Terrain class.

    Attributes
    ----------
    x: int
        The x-coordinate of the terrain.
    y: int
        The y-coordinate of the terrain.
    near_water: bool
        Whether the terrain is near water, which can affect fire ignition probability.
    color: tuple
        The RGB color representation of the dense forest terrain.
    ignition_probability: float
        The probability of fire ignition for the dense forest terrain type.
    fuel_resource: float
        The amount of fuel available in the dense forest terrain type, which can affect fire spread.
    """
    def __init__(self, x, y, near_water=False):
        super().__init__('dense_forest')
        self.x = x
        self.y = y
        self.near_water = near_water

        # Fixed attributes for the dense forest terrain type, can be adjusted based on simulation needs
        self.color = (34, 139, 34)
        self.ignition_probability = 0.2
        self.fuel_resource = 1.0