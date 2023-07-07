# STATUS: V1 - Experimential
'''
Readme:

Possible improvements:
Add rolling down collision
Noise in possition could be dependend on width of objects
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
from copy import deepcopy
class Collision(Runner):

    def __init__(self, port=1071):
        self.controller_name = 'collision'
        lib = ModelLibrarian('models_core.json')
        self.records = {record.name:record for record in lib.records}

        # Concatenate the lists and remove duplicates
        self.objects = list(set(CONTAINERS + OCCLUDERS + OCCLUDERS_SEE_THROUGH + OCCLUDED +
                        ROLLING_FLIPPED + BALLS))
      
        self.camera_pos = {"x": random.uniform(1.5, 2), "y": 0, "z": random.uniform(-1, 1)}



        super().__init__(port=port)

    def set_fall_postions(self):
        '''This method implements objects falling on top of each other, 
        by placing one above the other'''
        # Add postions for falling object
        fall_pos = {"x": random.uniform(-5, 5), "y": random.uniform(2, 4), "z": random.uniform(-5, 5)}
        
        # One object should be on the ground, underneath the falling object
        # Add some noise in position
        ground_pos = {'x':fall_pos['x'] + random.uniform(0, .2), 'y':0, 'z':fall_pos['z'] + random.uniform(0, .2)}

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
        o_id1, o_id2 = self.o_ids

        # Choose between falling or force collision
        coll_type = random.choice(['fall', 'force'])

        # Get positions based on collision type
        self.positions = self.set_fall_postions() if coll_type == 'fall' else self.set_force_positions()

        # To choose random object without putting back
        self.objects = random.shuffle(self.objects)

        commands = self.add_objects(commands=[])
        if coll_type == 'force':
            commands.extend([{"$type": "object_look_at",
                    "other_object_id": o_id2,
                    "id": o_id1},
                    {"$type": "apply_force_magnitude_to_object",
                    "magnitude": random.uniform(20, 70),
                    "id": o_id1}])

        print(coll_type)

        # Get point non-moving object
        cam_turn = deepcopy(self.positions[0])

        # Turn camera up/down, if objects falls down
        cam_turn['y'] = 0 # self.positions[1]['y']/10 if coll_type == 'fall' else 1.5

        # Rotate camera to occluding object
        # self.camera_pos = {"x": random.uniform(-2, 2), "y": 0.1, "z": random.uniform(-2, 1)}
    
        # Point camera towards non-moving object and up/down
        self.camera.look_at(cam_turn)

        # # 'zoom in' depending on height of object
        # for name in 
        # rec = self.records[name] 

        # # Calculate height and width of occluder #TODO check this formula
        # height_occl = abs(rec_occlu.bounds['top']['y'] - rec_occlu.bounds['bottom']['y'])
        
        return commands
    
if __name__ == "__main__":
    c = Collision()
    success = c.run(num=20, pass_masks=['_img', '_id'], room='empty', add_object_to_scene=False, tot_frames=150, png=False)
    print(success)