# STATUS: V1 - Experimential
'''
Readme:

Possible improvements:
random turns/scales/position cube
add other objects then cube
add more rolling objects
Always make two versions of the exact same trial, object and transition?

'''
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict

# Added for video
# Added for occlusions
import random


# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers.helpers import ObjectInfo, get_random_avatar_position

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

from helpers.helpers import message

# Added for Slopes
import random
import numpy as np

# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers.helpers import ObjectInfo, get_random_avatar_position

from helpers.runner_main import Runner
from helpers.objects import ROLLING_FLIPPED


class Slope(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        self.controller_name = 'rolling_down'
        
        # Uses models_core.json
        self.objects = ["apple",
                        "golf",
                    "orange"]
        self.objects.extend(ROLLING_FLIPPED)
        
    def run_per_frame_commands(self, trial_type, tot_frames):
        '''Communicate once for every frame
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param tot_frames: the total amount of frames per trial
        '''
        #TODO: improve transition
        transition_frame = random.choice(list(range(tot_frames//3, tot_frames)))
        for i in range(tot_frames):
            if i >= transition_frame and trial_type == 'transition':
                print('transition, started')
                self.communicate([{"$type": "teleport_object_by", "position": {"x": -.05, "y": 0.0, "z": 0}, "id": self.o_ids[0], "absolute": True}])
            else:
                self.communicate([])

        destroy_commands = []
        for o_id in self.o_ids:
            # Reset the scene by destroying the object.
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)

    def add_object_to_scene(self, commands = []):
        '''This method adds a slope for the rolling down trials, by adding a freezed cube object and a wall to bounce too
        since the object will not change during trials and is fixed in place, it will be added to the background shot'''
        ids = [self.get_unique_id(), self.get_unique_id()]
        slope_id = ids[0]
        wall_id = ids[1]

        # Add slope
        commands.extend(self.get_add_physics_object(model_name="cube",
                                                    library="models_flex.json",
                                                    object_id=slope_id,
                                                    rotation={"x": 0, "y": 0, "z": random.uniform(216, 244)},
                                                    position={"x": -.5, "y": 0, "z": 0},
                                                    scale_factor = {"x": .8, "y": .8, "z": .8}))
        
        # Add wall
        commands.extend(self.get_add_physics_object(model_name="cube",
                                                    library="models_flex.json",
                                                    object_id=wall_id,
                                                    position={"x": .5, "y": 0, "z": 0},
                                                    rotation={"x": 0, "y": 180, "z": 0},
                                                    scale_factor={"x": .1, "y": .25, "z": .5}
                                                    ))
        for object_id in ids:
            # Freeze position and rotation for each axis
            commands.extend([{"$type": "set_rigidbody_constraints", "id": object_id, "freeze_position_axes": {"x": 1, "y": 1, "z": 1}, "freeze_rotation_axes": {"x": 1, "y": 1, "z": 1}}])
            # Set a random color.
            commands.append({"$type": "set_color",
                            "color": {"r": random.random(), "g": random.random(), "b": random.random(), "a": 1.0},
                            "id": object_id})
        return commands
    
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp'
        '''
        # Add camera
        camera = ThirdPersonCamera(position={"x": 0, "y": 1.2, "z": -1},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id='frames_temp')
        self.add_ons.append(camera)

    def trial_initialization_commands(self):
        if not self.slope_added:
            return message('Rolling down trials should have slope', 'error')
        
        
        
        o_id1 = self.get_unique_id()
        o_id2 = self.get_unique_id()

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [o_id1]

        commands = []

        object_choice = random.choice(self.objects)
        rotation_x = 0 if object_choice not in ROLLING_FLIPPED else random.choice([90, -90])
        commands.extend(self.get_add_physics_object(model_name=object_choice,
                                                    library='models_core.json',
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": random.uniform(.5, 1.5), "z": 0},
                                                    rotation={"x": rotation_x, "y": 0, "z": 0}))
        return commands
    
if __name__ == "__main__":
    c = Slope()
    success = c.run(num=20, pass_masks=['_img', '_id'], room='empty', tot_frames=200, add_object_to_scene=True, trial_type='object')
    print(success)