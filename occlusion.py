from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.controller import Controller
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.collision_manager import CollisionManager
from tdw.add_ons.object_manager import ObjectManager

# Added for video
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from os import chdir, system
from subprocess import call
import shutil

# Added for collisions
import random


# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers import ObjectInfo, get_random_avatar_position



class Occlusion(Controller):
    def __init__(self):
        lib = ModelLibrarian('models_core.json')
        self.records = lib.records
        # self.records = {record.name:record for record in lib.records}
        self._target_id: int = 0

        # Define the location of moving object #TODO bigger variations
        self.o_moving_loc = {"x": random.uniform(-4, -2), "y": 0, "z": random.uniform(-6, -4)}
        print(self.o_moving_loc)
        # Define the z location of occluding object
        self.o_occl_loc_z = random.uniform(-.4, .4)

        print(self.o_moving_loc)
        super().__init__(port=1071)

    def occlusion_walk(self, commands, o_id1, o_id2):
        '''This method implements objects falling on top of each other, 
        by placing one above the other'''

        
        commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                    object_id=o_id1,
                                                    position=self.o_moving_loc))
        commands.extend(self.get_add_physics_object(model_name="rh10",
                                                object_id=o_id2,
                                                position={"x": 0, "y": 0, "z": self.o_occl_loc_z}))
        
    def trial(self, path):
        '''
        param path: "Images will be save to here"'''
        # Clear the list of add-ons.
        self.add_ons.clear()

        # Add camera
        camera = ThirdPersonCamera(position={"x": 3, "y": .5, "z": 0},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id="collision")
        self.add_ons.append(camera)
 
        # Remove previous images and videos
        try:
            shutil.rmtree(f'{path}collision/')
        except FileNotFoundError:
             pass
        
        # Save output images/frames for video
        self.add_ons.append(ImageCapture(path=path, avatar_ids=["collision"]))
        
        # Create room and set target framerate
        commands = [TDWUtils.create_empty_room(12, 12),
                    {"$type": "set_target_framerate",
                "framerate": 30}]
        o_id1 = self.get_unique_id()
        o_id2 = self.get_unique_id()

        self.occlusion_walk(commands, o_id1, o_id2)

        self.communicate(commands)
        for i in range(200):
            self.communicate([{"$type": "teleport_object_by", "position": {"x": 0, "y": 0.0, "z": 0.05}, "id": o_id1}])

        self.communicate({"$type": "terminate"})

if __name__ == "__main__":
    c = Occlusion()
    path = 'data/'
    success = c.trial(path)
    print('succes:', success)

    # Change directory.
    # chdir(str(path.joinpath("a").resolve()))

    # Call ffmpeg to make video
    call(["ffmpeg",
        "-i", f"{path}collision/"+"img_%04d.jpg",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        f"{path}collision/"+"image_only_video.mp4"])