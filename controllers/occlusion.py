# STATUS: V1 - Experimential
'''
Readme:
The scales of the objects are random
The rotation of the objects is random
The height and distance of the camera is random for every trial
The camera is always the same perpendicular z distance from the x axis as the same from the moving object
The occluder is always on the y and z are always 0 for the occluder

Possible improvements:
Use real physics (e.g. mass)
Fix other rooms if needed
Make after-selector: if occluder on edge -> remove, if amount of objects < 2 remove
Use width, not only height, which is already sketchy
Use bounds to fit objects better
Move small objects closer
'''
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict

# Added for occlusions
import random
from helpers.runner_main import Runner
from helpers.objects import *
from helpers.helpers import message, get_two_random_records, get_magnitude, get_record_with_name

# To keep track of where the moving objects is
from tdw.output_data import Transforms, OutputData
from tdw.librarian import ModelLibrarian
import numpy as np

from tdw.object_data.object_static import ObjectStatic
from tdw.tdw_utils import TDWUtils

class Occlusion(Runner):
    def __init__(self, port=1071):
        self.controller_name = 'occlusion'
        lib = ModelLibrarian('models_core.json')
        self.records_dict = {record.name:record for record in lib.records}
        self.camera_pos = {"x": random.uniform(1.5, 2), "y": 0.1, "z": random.uniform(-1, 1)}
        super().__init__(port=port)
            
    def add_occ_objects(self):
        '''This method adds two objects to the scene, one moving and one occluder'''
        records, commands = [], []

        # Random occluded and occluder object, where occluded object is smaller
        records, bounds = get_two_random_records(smaller_list=OCCLUDED, larger_list=OCCLUDERS, axis=[1,2])

        self.names = [record.name for record in records]
        for i, record in enumerate(records):

            # Moving object is record[0] & self.o_ids[0] and occluder is record[1] & self.o_ids[1]
            object_id = self.o_ids[0] if i == 0 else self.o_ids[1]
            position = self.o_moving_loc if i == 0 else {"x": 0, "y": 0, "z": self.o_occl_loc_z}
            
            # Set randomized physics values and update the physics info. #NOTE this is done differently in tdw_physics with TDWUtils.get_unit_scale
            scale = random.uniform(0.9, 1.1)

            rotation_y = random.uniform(-90, 90) if i == 0 else 0
            # Add object
            commands.extend(self.get_add_physics_object(model_name=record.name,
                                                        library="models_core.json",
                                                        object_id=object_id,
                                                        position=position,
                                                        rotation={"x": 0, "y": rotation_y, "z": 0},
                                                        scale_factor={"x": scale, "y": scale, "z": scale},
                                                        default_physics_values=False,
                                                        dynamic_friction=0.9,
                                                        static_friction=0.9,
                                                        mass = 1 # TODO, use real scale
                                                        ))
        return commands, bounds
    
    def set_camera(self):
        # Add camera
        self.camera = ThirdPersonCamera(position=self.camera_pos,
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id='frames_temp')
        self.add_ons.append(self.camera)
    
    def get_ob_pos(self, o_id, resp):
        '''Get object position'''
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            # Parse Transforms output data to get the object's position.
            if r_id == "tran":
                transforms = Transforms(resp[i])
                for j in range(transforms.get_num()):
                    if transforms.get_id(j) == o_id:
                        # Return position of object with o_id as object id
                        return transforms.get_position(j)
        return message(f"{self.names[0]} does not have positions data, with occluder {self.names[1]}", 'error')

    def run_per_frame_commands(self, trial_type, tot_frames):
        # Check if transition is done
        transition_compl = False             
        
        # Calculate z distance between occluder and camera
        stop_moving = np.abs(self.o_occl_loc_z - self.camera_pos['z'])

        # If occluder is on the left of the camera, moving object should stop on the right and vice versa
        if self.camera_pos['z'] > self.o_occl_loc_z:
            # Camera is on the right of occluder, object stops on the left of occluder
            stop_moving = self.o_occl_loc_z - stop_moving
        else:
            # Camera is on the left of occluder, object stops on the right of occluder
            stop_moving = self.o_occl_loc_z + stop_moving

        for i in range(tot_frames):
            # Check if this is object based or transition trial
            if trial_type == 'transition':
                # Start transition when it's behind the object #TODO: adjust for line of camera
                if self.o_moving_loc['z'] > stop_moving and self.direction == 'left' or self.o_moving_loc['z'] < stop_moving and self.direction == 'right':
                    commands = []
                    if not transition_compl:
                        # Choose between reverse random speed change, stop
                        speed = random.choice([random.uniform(0.01, 0.3), 0])
                        speed = speed if self.direction == 'right' else -speed                
                        transition_compl = True

                        # Freeze object, then start 'manual' movement
                        commands.extend([{"$type": "set_rigidbody_constraints", "id": self.o_ids[0], "freeze_position_axes": {"x": 1, "y": 1, "z": 1}, "freeze_rotation_axes": {"x": 1, "y": 1, "z": 1}}])
                    else:
                        commands.extend([{"$type": "set_rigidbody_constraints", "id": self.o_ids[0], "freeze_position_axes": {"x": 0, "y": 0, "z": 0}, "freeze_rotation_axes": {"x": 0, "y": 0, "z": 0}}])

                    # Start 'manual' movement
                    commands.extend([{"$type": "teleport_object_by", "position": {"x": 0, "y": 0, "z": speed}, "id": self.o_ids[0], "absolute": True}])
                    self.communicate(commands)
                else:
                    # Store response and make frame
                    resp = self.communicate([])

                    # Update previous position with current position, only update z position 
                    # #NOTE: I assume here that the output of get_ob_pos is [x, y, z]
                    for axis_name, axis_val in zip(['x', 'y', 'z'], self.get_ob_pos(self.o_ids[0], resp)):
                        if isinstance(axis_val, str):
                            return axis_val
                        self.o_moving_loc[axis_name] = axis_val
                        
            if trial_type == 'object':
                self.communicate([])
        
        # Reset the scene by destroying the objects
        destroy_commands = []
        for o_id in self.o_ids:
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)

    def trial_initialization_commands(self):
        '''
        param path: "Images will be save to here"'''
        # Choose if the object should come from left or right
        self.direction = random.choice(['left', 'right'])

        # Define the location of moving object #TODO bigger variations
        z = random.uniform(-5, -4) if self.direction == 'left' else random.uniform(5, 4)
        self.o_moving_loc = {"x": random.uniform(-2.5, -1), "y": 0, "z": z}
        
        # Define the z location of occluding object
        self.o_occl_loc_z = random.uniform(-.5, .5)

        # Add objects and their ids, first id is moving object, second collider
        self.o_ids = [self.get_unique_id(), self.get_unique_id()]
        moving_o_id = self.o_ids[0]
        commands, bounds = self.add_occ_objects()

        # Teleport camera same distance from occluder as moving object
        #TODO change height depending on height objects
        #TODO check if moving camera creates problems
        self.camera_pos['x'] = -self.o_moving_loc['x']

        # Float somewhere between the ground and occluder height
        self.camera_pos['y'] = random.uniform(0.01, np.mean(bounds[1][1]))
        self.camera.teleport(position=self.camera_pos)

        # Rotate camera to occluding object
        self.camera.rotate({"x": 0, "y": 0, "z":self.o_occl_loc_z})

        # Apply point object towards middle (but behind occluder) #TODO does not account for scale of object
        commands.append({"$type": "object_look_at_position", 
                         "position": {"x": self.o_moving_loc['x'], 
                                      "y": 0, 
                                      "z": 0},
                          "id": moving_o_id})
        
        # Find suitable magnitude for force
        record_moving = get_record_with_name(self.names[0])
        magnitude = get_magnitude(record_moving)
        print(magnitude)
        # Apply force
        commands.append({"$type": "apply_force_magnitude_to_object",
                          "magnitude": magnitude,
                          "id": moving_o_id})
        
        #TODO Make sure objects cannot fly or even bounce  maybe this is not necessary with the right objects
         
        # Keep track of transforms, so we can keep track of the movement
        commands.extend([{"$type": "send_transforms",
                                  "frequency": "always"},
                        {"$type": "send_rigidbodies",
                       "frequency": "always"},
                      {"$type": "send_static_rigidbodies",
                       "frequency": "once"}])
        
        print(self.names)
        return commands
    

if __name__ == "__main__":
    c = Occlusion()
    success = c.run(num=500, pass_masks=['_img', '_mask'], room='empty', tot_frames=160, add_object_to_scene=False, trial_type='transition', png=False)
    # The commented code only works for other masks then _img
    # for i in range(30):
    #     c = Occlusion(port=1000+i)
    #     success = c.run(num=3, pass_masks=['_img', '_id'], room='empty', tot_frames=150, add_object_to_scene=False, trial_type='object', png=False)
    print(success)