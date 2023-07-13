# STATUS: V1 - Experimential
'''
Readme:
Objects move mostly in z and y position

Possible improvements:
add other objects then cube
Always make two versions of the exact same trial, object and transition?
Use collision manager to see when transition needs to happen?
'''
from tdw.add_ons.third_person_camera import ThirdPersonCamera
import random

# Added for Slopes
import random
import numpy as np

from helpers.runner_main import Runner
from helpers.objects import ROLLING_FLIPPED
from helpers.helpers import get_magnitude, message, get_record_with_name


class Slope(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        self.controller_name = 'rolling_down'
        
        # Uses models_core.json
        self.objects = ["apple",
                        "golf",
                    "orange"]
        self.objects.extend(ROLLING_FLIPPED)
        
    def run_per_frame_commands(self, trial_type, tot_frames):
        '''Communicate once for every frame
        param trial_type: you can choose if you would like to run an trial object, agent or transition based
        param tot_frames: the total amount of frames per trial
        '''
        #TODO: improve transition
        transition_frame = random.choice(list(range(tot_frames//2, tot_frames)))
        for i in range(tot_frames):
            if i >= transition_frame and trial_type == 'transition':
                print('transition, started')
                self.communicate([{"$type": "teleport_object_by", "position": {"x": -.05, "y": 0.0, "z": 0}, "id": self.o_ids[0], "absolute": True}])
            else:
                self.communicate([])

        destroy_commands = []
        for o_id in self.o_ids:
            # Reset the scene by destroying the object.
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)

    def add_object_to_scene(self, commands = []):
        '''This method adds a slope for the rolling down trials, by adding a freezed cube object and a wall to bounce too
        since the object will not change during trials and is fixed in place, it will be added to the background shot'''
        ids = [self.get_unique_id(), self.get_unique_id()]
        slope_id = ids[0]
        wall_id = ids[1]

        # Add slope
        commands.extend(self.get_add_physics_object(model_name="cube",
                                                    library="models_flex.json",
                                                    object_id=slope_id,
                                                    rotation={"x": 0, "y": 0, "z": random.uniform(216, 244)},
                                                    position={"x": -.5, "y": 0, "z": 0},
                                                    scale_factor = {"x": .8, "y": .8, "z": .9},
                                                    dynamic_friction = 0, 
                                                    static_friction = 0))
        # Add wall
        commands.extend(self.get_add_physics_object(model_name="cube",
                                                    library="models_flex.json",
                                                    object_id=wall_id,
                                                    position={"x": .5, "y": 0, "z": 0},
                                                    rotation={"x": 0, "y": 180, "z": 0},
                                                    scale_factor={"x": .1, "y": .25, "z": .9},
                                                    bounciness=1
                                                    ))
        
        # # Make slope very 'slippery' #NOTE this shouldn't do anything, because we already set it in add_physics_object, but it does?
        commands.append({"$type": "set_physic_material", "dynamic_friction": 0, "static_friction": 0, "id": slope_id})
        
        # # Make wall very bouncy #NOTE this shouldn't do anything, because we already set it in add_physics_object, but it does?
        commands.append({"$type": "set_physic_material", "bounciness": 1, "id": wall_id})

        for object_id in ids:
            # Freeze position and rotation for each axis
            commands.extend([{"$type": "set_rigidbody_constraints", "id": object_id, "freeze_position_axes": {"x": 1, "y": 1, "z": 1}, "freeze_rotation_axes": {"x": 1, "y": 1, "z": 1}}])
            # Set a random color.
            commands.append({"$type": "set_color",
                            "color": {"r": random.random(), "g": random.random(), "b": random.random(), "a": 1.0},
                            "id": object_id})
        return commands
    
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp'
        '''
        # Add camera
        camera = ThirdPersonCamera(position={"x": 0, "y": 1.2, "z": -1},
                           look_at={"x": 0, "y": 0, "z": 0},
                           avatar_id='frames_temp')
        self.add_ons.append(camera)

    def trial_initialization_commands(self):
        if not self.slope_added:
            return message('Rolling down trials should have slope', 'error')
        
        
        
        o_id1 = self.get_unique_id()
        o_id2 = self.get_unique_id()

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [o_id1]

        commands = []

        object_choice = random.choice(self.objects)

        # Flip object if needed to roll, e.g. cola can
        rotation_x = 0 if object_choice not in ROLLING_FLIPPED else random.choice([90, -90])
        
        # Get position for falling object
        position = {"x": random.uniform(-.15,-.1), "y": random.uniform(4, 5), "z": random.uniform(-.15,.15)}

        # Add object
        commands.extend(self.get_add_physics_object(model_name=object_choice,
                                                    library='models_core.json',
                                                    object_id=o_id1,
                                                    position=position,
                                                    rotation={"x": rotation_x, "y": 0, "z": 0}))
        
        print(object_choice)
        # Get suitable random force magnitude
        force = get_magnitude(get_record_with_name(object_choice))*.25
        return commands
    
if __name__ == "__main__":
    c = Slope()
    success = c.run(num=5, pass_masks=['_img', '_id'], room='empty', tot_frames=250, add_object_to_scene=True, trial_type='transition')
    print(success)