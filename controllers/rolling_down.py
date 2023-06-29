# STATUS: V1 - Experimential
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


class Slope(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        self.controller_name = 'rolling_down'
        
        # Uses models_core.json
        self.objects = ["apple",
                        "golf",
                    "orange"]
    
    def run_per_frame_commands(self, trial_type, tot_frames):
        '''Communicate once for every frame
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param tot_frames: the total amount of frames per trial
        '''
        #TODO: improve transition
        transition_frame = random.choice(list(range(tot_frames)))
        # transition_frame = tot_frames//3
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
    success = c.run(num=3, pass_masks=['_img', '_id', '_category'], room='empty', tot_frames=150, add_slope=True, trial_type='transition')
    print(success)