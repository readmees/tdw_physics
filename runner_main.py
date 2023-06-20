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

import os

class Collision(Controller):
    
    def collision_fall(self, commands, o_id1, o_id2):
        '''This method implements objects falling on top of each other, 
        by placing one above the other'''
        commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": 3, "z": 0}))
        commands.extend(self.get_add_physics_object(model_name="rh10",
                                                object_id=o_id2,
                                                position={"x": 0, "y": 0, "z": 0}))
        
    def collision_force(self, commands, o_id1, o_id2):
        '''This method implements objects bumping into each other, 
        by placing next to the other, then applying a force towards the other one'''
        commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": 0, "z": 1}))
        commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                object_id=o_id2,
                                                position={"x": 1, "y": 0, "z": 1}))
        commands.extend([{"$type": "object_look_at",
                          "other_object_id": o_id1,
                          "id": o_id2},
                         {"$type": "apply_force_magnitude_to_object",
                          "magnitude": random.uniform(20, 60),
                          "id": o_id2}])
        return commands
    
    def trial(self, png=False):
        '''
        param png: If True, images will be lossless png files.
        '''
        # Clear the list of add-ons.
        self.add_ons.clear()

        # Add camera
        main_cam = "collision"
        camera = ThirdPersonCamera(position={"x": 2, "y": 1.6, "z": -1},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id=main_cam)
        self.add_ons.append(camera)
        
        # Define path for output data frames
        path_main = 'data'
        paths = [f'{path_main}/{name}/{main_cam}' for name in ['frames_temp', 'backgrounds', 'videos']]
        path_frames, path_backgr, path_videos = paths

        # Make sure paths exist
        for path in paths:
            os.makedirs(path, exist_ok=True)

        # Generate random id for this set of trials, and output for user
        trial_id = random.randint(10**16, 10**17-1) 
        print(f'The random id of this set of trials will be {trial_id}')

        # Remove previous frames (if possible)
        try:
            shutil.rmtree(path_frames)
        except FileNotFoundError:
             pass
        
        # Save 'normal' output images/frames_temp for video
        # ["_img", "_id", "_category", "_mask"]
        self.add_ons.append(ImageCapture(path=path_main+'/frames_temp/', avatar_ids=[main_cam], png=True, pass_masks=["_img"]))
        
        # Create room and set target framerate
        commands = [TDWUtils.create_empty_room(12, 12),
                    {"$type": "set_target_framerate",
                    "framerate": 30}]
        self.communicate(commands)


        # Save scene/background separately
        shutil.move(f'{path_frames}/img_0000.png', f'{path_backgr}/background_{main_cam}{trial_id}.png') 
        
        for i in range(5):
            o_ids = [self.get_unique_id() for _ in range(2)]
            commands = [{"$type": "send_rigidbodies",
                                      "frequency": "always"}]
            
            commands = self.collision_force(commands, o_ids[0], o_ids[1])

            self.communicate(commands)
            for i in range(400):
                self.communicate([])

            for o_id in o_ids:
                # Reset the scene by destroying the object.
                self.communicate([{"$type": "destroy_object",
                                "id": o_id},
                                {"$type": "send_rigidbodies",
                                "frequency": "never"}])
                print(f'Object {o_id} deleted')
            
            # Call ffmpeg to make video from frames in frames_temp
            '''NOTE: the %d wildcard in ffmpeg is not safe for extremely large numbers (with 32-bit max 2,147,483,647)
            Furthermore, large numbers like this might lead to potential performance issues or file system limitations.
            The frame number will increase across trials, so 10000 trials of 1000 frames is, will lead to 
            {trial_id}_trial_10000000.mp4. Numbers under 10**9 should be safe,
            this is all according to ChatGPT 20 Jun 2023'''
            
            call(["ffmpeg",
                "-i", f'{path_frames}/'+"*.png",
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                f"{path_videos}/{trial_id}_trial_{i}.mp4"])
            import time
            time.sleep(1)
            # Remove frames for next trial
            shutil.rmtree(path_frames)

        self.communicate({"$type": "terminate"})

        # Let the user know where the trial videos are stored
        print(f'The random id of this set of trials was {trial_id}')
        print(f'You can find trial n at f"{path_videos}/{trial_id}_trial_n.mp4"')


if __name__ == "__main__":
    c = Collision()
    success = c.trial()
    print('succes:', success)