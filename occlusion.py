from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.controller import Controller
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.occlusion_manager import occlusionManager
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

class Occlusion(Controller):
    def __init__(self, transition):
        lib = ModelLibrarian('models_core.json')
        self.records = lib.records
        # self.records = {record.name:record for record in lib.records}
        self._target_id: int = 0
        self.transition = transition
        # Choose if the object should come from left or right
        self.direction = random.choice(['left', 'right'])
        # Define the location of moving object #TODO bigger variations
        z = random.uniform(-5, -4) if self.direction == 'left' else random.uniform(5, 4)
        self.o_moving_loc = {"x": random.uniform(-4, -2), "y": 0, "z": z}
        print(self.o_moving_loc)
        # Define the z location of occluding object
        self.o_occl_loc_z = random.uniform(-.1, .1)

        print(self.o_moving_loc)
        super().__init__(port=1072)

    def get_random_records(self):
        '''This method gets two objects, where 
        occluder is bigger in width and height'''
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
            print(rec_occlu.name)

            # Calculate height and width of occluder #TODO check this formula
            height_occl = abs(rec_occlu.bounds['top']['y'] - rec_occlu.bounds['bottom']['y'])
            width_occl = abs(rec_occlu.bounds['left']['z'] - rec_occlu.bounds['right']['z'])

            if height_occl > height_moving and width_occl>width_moving:
                return [rec_moving, rec_occlu]
            
            # If none of records is bigger then moving object
            if not records:
                return []
            
    def add_occ_objects(self, commands, o_id1, o_id2):
        '''This method adds two objects to the scene, one walker and one occluder'''
        records = []
        while not records:
            records = self.get_random_records()

        for i, record in enumerate(records):
            # Moving object is o_id1 and occluder is o_id2
            object_id = o_id1 if i == 0 else o_id2
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
        

    def trial(self, path):
        '''
        param path: "Images will be save to here"'''
        # Clear the list of add-ons.
        self.add_ons.clear()

        # Add camera
        camera = ThirdPersonCamera(position={"x": 2.5, "y": .5, "z": 0},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id="occlusion")
        self.add_ons.append(camera)
 
        # Remove previous images and videos
        try:
            shutil.rmtree(f'{path}occlusion/')
        except FileNotFoundError:
             pass
        
        # Save output images/frames for video
        self.add_ons.append(ImageCapture(path=path, avatar_ids=["occlusion"]))
        
        # Create room and set target framerate
        commands = [
            # TDWUtils.create_empty_room(12, 12), #TODO uncomment
                    {"$type": "set_target_framerate",
                "framerate": 30}]
        o_id1 = self.get_unique_id()
        o_id2 = self.get_unique_id()

        self.add_occ_objects(commands, o_id1, o_id2)

        self.communicate(commands)
        

        for i in range(200):
            self.communicate([])

        self.communicate({"$type": "terminate"})

if __name__ == "__main__":
    c = Occlusion(transition=False)
    path = 'data/'
    success = c.trial(path)
    print('succes:', success)

    # Change directory.
    # chdir(str(path.joinpath("a").resolve()))

    # Call ffmpeg to make video
    call(["ffmpeg",
        "-i", f"{path}occlusion/"+"img_%04d.jpg",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        f"{path}occlusion_mees_empty_room/"+f"{random.uniform(0.01, 0.2)}.mp4"])