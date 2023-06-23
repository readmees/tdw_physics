# STATUS: Not finished
#TODO: random turns/scales/position cube
#TODO: add other objects then cube
#TODO: add more rolling objects
# STATUS: Not updated for new streamlines process yet
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.controller import Controller
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.object_manager import ObjectManager

# Added for video
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from os import chdir, system
from subprocess import call
import shutil

# Added for occlusions
import random


# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers import ObjectInfo, get_random_avatar_position

from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.add_ons.collision_manager import CollisionManager
from tdw.add_ons.object_manager import ObjectManager

# Added for video
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from os import chdir, system
from subprocess import call
import shutil

from helpers import message

# Added for Slopes
import random
import numpy as np

# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers import ObjectInfo, get_random_avatar_position

from runner_main import Runner


class Slope(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        self.controller_name = 'rolling_down'
        
        # Uses models_core.json
        self.objects = ["apple",
                        "golf",
                    "orange"]

    def trial_initialization_commands(self):
        if not self.slope_added:
            return message('Rolling down trials should have slope', 'error')
        
        
        
        o_id1 = self.get_unique_id()
        o_id2 = self.get_unique_id()

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [o_id1]

        commands = []
        commands.extend(self.get_add_physics_object(model_name=random.choice(self.objects),
                                                    library='models_core.json',
                                                    object_id=o_id1,
                                                    position={"x": .5, "y": random.uniform(.5, 1.5), "z": 0}))
        
        return commands
    
if __name__ == "__main__":
    c = Slope()
    success = c.run(num=20, pass_masks=['_img'], room='empty', tot_frames=50, add_slope=True)
    print(success)