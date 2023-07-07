# STATUS: V1 Experimental
'''
Readme:
This file is meant to apply something random, but an object based trial to each of the union of all the objects. 
The goal is to provide a baseline for a neural network to 'warm up' the parameters.

Possible improvements:

'''
from helpers.runner_main import Runner

# To keep track of where the moving objects is
from tdw.output_data import Transforms, OutputData
from tdw.librarian import ModelLibrarian
import numpy as np
import random 
from helpers.objects import *
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from copy import deepcopy

class UpWarmer(Runner):
    def __init__(self, port=1071):
        self.controller_name = 'warming_up'
        lib = ModelLibrarian('models_core.json')
        self.records = {record.name:record for record in lib.records}

        # Concatenate the ALL lists
        self.objects = CONTAINERS + CONTAINED + OCCLUDERS + OCCLUDERS_SEE_THROUGH + OCCLUDED +\
                        ROLLING_FLIPPED + BALLS

        # Remove duplicates, while preserving order
        # See https://stackoverflow.com/questions/480214/how-do-i-remove-duplicates-from-a-list-while-preserving-order
        self.objects = list(dict.fromkeys(self.objects))
        print(self.objects)
        self.camera_pos = {"x": random.uniform(1.5, 2), "y": random.uniform(1.5, 2), "z": random.uniform(-1, 1)}

        super().__init__(port=port)

    def set_force(self, commands=[]):
        '''Apply force to object into random direction'''
        # Rotate the object
        commands.append({"$type": "object_look_at_position",
                         "position": {"x": random.uniform(-10, 10), "y": 0, "z": random.uniform(-10, 10)},
                         "id": self.o_ids[0]})
        # Apply a force to the object
        commands.append({"$type": "apply_force_magnitude_to_object",
                         "magnitude": random.uniform(1, 100),
                         "id": self.o_ids[0]})

        return commands
    
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp' '''
        # Add camera
        self.camera = ThirdPersonCamera(position=self.camera_pos,
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id='frames_temp')
        self.add_ons.append(self.camera)
        
    def trial_initialization_commands(self):
        # Choose between falling or force collision
        coll_type = random.choice(['fall', 'force'])
        print(coll_type)
        # Always store object ids so the main runner knows which to remove
        self.o_ids = [self.get_unique_id()]
        commands = []

        position = {"x": 0, "z": 0}
        position['y'] = random.uniform(0, 4) if coll_type == 'fall' else 0
        # To choose random object without putting back
        commands.extend(self.get_add_physics_object(model_name=self.objects[0],
                                                    library='models_core.json',
                                                    object_id=self.o_ids[0],
                                                    position=position))
        
        # Remove selected object, so next object won't be the same
        self.objects.remove(self.objects[0])

        # Add force towards random direction or simply let physics do its thing (falling)
        commands = self.set_force(commands) if coll_type == 'force' else commands

        return commands
    
if __name__ == "__main__":
    c = UpWarmer()
    success = c.run(num=160, pass_masks=['_img', '_id'], room='empty', add_object_to_scene=False, tot_frames=150, png=False)
    print(success)