# STATUS: Not finished
#TODO: random turns/scales/position cube
#TODO: add other objects then cube
#TODO: add more rolling objects

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

# Added for Slopes
import random
import numpy as np

# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers import ObjectInfo, get_random_avatar_position

from runner_main import Runner
from helpers import SlopeInfo

class Slope(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        self.controller_name = 'rolling_down'
        
        # Uses models_core.json
        self.objects = ["apple",
                    "b04_orange_00",
                    "golf",
                    "orange"]
        
        #TODO maybe add more objects that can act as a slope from models_flex.json
        self.slope_name = "cube"
        self.slope_record = [rec for rec in ModelLibrarian('models_flex.json').records if rec.name == self.slope_name][0]

    def trial_initialization_commands(self):
        commands = []
        # Create id(s) for rolling down object(s) #TODO maybe add more rolling down objects
        o_num = random.choice([1])
        self.o_ids = [self.get_unique_id() for i in range(o_num)]
        
        # Set slope id
        slope = SlopeInfo(id=self.get_unique_id(), name=self.slope_name)
        
        # Set randomized physics values and update the physics info for slope
        slope.scale = TDWUtils.get_unit_scale(self.slope_record) * random.uniform(0.8, 1.2)

        commands.extend(self.get_add_physics_object(model_name=slope.name,
                                                    library="models_flex.json",
                                                    object_id=slope.id,
                                                    position={"x": random.uniform(-0.02, 0.02),
                                                              "y": random.uniform(-0.2, 0),
                                                              "z": random.uniform(-0.02, 0.02)},
                                                    rotation={"x": 0,
                                                              "y": 0,
                                                              "z": random.uniform(0, 360)},
                                                    scale_factor={"x": slope.scale, "y": slope.scale, "z": slope.scale}))
        
        #TODO: position should be dependend on scale
        #TODO: rotation can now be 0, fix this
        # commands.append({"$type": "set_rigidbody_constraints", 
        #                  "id": slope.id, 
        #                  "freeze_position_axes": {"x": random.uniform(-0.02, 0.02),
        #                                           "y": random.uniform(-0.2, 0),
        #                                           "z": random.uniform(-0.02, 0.02)}, 
        #                  "freeze_rotation_axes": {"x": 0, "y": 0, "z": random.uniform(0, 360)}})
        return commands
    
if __name__ == "__main__":
    c = Slope()
    success = c.run(num=4, pass_masks=['_img'], room='empty', tot_frames=20)
    print(success)