# STATUS: V1 - Experimential
'''
Readme:
Example usage: python object_test.py --pass_masks _img,_mask
The goal of this file is to test which objects create bugs and which objects are fine

Possible improvements:
This file is extremely messy, since it's just made to show the objects quickly for the developers
Zoom in and out with smaller objects
'''
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from tdw.add_ons.image_capture import ImageCapture
from tdw.librarian import SceneLibrarian
import shutil
import random   
import os
from helpers.helpers import message, create_arg_parser
import time
from tdw.librarian import ModelLibrarian


class Object_tester(Controller):
    def __init__(self):
        lib = ModelLibrarian('models_core.json')
        self.names = [record.name for record in lib.records]
        self.records = {record.name:i for i, record in enumerate(lib.records)}
        self.index = 129
        self.controller_name = 'object_shower'
        super().__init__(port=1071) 

    def run_per_frame_commands(self, trial_type, tot_frames):
        '''Communicate once for every frame
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param tot_frames: the total amount of frames per trial
        '''
        for i in range(tot_frames):
                self.communicate([])

        # Reset the scene by destroying the objects
        destroy_commands = []
        # self.o_ids.append(self.slope_id)
        for o_id in [self.slope_id]:
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)
        return None
    
    def set_camera(self):
        # Add camera
        position, look_at = {"x": 2, "y": 1.6, "z": -1}, {"x": 0, "y": 0, "z": 0}
        camera = ThirdPersonCamera(position=position,
                           look_at=look_at,
                           avatar_id=self.controller_name)
        self.add_ons.append(camera)
        return position, look_at
    
    def run(self, num=5, png=False, pass_masks=["_img", "_mask"], framerate = 30, room='random'):
        '''
        param num: the number of trials
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param png: If True, images will be lossless png files. Usually jpg should be enough, but only works for _img
        param pass_masks: segmentation data and much more, see: https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#set_pass_masks
        param framerate: target framerate and fps of video, should be int
        param room: can be any of the specified scene names, 'empty' will create an empty room, 'random_unsafe' pick a random room which is not safe,
                    because not all rooms are tested
        param tot_frames: nummer of frames per trials
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
        main_cam = self.controller_name
        
        # Define path for output data frames
        path_main = '../data'
        paths = [f'{path_main}/{name}/{main_cam}' for name in ['frames_temp', 'objects_screenshot', 'videos']]
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
            return message(f"param room should be 'empty', 'random' or any of the following names: \n {scene_names}", 'error')

        # Set target framerate
        commands.append({"$type": "set_target_framerate",
                        "framerate": framerate})
        slope_id = 1
        for trial_num in range(num):
            # Show the object
            commands.extend(self.get_add_physics_object(model_name=self.names[self.index],
                                                    library="models_core.json",
                                                    object_id=slope_id,
                                                    rotation={"x": 0, "y": 0, "z": 0},
                                                    position={"x": 0, "y": 0, "z": 0}))
            
            # Save screenshot of the object
            self.communicate(commands)
            ext = '.png' if png else '.jpg'
            moved = False
            while not moved:
                try:
                    first_frame = os.listdir(f'{path_frames}')[0]
                    if '.' in self.names[self.index]:
                        return message('name cannot contain a dot for later evalutation',  'error')
                    shutil.move(f'{path_frames}/{first_frame}', f'{path_backgr}/{self.index}.{self.names[self.index]}{ext}') 
                    moved = True
                except FileNotFoundError:
                    # Scene is still loading
                    print(message("Loading scene is taking a long time", 'warning'))
                    time.sleep(5)

                    #NOTE: this might create unneccesary extra frames
                    self.communicate([])
            destroy_commands = []
            destroy_commands.append({"$type": "destroy_object",
                            "id": slope_id})
            destroy_commands.append({"$type": "send_rigidbodies",
                                "frequency": "never"})  
            self.communicate(destroy_commands)
            print(f'{self.names[self.index]}:', self.index)

            # Remove frames (this controlller is not here to make videos)
            shutil.rmtree(path_frames)

            # Next object
            self.index +=1 
            commands = []
        self.communicate({"$type": "terminate"})

        # Let the user know where the trial videos are stored
        return message(f'You can now find trial n for every n at f"{path_videos}/{trial_id}_trial_n.mp4"', 'success')
    
    
if __name__ == "__main__":
    c = Object_tester()
    
    # Retrieve the right arguments
    args = create_arg_parser()
    print(message('add_object_to_scene is set to False and tot_frames to 200', 'warning'))
    success = c.run(num=args.num, pass_masks=args.pass_masks, room=args.room, framerate=args.framerate, png=args.png)
    print(success)