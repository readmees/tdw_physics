from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
import shutil
import random   
import os
from helpers import images_to_video, message

class Runner(Controller):
    def init():
        super().__init__(port=1071) 
        
    def trial_initialization_commands(self):
        '''This method implements objects bumping into each other, 
        by placing next to the other, then applying a force towards the other one'''
        self.o_ids = [self.get_unique_id() for _ in range(2)]
        o_id1, o_id2 = self.o_ids

        commands = [{"$type": "send_rigidbodies",
                                    "frequency": "always"}]
        
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

    def run_per_frame_commands(self, trial_type='object'):
        '''Communicate once for every frame'''
        for i in range(399):
                self.communicate([])

        for o_id in self.o_ids:
            # Reset the scene by destroying the object.
            self.communicate([{"$type": "destroy_object",
                            "id": o_id},
                            {"$type": "send_rigidbodies",
                            "frequency": "never"}])
    
    def run(self, num=5, png=False, pass_masks=["_img", "_mask"]):
        '''
        param png: If True, images will be lossless png files. Usually jpg should be enough, but only works for _img
        parm pass_masks: segmentation data and much more, see: https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#set_pass_masks
        '''
        # Check if input Camera params are valid
        if not isinstance(pass_masks, list):
            return message("pass_masks should be list", 'error')
        if not png and pass_masks != ["_img"]:
            print(message("jpg only implemented for image mask", 'warning'))
        masks_options = ['_albedo', '_flow', '_normals', '_depth_simple', '_depth', '_mask', '_category', '_id', '_img']
        for mask_type in pass_masks:
            if mask_type not in masks_options:
                return message(f'{mask_type} not in {masks_options}', 'error')
        if len(set(pass_masks)) != len(pass_masks):
            return message('pass_mask cannot contain any double masks', 'error')
        
        # Clear the list of add-ons.
        self.add_ons.clear()

        # Add camera
        main_cam = self.controller_name
        camera = ThirdPersonCamera(position={"x": 2, "y": 1.6, "z": -1},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id=main_cam)
        self.add_ons.append(camera)
        
        # Define path for output data frames
        path_main = '../data'
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
        self.add_ons.append(ImageCapture(path=path_main+'/frames_temp/', avatar_ids=[main_cam], png=png, pass_masks=pass_masks))
        
        # Create room and set target framerate
        framerate = 30
        commands = [TDWUtils.create_empty_room(12, 12),
                    {"$type": "set_target_framerate",
                    "framerate": framerate}]
        self.communicate(commands)

        # Save scene/background separately
        ext = '.png' if png else '.jpg'
        shutil.move(f'{path_frames}/img_0000{ext}', f'{path_backgr}/background_{main_cam}{trial_id}{ext}') 
        
        print(f"Video of trial n will be saved at {path_videos}/{trial_id}_trial_n.mp4")

        for trial_num in range(num):
            self.communicate(self.trial_initialization_commands())
            self.run_per_frame_commands(trial_type='object')
            
            # Specify the output video file name
            output_video = f"{path_videos}/{trial_id}_trial_{trial_num}"

            # Convert images to video
            images_to_video(path_frames, output_video, framerate, pass_masks, png)
            shutil.rmtree(path_frames)

            # Show progress
            message(f'Progress trials ({trial_num+1}/{num})', 'success', round((trial_num+1)/num*10))
            
        self.communicate({"$type": "terminate"})

        # Let the user know where the trial videos are stored
        print(f'The random id of this set of trials was {trial_id}')
        return message(f'You can now find trial n for every n at f"{path_videos}/{trial_id}_trial_n.mp4"', 'success')

if __name__ == "__main__":
    c = Collision(run_class=Runner)
    c.controller_name = 'test'
    success = c.run(num=1000, pass_masks=['_img'])
    print(success)