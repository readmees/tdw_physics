from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.controller import Controller
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.collision_manager import CollisionManager
from tdw.add_ons.object_manager import ObjectManager

# Added for video
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from os import chdir, system
from subprocess import call
import shutil
import random

# Added for collisions

from runner_main import Runner

class Collision(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        self.controller_name = 'simple'

    def trial_initialization_commands(self):
        '''This method implements objects bumping into each other, 
        by placing next to the other, then applying a force
         towards the other one'''
        self.o_ids = [self.get_unique_id() for _ in range(1)]
        # o_id1, o_id2 = self.o_ids
        o_id1 = self.o_ids[0]
        commands = [{"$type": "send_rigidbodies",
                                    "frequency": "always"}]
        
        commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": 0, "z": 0}))
        # commands.extend([{"$type": "object_look_at",
        #                   "other_object_id": o_id1,
        #                   "id": o_id2},
        #                  {"$type": "apply_force_magnitude_to_object",
        #                   "magnitude": random.uniform(20, 60),
        #                   "id": o_id2}])
        return commands
if __name__ == "__main__":
    c = Collision()
    success = c.run(num=3, pass_masks=['_img'])
    print(success)