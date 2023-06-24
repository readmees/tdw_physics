# STATUS: V1 - Experimential
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
from helpers import ObjectInfo, get_random_avatar_position
from runner_main import Runner

class Occlusion(Runner):
    def __init__(self):
        self.controller_name = 'occlusion'
        lib = ModelLibrarian('models_core.json')
        self.records = lib.records

        # self.records = {record.name:record for record in lib.records}
        self._target_id: int = 0
        super().__init__(port=1072)

    def get_two_random_records(self):
        '''This method gets two objects, where 
        occluder is bigger in width and height''' #TODO Choose set of suitable objects
         # Choose a random object without putting back
        records = self.records
        rec_moving = random.choice(records)
        records.remove(rec_moving)

        # Get height and width of moving object #TODO check this formula
        height_moving = abs(rec_moving.bounds['top']['y'] - rec_moving.bounds['bottom']['y'])
        width_moving = abs(rec_moving.bounds['left']['z'] - rec_moving.bounds['right']['z'])

        # Make sure the occluding object covers the other object
        while True:
            rec_occlu = random.choice(records)
            records.remove(rec_occlu)

            # Calculate height and width of occluder #TODO check this formula
            height_occl = abs(rec_occlu.bounds['top']['y'] - rec_occlu.bounds['bottom']['y'])
            width_occl = abs(rec_occlu.bounds['left']['z'] - rec_occlu.bounds['right']['z'])

            if height_occl > height_moving and width_occl>width_moving:
                return [rec_moving, rec_occlu]
            
            # If none of records is bigger then moving object
            if not records:
                return []
            
    def add_occ_objects(self):
        '''This method adds two objects to the scene, one moving and one occluder'''
        records, commands = [], []
        while not records:
            records = self.get_two_random_records()

        for i, record in enumerate(records):
            # Moving object is record[0] & self.o_ids[0] and occluder is record[1] & self.o_ids[1]
            object_id = self.o_ids[0] if i == 0 else self.o_ids[1]
            position = self.o_moving_loc if i == 0 else {"x": 0, "y": 0, "z": self.o_occl_loc_z}
            
            # Set randomized physics values and update the physics info.
            scale = TDWUtils.get_unit_scale(record) * random.uniform(0.8, 1.1)

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
                                                        scale_factor={"x": scale, "y": scale, "z": scale}))
        return commands
    
    def set_camera(self):
        # Add camera
        camera = ThirdPersonCamera(position={"x": 2.5, "y": .5, "z": 0},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id="occlusion")
        self.add_ons.append(camera)

    def run_per_frame_commands(self, trial_type, tot_frames):
        # Define standard speed and direction
        speed = random.uniform(0.05, 0.1) if self.direction == 'left' else -random.uniform(0.05, 0.1)

        # Check if transition is done
        transition_compl = False             

        for i in range(200):
            self.o_moving_loc['z'] += speed
            self.communicate([{"$type": "teleport_object", "position": self.o_moving_loc, "id": self.o_ids[0]}])

            # Check if this is object based or transition trial
            if trial_type == 'transition':
                # Start transition when it's behind the object #TODO: adjust for line of camera
                if self.o_moving_loc['z'] > self.o_occl_loc_z and speed > 0 or self.o_moving_loc['z'] < self.o_occl_loc_z and speed < 0:
                    if not transition_compl:
                        # Choose between reverse random speed change, stop, random speed change
                        speed = random.choice([-random.uniform(0.01, 0.2), 0, random.uniform(0.01, 0.2), -speed])                 
                        transition_compl = True
        
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
        self.o_occl_loc_z = random.uniform(-.1, .1)

        # Add objects and their ids, first id is moving object, second collider
        self.o_ids = [self.get_unique_id(), self.get_unique_id()]
        
        return self.add_occ_objects()

if __name__ == "__main__":
    c = Occlusion()
    success = c.run(num=5, pass_masks=['_img', '_id'], room='empty', tot_frames=150, add_slope=False, trial_type='transition')
    print(success)