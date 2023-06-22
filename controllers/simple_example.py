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

from runner_main import Runner

class Collision(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        self.controller_name = 'simple'

    def trial_initialization_commands(self):
        # Your code here
        return []
    
if __name__ == "__main__":
    c = Collision()
    success = c.run(num=3, pass_masks=['_img'])
    print(success)