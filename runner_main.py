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

# Added for collisions
import random


# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers import ObjectInfo, get_random_avatar_position


import numpy as np
from tdw.controller import Controller
from tdw.output_data import OutputData, Rigidbodies

from occlusion_transition import *


class ResetScene(Controller):
    """
    Create multiple trials of an object falling and reset the scene between trials.
    """

    def __init__(self, port: int = 1071, launch_build: bool = True, random_seed: int = 0):
        super().__init__(port=port, launch_build=launch_build)
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)

    def do_trials(self, num_trials: int):
        scenes = ["tdw_room", "iceland_beach", "lava_field", "abandoned_factory"]
        # Divided the total number of trials by the number of scenes.
        num_trials_per_scene = int(num_trials / len(scenes))
        # Initialize a scene for the next batch of trials.
        for scene in scenes:
            self.communicate(self.get_add_scene(scene_name=scene))
            # Do trials for this scene.
            self.do_trials_in_scene(num_trials=num_trials_per_scene)
        self.communicate({"$type": "terminate"})

    def do_trials_in_scene(self, num_trials: int):
        for i in range(num_trials):
            # Add an object with a random rotation and starting height.
            object_id = self.get_unique_id()
            
            trial()

            # Reset the scene by destroying the object.
            self.communicate([{"$type": "destroy_object",
                               "id": object_id},
                              {"$type": "send_rigidbodies",
                               "frequency": "never"}])


if __name__ == "__main__":
    c = ResetScene()
    c.do_trials(num_trials=10000)