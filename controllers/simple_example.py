# STATUS: Passing
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

from helpers.runner_main import Runner

class Collision(Runner):
    def collision_fall(self, commands, o_id1, o_id2):
        '''This method implements objects falling on top of each other, 
        by placing one above the other'''
        commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": 3, "z": 0}))
        commands.extend(self.get_add_physics_object(model_name="rh10",
                                                object_id=o_id2,
                                                position={"x": 0, "y": 0, "z": 0}))
        return commands
        
    def collision_force(self, commands, o_id1, o_id2):
        '''This method implements objects bumping into each other, 
        by placing next to the other, then applying a force towards the other one'''
        commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": 0, "z": 1}))
        commands.extend(self.get_add_physics_object(model_name="rh10",
                                                object_id=o_id2,
                                                position={"x": 1, "y": 0, "z": 1}))
        commands.extend([{"$type": "object_look_at",
                          "other_object_id": o_id1,
                          "id": o_id2},
                         {"$type": "apply_force_magnitude_to_object",
                          "magnitude": random.uniform(20, 60),
                          "id": o_id2}])
        return commands
        
    def __init__(self):
        super().__init__(port=1000) 
        self.controller_name = 'simple'

    def trial_initialization_commands(self):
        o_id1 = self.get_unique_id()
        o_id2 = self.get_unique_id()

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [o_id1, o_id2]

        commands = self.collision_force([], o_id1, o_id2)
        return commands
    
if __name__ == "__main__":
    c = Collision()
    success = c.run(num=3, pass_masks=['_img'], room='empty', add_slope=False, tot_frames=100, png=False)
    print(success)