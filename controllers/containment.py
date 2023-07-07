# STATUS: V1 Experimental
'''
Readme:
The core of of this code is taken from tdw_physics, from containment.py and stability.py

Possible improvements:
Shaking doesn't work yet
Freeze y-axis; probably not necessary with 'new' containment idea
Think about physics settings (fixed/random/real)
Make sure contained object fits
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
class Containment(Runner):
    """
    Create a set of "Containment" trials, where a container object holds a smaller target
    object and is shaken violently, causing the target object to move around and possibly fall out.
    """

    Controller.MODEL_LIBRARIANS["models_core.json"] = ModelLibrarian("models_core.json")
    
    O_X = -1.3
    O_Z = -2.15

    def __init__(self, port: int = 1071):
        super().__init__(port=port)

        self.controller_name = 'containment'

        #TODO not sure if we need to use the rest from tdw_physics:
        # for key in PHYSICS_INFO:
        #     # All containers have the same physics values. Set these manually.
        #     if key in Containment.CONTAINERS:
        #         PHYSICS_INFO[key].mass = 3

    def get_two_random_records(self):
        '''This method gets two objects, where 
        container is bigger in width and height''' 
        # Store globals in locals, so we can remove objects temporary
        # Choose a random moving object
        o_contained_name = random.choice(CONTAINED)

        # Get record of moving object
        rec_moving = self.records[CONTAINED_DICT[o_moving_name]]

        # Get height and width of moving object #TODO check this formula
        height_moving = abs(rec_moving.bounds['top']['y'] - rec_moving.bounds['bottom']['y'])
        width_moving = abs(rec_moving.bounds['left']['z'] - rec_moving.bounds['right']['z'])

        # Make sure the occluding object covers the other object
        while True:
            # Choose a random occluder object without putting back
            o_occlu_name = random.choice(occluders)
            occluders.remove(o_occlu_name)
            
            # Get record of moving object
            rec_occlu = self.records[OCCLUDERS_DICT[o_occlu_name]]

            # Calculate height and width of occluder #TODO check this formula
            height_occl = abs(rec_occlu.bounds['top']['y'] - rec_occlu.bounds['bottom']['y'])

            #NOTE TODO Somehow width is often 0
            width_occl = abs(rec_occlu.bounds['left']['z'] - rec_occlu.bounds['right']['z'])

            #NOTE TODO Somehow width is often 0
            if height_occl > height_moving:
                return [rec_moving, rec_occlu], [height_occl, width_moving]
            
            # If none of records is bigger then moving object
            if not occluders:
                return [], [height_occl, width_moving]
            
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp' '''
        # Add camera
        camera = ThirdPersonCamera(position={"x": -0.625, "y": 2.0, "z": -0.7},
                           look_at={"x": -1.0, "y": 1.0, "z": -1.5},
                           avatar_id='frames_temp')
        self.add_ons.append(camera)

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
    
    def trial_initialization_commands(self):
        commands = []
        # Select a container.
        # Manually set the mass of the container.
        container_name = choice(CONTAINERS)
        container_scale = 1
        container_id = self.get_unique_id()
        commands.extend(self.get_add_physics_object(model_name=container_name,
                                                    library="models_core.json",
                                                    object_id=container_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.5,
                                                              "z": Containment.O_Z},
                                                    rotation=TDWUtils.VECTOR3_ZERO,
                                                    scale_factor={"x": container_scale,
                                                                  "y": container_scale,
                                                                  "z": container_scale}))
        
        # Add a random target object, with random size, mass, bounciness and initial orientation.
        object_name = choice(CONTAINED)
        o_id = self.get_unique_id()
        o_record = Controller.MODEL_LIBRARIANS["models_core.json"].get_record(object_name)
        o_scale = 1
        self.o_ids = [o_id, container_id]
        commands.extend(self.get_add_physics_object(model_name=o_record.name,
                                                    library="models_core.json",
                                                    object_id=o_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.8,
                                                              "z": Containment.O_Z},
                                                    rotation={"x": uniform(0, 360),
                                                              "y": uniform(0, 360),
                                                              "z": uniform(0, 360)},
                                                    default_physics_values=False,
                                                    scale_mass=False,
                                                    mass=uniform(0.1, 0.5),
                                                    dynamic_friction=uniform(0.1, 0.5),
                                                    static_friction=uniform(0.1, 0.5),
                                                    bounciness=uniform(0.5, 0.95),
                                                    scale_factor={"x": o_scale, "y": o_scale, "z": o_scale}))

        return commands

if __name__ == "__main__":
    c = Containment()
    success = c.run(num=5, pass_masks=['_img'] , room='empty', tot_frames=50, add_object_to_scene=True, trial_type='object')
    print(success)