# STATUS: Passing
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.librarian import SceneLibrarian
import shutil
import random   
import os
from helpers import images_to_video, message

class Runner(Controller):
    def init():
        super().__init__(port=1071) 
        
    def trial_initialization_commands(self):
        '''In this function the objects should be added, 
        and initial forces etc. can be applied. Should return commands'''
        return []

    def run_per_frame_commands(self, trial_type='object'):
        '''Communicate once for every frame
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        '''
        for i in range(20):
                self.communicate([])

        for o_id in self.o_ids:
            # Reset the scene by destroying the object.
            self.communicate([{"$type": "destroy_object",
                            "id": o_id},
                            {"$type": "send_rigidbodies",
                            "frequency": "never"}])
    
    def set_camera(self):
        # Add camera
        camera = ThirdPersonCamera(position={"x": 2, "y": 1.6, "z": -1},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id=self.controller_name)
        self.add_ons.append(camera)
    
    def run(self, num=5, trial_type='object', png=False, pass_masks=["_img", "_mask"], framerate = 30, room='random'):
        '''
        param num: the number of trials
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param png: If True, images will be lossless png files. Usually jpg should be enough, but only works for _img
        param pass_masks: segmentation data and much more, see: https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#set_pass_masks
        param framerate: target framerate and fps of video, should be int
        param room: can be any of the specified scene names, 'empty' will create an empty room, 'random_unsafe' pick a random room which is not safe,
                    because not all rooms are tested
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

        # Set camera
        self.set_camera()
        main_cam = self.controller_name
        
        # Define path for output data frames
        path_main = '../data'
        paths = [f'{path_main}/{name}/{main_cam}' for name in ['frames_temp', 'backgrounds', 'videos']]
        path_frames, path_backgr, path_videos = paths

        # Remove previous frames (if possible) 
        #NOTE: could be more efficient, because frames folder gets recreated
        try:
            shutil.rmtree(path_frames)
        except FileNotFoundError:
             pass
        
        # Make sure paths exist
        for path in paths:
            os.makedirs(path, exist_ok=True)

        # Generate random id for this set of trials, and output for user
        #NOTE: in theory two trials could have the same random id 
        trial_id = random.randint(10**16, 10**17-1) 
        print(f'The random id of this set of trials will be {trial_id}')
        
        # Save 'normal' output images/frames_temp for video
        self.add_ons.append(ImageCapture(path=path_main+'/frames_temp/', avatar_ids=[main_cam], png=png, pass_masks=pass_masks))
        
        # Create room
        lib = SceneLibrarian(library="scenes.json")
        scene_names = [record.name for record in lib.records]
        if room == 'empty':
            commands = [TDWUtils.create_empty_room(12, 12)]
        elif room in scene_names or room == 'random':
            scene_name = random.choice(scene_names) if room == 'random' else room
            print('scene_name=', scene_name)
            commands = [self.get_add_scene(scene_name=scene_name)]
        else:
            return message(f"param room should be 'empty', 'random' or any of the following names: \n {scene_names}")

        # Set target framerate
        commands.append({"$type": "set_target_framerate",
                        "framerate": framerate})
        self.communicate(commands)
        import time
        
        # Save scene/background separately
        ext = '.png' if png else '.jpg'
        moved = False
        while not moved:
            try:
                shutil.move(f'{path_frames}/img_0000{ext}', f'{path_backgr}/background_{main_cam}{trial_id}{ext}') 
                moved = True
            except FileNotFoundError:
                # Scene is still loading
                print(message("Loading scene is taking a long time", 'warning'))
                time.sleep(5)

                #NOTE: this might create unneccesary extra frames
                self.communicate([])
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
    c = Runner()
    c.controller_name = 'test'
    success = c.run(num=1000, pass_masks=['_img'])
    print(success)