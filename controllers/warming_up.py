# STATUS: V1 Experimental
'''
Readme:
This file is meant to apply something random, but object based, to each of the union of all the objects. 
The goal is to provide a baseline for a neural network to 'warm up' the parameters.
Different scenarios:
- fall from height between 0 and 4, with random rotation between 0 and 360 degrees on all or some axis: axis have 50% chance to be on or off
- Apply force #NOTE like trials, force is biased on bounds extends and scale unit
    - Object looks at a position and gets force in that direction
    - Object gets force from direction on all or some axis: axis have 50% chance to be on or off 
- fall + force
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
from random import uniform
from helpers.helpers import get_magnitude, get_record_with_name

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
        self.camera_pos = {"x": uniform(1.5, 2), "y": uniform(1.5, 2), "z": uniform(-1, 1)}

        super().__init__(port=port)

    def set_force(self, commands=[]):
        '''Apply force to object into random direction'''
        # Get suitable random force
        force = get_magnitude(get_record_with_name(self.objects[0]))

        if random.choice([True, False]):
            # Rotate the object
            commands.append({"$type": "object_look_at_position",
                            "position": {"x": uniform(-10, 10), "y": 0, "z": uniform(-10, 10)},
                            "id": self.o_ids[0]})
            # Apply a force to the object
            commands.append({"$type": "apply_force_magnitude_to_object",
                            "magnitude": force,
                            "id": self.o_ids[0]})

        else:
            # Apply a force to the object
            commands.append({"$type": "apply_force_at_position", 
                                "id": self.o_ids[0], 
                                "force": {"x": force if random.choice([True, False]) else 0,  #NOTE: forces are not different, just like in containment
                                        "y": force if random.choice([True, False]) else 0, 
                                        "z": force if random.choice([True, False]) else 0}, 
                                "position": {"x": random.uniform(-10, 10), 
                                        "y": random.uniform(0, 10), #NOTE: No upwards force, since we do not apply this in the trials yet #TODO: this might be the case after agent trials
                                        "z": random.uniform(-10, 10)}})
        return commands

    
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp' '''
        # Add camera
        self.camera = ThirdPersonCamera(position=self.camera_pos,
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id='frames_temp')
        self.add_ons.append(self.camera)
        
    def trial_initialization_commands(self):
        # Choose between falling or force collision #TODO check if random choice still works
        coll_type = random.choice([['fall'], ['force'], ['fall', 'force']])
        print(coll_type)
        # Always store object ids so the main runner knows which to remove
        self.o_ids = [self.get_unique_id()]
        commands = []

        position = {"x": 0, "z": 0}
        position['y'] = uniform(0, 4) if 'fall' in coll_type else 0

        rotation = {"x": uniform(0, 360) if random.choice([True, False]) else 0, 
                    "y": uniform(0, 360) if random.choice([True, False]) else 0, 
                    "z": uniform(0, 360) if random.choice([True, False]) else 0} if 'fall' in coll_type else {"x": 0, "y": 0, "z": 0}

        # To choose random object without putting back
        commands.extend(self.get_add_physics_object(model_name=self.objects[0],
                                                    library='models_core.json',
                                                    object_id=self.o_ids[0],
                                                    position=position,
                                                    rotation=rotation))
        
        # Remove selected object, so next object won't be the same
        self.objects.remove(self.objects[0])

        # Add force towards random direction or simply let physics do its thing (falling)
        commands = self.set_force(commands) if 'force' in coll_type else commands

        return commands
    
if __name__ == "__main__":
    c = UpWarmer()
    success = c.run(num=97, pass_masks=['_img', '_id'], room='empty', add_object_to_scene=False, tot_frames=150, png=False)
    print(success)