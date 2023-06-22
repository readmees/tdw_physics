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

def collision_fall(commands):
    commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                object_id=o_id1,
                                                position={"x": 0, "y": 3, "z": 0}))
    commands.extend(self.get_add_physics_object(model_name="rh10",
                                            object_id=o_id2,
                                            position={"x": 0, "y": 0, "z": 0}))
    commands.extend([{"$type": "object_look_at_position",
                        "position": {"x": 0, "y": 0.5, "z": 0},
                        "id": o_id1}])


class Collision(Controller):

    def trial(self, path):
        '''
        param path: "Images will be save to here"'''
        # Clear the list of add-ons.
        self.add_ons.clear()

        # Add camera
        camera = ThirdPersonCamera(position={"x": 2, "y": 1.6, "z": -1},
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

        collision_fall(commands, o_id1, o_id2)
        
        
        # For MacOS
        system('open TDW.app')

        self.communicate(commands)
        for i in range(400):
            self.communicate([])

        self.communicate({"$type": "terminate"})

if __name__ == "__main__":
    c = Collision()
    path = 'data/'
    success = c.trial(path)
    print('succes:', success)

    # Change directory.
    # chdir(str(path.joinpath("a").resolve()))

    # Call ffmpeg.
    call(["ffmpeg",
        "-i", f"{path}collision/"+"img_%04d.jpg",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        f"{path}collision/"+"image_only_video.mp4"])