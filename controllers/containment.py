# STATUS: V1 Experimental
'''
Readme:
The core of of this code is taken from tdw_physics, from containment.py and stability.py
tdw_physics uses custom/random physics, here we use the default

Possible improvements:
'''
from typing import List
from random import choice, uniform
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from tdw.librarian import ModelLibrarian
from tdw.add_ons.third_person_camera import ThirdPersonCamera

import random

from helpers.runner_main import Runner
from helpers.objects import CONTAINERS, CONTAINED
from helpers.helpers import get_two_random_records
class Containment(Runner):
    """
    Create a set of "Containment" trials, where a container object holds a smaller target
    object and is shaken violently, causing the target object to move around and possibly fall out.
    """

    Controller.MODEL_LIBRARIANS["models_core.json"] = ModelLibrarian("models_core.json")
    
    O_X = -1.3
    O_Z = -2.15

    def __init__(self, port: int = 1071):
        self.controller_name = 'containment'
        super().__init__(port=port)

    def add_object_to_scene(self, commands):
        '''This method will add a fixed object to the scene that the container has something to balance/shake on,
        since the object will not change during trials and is fixed in place, it will be added to the background shot'''
        balancer_name = random.choice([record.name for record in ModelLibrarian('models_flex.json').records])
        
        balancer_scale = .5
        object_id = self.get_unique_id()

        # Add the object
        commands.extend(self.get_add_physics_object(model_name=balancer_name,
                                                library="models_flex.json",
                                                object_id=object_id,
                                                position={"x": Containment.O_X,
                                                            "y": 0,
                                                            "z": Containment.O_Z},
                                                rotation=TDWUtils.VECTOR3_ZERO,
                                                scale_factor={"x": balancer_scale,
                                                                "y": balancer_scale,
                                                                "z": balancer_scale}))
        
        # Freeze position and rotation for each axis
        commands.extend([{"$type": "set_rigidbody_constraints", "id": object_id, "freeze_position_axes": {"x": 1, "y": 1, "z": 1}, "freeze_rotation_axes": {"x": 1, "y": 1, "z": 1}}])
        
        # Set a random color.
        commands.append({"$type": "set_color",
                        "color": {"r": random.random(), "g": random.random(), "b": random.random(), "a": 1.0},
                        "id": object_id})
        return commands
    
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp' '''
        # Add camera
        camera = ThirdPersonCamera(position={"x": uniform(-1,0), "y": uniform(1.8,2.2), "z": uniform(-1, 0)},
                           look_at={"x": -1.0, "y": 1.0, "z": -1.5},
                           avatar_id='frames_temp')
        self.add_ons.append(camera)

    def trial_initialization_commands(self):
        commands = []
        # Select a random container and contained object
        records = get_two_random_records(smaller_list=CONTAINED, larger_list=CONTAINERS)[0]
        
        # Select a container.
        # Manually set the mass of the container.
        container_id = self.get_unique_id()
        commands.extend(self.get_add_physics_object(model_name=records[1].name,
                                                    library="models_core.json",
                                                    object_id=container_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.5,
                                                              "z": Containment.O_Z},
                                                    rotation={"x": uniform(-10, 10),
                                                              "y": uniform(-10, 10),
                                                              "z": uniform(-10, 10)}))
        
        # Add a random target object, with random size, mass, bounciness and initial orientation.
        o_record = records[0]
        o_id = self.get_unique_id()
        self.o_ids = [o_id, container_id]
        commands.extend(self.get_add_physics_object(model_name=o_record.name,
                                                    library="models_core.json",
                                                    object_id=o_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.8,
                                                              "z": Containment.O_Z},
                                                    rotation={"x": uniform(-45, 45),
                                                              "y": uniform(-45, 45),
                                                              "z": uniform(-45, 45)}))

        return commands

if __name__ == "__main__":
    c = Containment()
    success = c.run(num=5, pass_masks=['_img'] , room='empty', tot_frames=50, add_object_to_scene=True, trial_type='object')
    print(success)