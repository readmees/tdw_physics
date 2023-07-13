# STATUS: V1 - Experimential
'''
Readme:

Possible improvements:
Add rolling down collision
Noise in position could be dependend on width of objects
Random force positions could better
'''
# Added for collisions
from helpers.runner_main import Runner

# To keep track of where the moving objects is
from tdw.output_data import Transforms, OutputData
from tdw.librarian import ModelLibrarian
import numpy as np
import random 
from helpers.objects import *
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from helpers.helpers import get_magnitude, get_record_with_name
from copy import deepcopy
class Collision(Runner):

    def __init__(self, port=1071):
        self.controller_name = 'collision'

        # Concatenate the lists and remove duplicates
        self.objects = list(set(CONTAINERS + OCCLUDERS + OCCLUDERS_SEE_THROUGH + OCCLUDED +
                        ROLLING_FLIPPED + BALLS))
      
        self.camera_pos = {"x": random.uniform(1.5, 2), "y": 0.5, "z": random.uniform(-1, 1)}
        super().__init__(port=port)

    def set_fall_postions(self):
        '''This method implements objects falling on top of each other, 
        by placing one above the other'''
        # Add postions for falling object
        fall_pos = {"x": random.uniform(-1, 1), "y": random.uniform(2, 4), "z": random.uniform(-1, 1)}
        
        # One object should be on the ground, underneath the falling object
        # Add some noise in position
        ground_pos = {'x':fall_pos['x'] + random.uniform(-.1, .1), 'y':0, 'z':fall_pos['z'] + random.uniform(-.1, .1)}

        return [ground_pos, fall_pos]
    
    def set_force_positions(self):
        # Add postions for moving object
        x = random.choice([random.uniform(-5, -2), random.uniform(2, 5)])
        z = random.choice([random.uniform(-5, -2), random.uniform(2, 5)])
        moving_pos = {"x": x, "y": 0, "z": z}
        
        # Add position of the object that will be in the way of the moving object
        coll_pos = {"x": random.uniform(-.5, .5), "y": 0, "z": random.uniform(-.5, .5)}

        return [coll_pos, moving_pos]

    def add_objects(self, commands):
        for i in range(self.num_objects):
            commands.extend(self.get_add_physics_object(model_name=self.objects[i],
                                                        library='models_core.json',
                                                        object_id=self.o_ids[i],
                                                        position=self.positions[i]))
        return commands
    

    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp'
        '''
        # Add camera
        self.camera = ThirdPersonCamera(position={"x": -1, "y": 1.5, "z": -2},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id='frames_temp')
        self.add_ons.append(self.camera)
        
    def trial_initialization_commands(self):
        # Could be extended to multiple objects one day
        self.num_objects = 2

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [self.get_unique_id() for i in range(self.num_objects)]
        coll_id, move_id = self.o_ids

        # Choose between falling or force collision
        coll_type = random.choice(['force', 'force']) #TODO should be fall force

        # Get positions based on collision type
        self.positions = self.set_fall_postions() if coll_type == 'fall' else self.set_force_positions()

        # To choose random object without putting back
        random.shuffle(self.objects)

        commands = self.add_objects(commands=[])
        if coll_type == 'force':
            magnitude = get_magnitude(get_record_with_name(self.objects[1]))*2
            print(magnitude)
            commands.extend([{"$type": "object_look_at",
                    "other_object_id": coll_id,
                    "id": move_id},
                    {"$type": "apply_force_magnitude_to_object",
                    "magnitude": magnitude,
                    "id": move_id}])


        # Get point non-moving object
        cam_turn = deepcopy(self.positions[0])

        # Turn camera up/down, if objects falls down
        cam_turn['y'] = 0 # self.positions[1]['y']/10 if coll_type == 'fall' else 1.5

        # Point camera towards non-moving object and up/down
        self.camera.look_at(cam_turn)

        #TODO 'zoom in' depending on height of object
        # for name in 
        # rec = self.records[name] 

        return commands
    
if __name__ == "__main__":
    c = Collision()
    success = c.run(num=20, pass_masks=['_img'], room='empty', add_object_to_scene=False, tot_frames=150, png=False)
    print(success)