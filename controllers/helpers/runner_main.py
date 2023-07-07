# STATUS: Passing
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.librarian import SceneLibrarian
import shutil
import random   
import os
from helpers.helpers import images_to_video, message
import time
from tdw.librarian import ModelLibrarian

class Runner(Controller):
    def __init__(self, port=1071):
        # Important to use the models_core, since the index from is based on the helpers.objects
        lib = ModelLibrarian('models_core.json')
        self.records = lib.records
        super().__init__(port=port) 
        
    def trial_initialization_commands(self):
        '''In this function the objects should be added, 
        and initial forces etc. can be applied. Should return commands'''
        return []

    def run_per_frame_commands(self, trial_type, tot_frames):
        '''Communicate once for every frame
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param tot_frames: the total amount of frames per trial
        '''
        for i in range(tot_frames):
                self.communicate([])

        # Reset the scene by destroying the objects
        destroy_commands = []
        for o_id in self.o_ids:
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)
    
    def add_object_to_scene(self, commands = []):
        '''This method should be used to add a fixed object to the scene, since the object will not change 
        during trials and is fixed in place, it will be added to the background shot
        See containment.py and rolling_down.py for examples'''
        return commands
    
    def set_camera(self):
        ''' Here a custom camera can be added. 
        The avatar_id of the camera should be 'frames_temp'
        '''
        # Add camera
        self.camera = ThirdPersonCamera(position=self.camera_pos,
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id='frames_temp')
        self.add_ons.append(self.camera)
    
    def run(self, num=5, trial_type='object', png=False, pass_masks=["_img", "_mask"], framerate = 30, room='random', 
            tot_frames=200, add_object_to_scene=False):
        '''
        param num: the number of trials
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param png: If True, images will be lossless png files. Usually jpg should be enough, but only works for _img
        param pass_masks: segmentation data and much more, see: https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#set_pass_masks
        param framerate: target framerate and fps of video, should be int
        param room: can be any of the specified scene names, 'empty' will create an empty room, 'random_unsafe' pick a random room which is not safe,
                    because not all rooms are tested
        param tot_frames: circa nummer of frames per trials #NOTE this is not the exact number of frames 
        param add_object_to_scene: add objects to the scene (and background), add slope to the background, for rolling down trials
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
        
        #TODO check input for all params
        self.framerate = framerate
        
        # Clear the list of add-ons.
        self.add_ons.clear()

        # Set camera
        self.set_camera()
        controller_name = self.controller_name
        
        # Define path for output data frames
        path_main = '../data_publish'
        paths = [f'{path_main}/{name}/{controller_name}/{trial_type}' for name in ['backgrounds', 'videos']]
        path_backgr, path_videos = paths
        path_frames = f'{path_main}/frames_temp'
        paths.append(path_frames)

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
        self.add_ons.append(ImageCapture(path=path_main+'/', avatar_ids=['frames_temp'], png=png, pass_masks=pass_masks))
        
        # Create room
        lib = SceneLibrarian(library="scenes.json")
        scene_names = [record.name for record in lib.records]
        if room == 'empty':
            commands = [TDWUtils.create_empty_room(12, 12)]
        elif room in scene_names or room == 'random':
            scene_name = random.choice(scene_names) if room == 'random' else room
            print('The name of the selected scene is:', scene_name)
            commands = [self.get_add_scene(scene_name=scene_name)]
        else:
            return message(f"param room should be 'empty', 'random' or any of the following names: \n {scene_names}", 'error')

        # Set target framerate
        commands.append({"$type": "set_target_framerate",
                        "framerate": framerate})
        
        # Add slope to the background, if param add_object_to_scene is true
        if isinstance(add_object_to_scene, bool):
            if add_object_to_scene:
                commands = self.add_object_to_scene(commands)
            self.slope_added = add_object_to_scene
        else:
            return message('Parameter add_object_to_scene should be of type bool', 'error')
        
        # Save scene/background separately
        self.communicate(commands)
        ext = '.png' if png else '.jpg'
        moved = False
        while not moved:
            try:
                shutil.move(f'{path_frames}/img_0000{ext}', f'{path_backgr}/background_{controller_name}{trial_id}{ext}') 
                moved = True
            except FileNotFoundError:
                # Scene is still loading
                print(message("Loading scene is taking a long time", 'warning'))
                time.sleep(5)

                #NOTE: this might create unneccesary extra frames
                self.communicate([])

        # Remove any intial frames that might've been created
        shutil.rmtree(path_frames)
        os.makedirs(path_frames)

        print(f"Video of trial n will be saved at {path_videos}/{trial_type}/{trial_id}_trial_n.mp4")
        for trial_num in range(num):
            # Initialize trial and return errors if something is wrong
            trial_commands = self.trial_initialization_commands()
            if not isinstance(trial_commands, list):
                return trial_commands
            self.communicate(trial_commands)

            self.run_per_frame_commands(trial_type=trial_type, tot_frames=tot_frames)
            
            # Specify the output video file name
            output_video = f"{path_videos}/{trial_id}_trial_{trial_num}"

            # Convert images to videos
            images_to_video(path_frames, output_video, framerate, pass_masks, png)
            shutil.rmtree(path_frames)

            # Show progress
            message(f'Progress trials ({trial_num+1}/{num})', 'success', round((trial_num+1)/num*10))
            
        self.communicate({"$type": "terminate"})

        # Remove temp files
        shutil.rmtree(path_frames)
        
        # Let the user know where the trial videos are stored
        print(f'The random id of this set of trials was {trial_id}')
        return message(f'You can now find trial n for every n at f"{path_videos}/{trial_type}/{trial_id}_trial_n.mp4"', 'success')

if __name__ == "__main__":
    c = Runner()
    c.controller_name = 'test'
    success = c.run(num=1000, pass_masks=['_img'])
    print(success)