# STATUS: V1 - Experimential
#TODO test new stopping math
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.add_ons.third_person_camera import ThirdPersonCamera

# Added for occlusions
import random
from helpers.runner_main import Runner
from helpers.objects import *

# To keep track of where the moving objects is
from tdw.output_data import Transforms, OutputData
import numpy as np
class Occlusion(Runner):
    def __init__(self, port=1071):
        self.controller_name = 'occlusion'
        #TODO change height depending on height objects
        self.camera_pos = {"x": random.uniform(2, 2.5), "y": .1, "z": random.uniform(-1, 1)}

        # self.records = {record.name:record for record in lib.records}
        self._target_id: int = 0
        super().__init__(port=port)

    def get_two_random_records(self):
        '''This method gets two objects, where 
        occluder is bigger in width and height''' #TODO Choose set of suitable objects
        # Store globals in locals, so we can remove objects temporary
        occluded, occluders = OCCLUDED.copy(), OCCLUDERS.copy()
        
        # Choose a random occluded object
        o_moving_name = random.choice(occluded)

        # Get record of moving object
        rec_moving = self.records[OCCLUDED_DICT[o_moving_name]]

        # Get height and width of moving object #TODO check this formula
        height_moving = abs(rec_moving.bounds['top']['y'] - rec_moving.bounds['bottom']['y'])
        width_moving = abs(rec_moving.bounds['left']['z'] - rec_moving.bounds['right']['z'])
        print('moving', o_moving_name, height_moving, width_moving)

        # Make sure the occluding object covers the other object
        while True:
            # Choose a random occluder object without putting back
            o_occlu_name = random.choice(occluders)
            occluders.remove(o_occlu_name)
            
            # Get record of moving object
            rec_occlu = self.records[OCCLUDERS_DICT[o_occlu_name]]

            # Calculate height and width of occluder #TODO check this formula
            height_occl = abs(rec_occlu.bounds['top']['y'] - rec_occlu.bounds['bottom']['y'])
            width_occl = abs(rec_occlu.bounds['left']['z'] - rec_occlu.bounds['right']['z'])
            print('occlu', o_occlu_name, height_occl, width_occl)

            #NOTE TODO Somehow width is often 0
            if height_occl > height_moving:
                return [rec_moving, rec_occlu]
            
            # If none of records is bigger then moving object
            if not occluders:
                return []
            
    def add_occ_objects(self):
        '''This method adds two objects to the scene, one moving and one occluder'''
        records, commands = [], []

        # There might a occluding object that is bigger then any occluders, in this case try again
        while not records:
            records = self.get_two_random_records()

        for i, record in enumerate(records):
            # Moving object is record[0] & self.o_ids[0] and occluder is record[1] & self.o_ids[1]
            object_id = self.o_ids[0] if i == 0 else self.o_ids[1]
            position = self.o_moving_loc if i == 0 else {"x": 0, "y": 0, "z": self.o_occl_loc_z}
            
            # Set randomized physics values and update the physics info.
            scale = TDWUtils.get_unit_scale(record) * random.uniform(0.89, 1.01)

            # Add object
            commands.extend(self.get_add_physics_object(model_name=record.name,
                                                        library="models_core.json",
                                                        object_id=object_id,
                                                        position=position,
                                                        # rotation={"x": 0, "y": random.uniform(-90, 90), "z": 0},
                                                        default_physics_values=False,
                                                        mass=random.uniform(1, 5),
                                                        scale_mass=False,
                                                        dynamic_friction=random.uniform(0, 0.9),
                                                        static_friction=random.uniform(0, 0.9),
                                                        bounciness=random.uniform(0, 1),
                                                        # scale_factor={"x": scale, "y": scale, "z": scale} #TODO uncomment for random
                                                        ))
        return commands
    
    def calc_stopping_pos(self):
        ''' This function calculates the stopping position of the moving object, 
        so it's in line with the occluder vs camera
        using a**2+b**2=c**2'''
        a_mo_oc = np.abs(self.o_moving_loc['x'])+np.abs(self.camera_pos['x'])
        b_mo_oc = self.o_occl_loc_z+np.abs(self.camera_pos['z']) 

        c_mo_oc = np.sqrt(a_mo_oc**2+b_mo_oc**2)
        c_co = np.sqrt(self.camera_pos['z']**2 + self.camera_pos['x']**2)
        
        c_mo = c_mo_oc-c_co

        a_mo = self.o_moving_loc['x']**2
        b_mo = np.sqrt(a_mo**2-c_mo**2)
        return b_mo
    
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

    def run_per_frame_commands(self, trial_type, tot_frames):
        # Check if transition is done
        transition_compl = False             
        
        # Calculate z distance from occluder
        stop_z = self.calc_stopping_pos()
        stop_z = self.o_occl_loc_z + stop_z if self.camera_pos['z'] < 0 else  self.o_occl_loc_z - stop_z
        stop_z = -self.camera_pos['z']+self.o_occl_loc_z
        print(stop_z)
        # If occluder is on the left of the camera, moving object should stop on the right and vice versa
        if self.camera_pos['z'] > self.o_occl_loc_z:
            stop_z = self.o_occl_loc_z - stop_z
        else:
            print('ELSE')
            stop_z = self.o_occl_loc_z + stop_z


            
        # stop_z = stop_z + self.o_occl_loc_z # if stop_z >= 0 else stop_z - self.o_occl_loc_z
        for i in range(tot_frames):
            # Check if this is object based or transition trial
            if trial_type == 'transition':
                # Start transition when it's behind the object #TODO: adjust for line of camera
                if self.o_moving_loc['z'] > stop_z and self.direction == 'left' or self.o_moving_loc['z'] < stop_z and self.direction == 'right':
                    commands = []
                    if not transition_compl:
                        print('stop_z', stop_z)
                        print('cam', self.camera_pos)
                        print('moving postiion', self.o_moving_loc)
                        print('occluder', self.o_occl_loc_z)


                        # Choose between reverse random speed change, stop, random speed change
                        speed = random.choice([-random.uniform(0.01, 0.3), 0, random.uniform(0.01, 0.3)])                 
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
        self.o_moving_loc = {"x": random.uniform(-4, -2), "y": 0, "z": z}
        
        # Define the z location of occluding object
        self.o_occl_loc_z = random.uniform(-.5, .5)

        # Rotate camera to occluding object
        # #TODO change height depending on height objects
        # self.camera_pos = {"x": random.uniform(2, 3), "y": random.uniform(.2,.3), "z": random.uniform(-1, 1)}
        # self.camera.teleport(position=self.camera_pos)

        self.camera.rotate({"x": 0, "y": 0, "z":self.o_occl_loc_z})


        # Add objects and their ids, first id is moving object, second collider
        self.o_ids = [self.get_unique_id(), self.get_unique_id()]
        moving_o_id = self.o_ids[0]
        commands = self.add_occ_objects()

        # Apply point object towards middle (but behind occluder) #TODO does not account for scale of object
        commands.append({"$type": "object_look_at_position", 
                         "position": {"x": self.o_moving_loc['x'], 
                                      "y": 0, 
                                      "z": 0},
                          "id": moving_o_id})
        
        # Apply force
        commands.append({"$type": "apply_force_magnitude_to_object",
                          "magnitude": random.uniform(30, 60),
                          "id": moving_o_id})
        
        #TODO Make sure objects cannot fly or even bounce  maybe this is not necessary with the right objects
         
        # Keep track of transforms, so we can keep track of the movement
        commands.append({"$type": "send_transforms",
                                  "frequency": "always"})
        return commands
    

if __name__ == "__main__":
    c = Occlusion()
    success = c.run(num=300, pass_masks=['_img', '_id'], room='empty', tot_frames=150, add_slope=False, trial_type='transition', png=False)
    # The following code only works for other masks then _img
    # for i in range(30):
    #     c = Occlusion(port=1000+i)
    #     success = c.run(num=3, pass_masks=['_img', '_id'], room='empty', tot_frames=150, add_slope=False, trial_type='object', png=False)
    print(success)