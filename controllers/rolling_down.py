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

class Rolling(Controller):
    def __init__(self, transition):
        lib = ModelLibrarian('models_core.json')
        self.records = lib.records
        # self.records = {record.name:record for record in lib.records}
        self._target_id: int = 0
        self.transition = transition

        super().__init__(port=1072)

            
    def add_occ_objects(self, commands, o_id1, o_id2):
        '''This method adds two objects to the scene, one walker and one occluder'''


        record = random.choice(self.records):
        scale = TDWUtils.get_unit_scale(record) * random.uniform(0.8, 1.1)

        # Add object
        commands.extend(self.get_add_physics_object(model_name=record.name,
                                                    library="models_core.json",
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": 0, "z": 0},
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
        commands = [
            # TDWUtils.create_empty_room(12, 12), #TODO uncomment
                    {"$type": "set_target_framerate",
                "framerate": 30}]
        o_id1 = self.get_unique_id()
        o_id2 = self.get_unique_id()

        self.add_slope_and_object(commands, o_id1, o_id2)

        self.communicate(commands)

        # Define standard speed and direction
        speed = random.uniform(0.05, 0.1) if self.direction == 'left' else -random.uniform(0.05, 0.1)

        # Check if transition is done
        transition_compl = False
        print('1', speed)                

        for i in range(200):
            self.o_moving_loc['z'] += speed
            self.communicate([{"$type": "teleport_object", "position": self.o_moving_loc, "id": o_id1}])

            # Check if this is object based or transition trial
            if self.transition:
                # Start transition when it's behind the object #TODO: could be cooler
                if self.o_moving_loc['z'] > self.o_occl_loc_z and speed > 0 or self.o_moving_loc['z'] < self.o_occl_loc_z and speed < 0:
                    if not transition_compl:
                        # Choose between reverse random speed change, stop, random speed change
                        speed = random.choice([-random.uniform(0.01, 0.2), 0, random.uniform(0.01, 0.2), -speed]) 
                        print('2', speed)                
                        transition_compl = True

        self.communicate({"$type": "terminate"})

if __name__ == "__main__":
    c = Rolling(transition=False)
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
        f"{path}rolling_mees_empty_room/"+f"{random.uniform(0.01, 0.2)}.mp4"])