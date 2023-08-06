# STATUS: V3.1 - Object, Transition and Agent implemented 
'''
Readme:
Example usage: python rolling_down.py --pass_masks _img,_mask   

Objects move mostly in z and y position
NOTE: stopping is not the same as in occlusion trial and could be perfected

Possible improvements:
add other objects then cube
Always make two versions of the exact same trial, object and transition?
'''
from tdw.add_ons.third_person_camera import ThirdPersonCamera

# Added for Slopes
import random

from helpers.runner_main import Runner
from helpers.objects import ROLLING_FLIPPED
from helpers.helpers import *

import shutil
import os

class Slope(Runner):
    def __init__(self):
        super().__init__(port=1071) 
        #NOTE do not change
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
        transition_frames = None if trial_type == 'object' else []
        transition_activated = False
        moving_o_id, wall_id = self.o_ids[0], self.scene_o_ids[1]
        print(self.object_choice)

        # Agent speed
        speed = .06
        first_resp = False
        agent_success = False

        # Get suitable, yet random force
        force = get_magnitude(get_record_with_name(self.object_choice))
        
        trial_success = True
        for i in range(tot_frames):
            try:
                if i >= 1 and trial_type == 'transition':
                    # self.o_ids[0] is agent, self.scene_o_ids[1]was
                    if get_distance(resp, moving_o_id, wall_id) < .25 and not transition_activated:
                        print('transition')
                        resp = self.communicate([{"$type": "add_constant_force", "id": self.o_ids[0], "force": {"x": -force, "y": 0, "z": 0}, "relative_force": {"x": 0, "y": 0, "z": 0}, "torque": {"x": 0, "y": 0, "z": 0}, "relative_torque": {"x": 0, "y": 0, "z": 0}}])
                        transition_activated = True
                        transition_frames.append(i)
                    else:
                        resp = self.communicate([])
                elif trial_type == 'agent':
                    if not first_resp:
                        resp = self.communicate([{"$type": "object_look_at", "other_object_id": self.o_ids[1], "id": self.o_ids[0]},
                                                {"$type": "teleport_object_by", "position": {"x": 0, "y": 0, "z": speed}, "id": self.o_ids[0], "absolute": False}])
                        first_resp = True
                        transition_frames.append(i)
                    elif get_distance(resp, self.o_ids[0], self.o_ids[1]) <.1 or agent_success:
                        resp = self.communicate([])
                        agent_success = True
                    else:
                        resp = self.communicate([{"$type": "object_look_at", "other_object_id": self.o_ids[1], "id": self.o_ids[0]},
                                                {"$type": "teleport_object_by", "position": {"x": 0, "y": 0, "z": speed}, "id": self.o_ids[0], "absolute": False}])
                        transition_frames.append(i)
                else:
                    resp = self.communicate([])
            except TypeError:
                #NOTE Somehow it seems important to communicate one more time anyways, otherwise the objects do not get removed properly
                resp = self.communicate([])
                # Sometimes we get TypeError: 'NoneType' object is not iterable, when trying to get the transforms
                trial_success = False
                break

        destroy_commands = []
        for o_id in self.o_ids:
            # Reset the scene by destroying the object.
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)

        if not trial_success:
            return 'Fail', trial_success
        return transition_frames if transition_frames != [] else -1, True


    def add_target(self, commands):
        # self.o_ids = [agent_id, occ_id, target_id]
        target_id = self.o_ids[1]

        # Put target on same position as agent 
        # But moved in the z position, so it is in front
        position = self.o_loc

        # Ball doesn't have to roll too much
        position['y'] = random.uniform(1.4,1.5)

        # Drop target slightly on the left of slope max, so agent on the right will have to go uphil
        position['x'] =  random.uniform(-.45,-.35)
        
        commands, self.target_rec = add_target_commands(target_id, position, commands)
        return commands
    
    def add_object_to_scene(self, commands = []):
        '''This method adds a slope for the rolling down trials, by adding a freezed cube object and a wall to bounce too
        since the object will not change during trials and is fixed in place, it will be added to the background shot'''
        ids = [self.get_unique_id(), self.get_unique_id()]
        self.scene_o_ids = ids
        slope_id = ids[0]
        wall_id = ids[1]


        rotation = {"x": 0, "y": 0}
        rotation["z"] = random.uniform(216, 244) if self.trial_type != 'agent' else 244

        # Add slope
        commands.extend(self.get_add_physics_object(model_name="cube",
                                                    library="models_flex.json",
                                                    object_id=slope_id,
                                                    rotation=rotation,
                                                    position={"x": -.5, "y": 0, "z": 0},
                                                    scale_factor = {"x": .8, "y": .8, "z": .9},
                                                    dynamic_friction = 0, 
                                                    static_friction = 0))
        
        if self.trial_type != 'agent':
            # Add wall to make transition and object based trials more similar
            commands.extend(self.get_add_physics_object(model_name="cube",
                                                        library="models_flex.json",
                                                        object_id=wall_id,
                                                        position={"x": .5, "y": 0, "z": 0},
                                                        rotation={"x": 0, "y": 180, "z": 0},
                                                        scale_factor={"x": .1, "y": .25, "z": .9},
                                                        bounciness=1
                                                        ))
            # Make wall very bouncy #NOTE this shouldn't do anything, because we already set it in add_physics_object, but it does?
            commands.append({"$type": "set_physic_material", "bounciness": 1, "id": wall_id})    
        else:
            ids = [slope_id]
        
        # # Make slope very 'slippery' #NOTE this shouldn't do anything, because we already set it in add_physics_object, but it does?
        commands.append({"$type": "set_physic_material", "dynamic_friction": 0, "static_friction": 0, "id": slope_id})
        
        # Set a random color, make platform the same color as slope
        color = {"r": random.random(), "g": random.random(), "b": random.random(), "a": 1.0}
        for object_id in ids:
            # Freeze position and rotation for each axis
            commands.extend([{"$type": "set_rigidbody_constraints", "id": object_id, "freeze_position_axes": {"x": 1, "y": 1, "z": 1}, "freeze_rotation_axes": {"x": 1, "y": 1, "z": 1}}])
            
            # Set a random color, make platform the same color as slope
            color = {"r": random.random(), "g": random.random(), "b": random.random(), "a": 1.0} if self.trial_type != 'agent' else color
            commands.append({"$type": "set_color",
                            "color": color,
                            "id": object_id})
        return commands
    
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp'
        '''
        # Add camera
        if self.trial_type == 'agent':
            position = {"x": 0, "y": 1.2, "z": -2}
        else:
            position = {"x": 0, "y": 1.2, "z": -1}

        look_at = {"x": 0, "y": 0, "z": 0}
        camera = ThirdPersonCamera(position=position,
                           look_at=look_at,
                           avatar_id='frames_temp')
        self.add_ons.append(camera)
        return position, look_at

    def trial_initialization_commands(self):
        o_id = self.get_unique_id()

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [o_id] if self.trial_type != 'agent' else [o_id, self.get_unique_id()]

        commands = []

        object_choice = random.choice(self.objects)
        self.object_choice = object_choice

        # self.names is put in the csv files, so the developers know which object(s) are chosen
        self.names = {'object':object_choice}

        # Flip object if needed to roll, e.g. cola can
        rotation_x = 0 if object_choice not in ROLLING_FLIPPED else random.choice([90, -90])
        
        # Get position for falling object
        position = {"x": random.uniform(-.15,-.1), "y": random.uniform(4, 5), "z": random.uniform(-.15,.15)}
        self.o_loc = position

        if self.trial_type == 'agent':
            # Put target on top instead
            commands = self.add_target(commands)
            self.names['target'] = self.target_rec.name


            # Put agent random position
            position = {"x": random.uniform(2.5, 3), "y": random.uniform(0, .5), "z": random.uniform(-.15,.15)}
            

        # Add object
        commands.extend(self.get_add_physics_object(model_name=object_choice,
                                                    library='models_core.json',
                                                    object_id=o_id,
                                                    position=position,
                                                    rotation={"x": rotation_x, "y": 0, "z": 0}))
        

        # Keep track of transforms, so we can keep track of the movement
        commands.extend([{"$type": "send_transforms",
                                  "frequency": "always"},
                        {"$type": "send_rigidbodies",
                       "frequency": "always"},
                      {"$type": "send_static_rigidbodies",
                       "frequency": "once"}])
        return commands
    
if __name__ == "__main__":
    c = Slope()

    # Retrieve the right arguments
    args = create_arg_parser()
    print(message('add_object_to_scene is set to True', 'warning'))
    success = c.run(num=args.num, pass_masks=args.pass_masks, room=args.room, tot_frames=args.tot_frames,
                    add_object_to_scene=True, trial_type=args.trial_type,
                    png=args.png, save_frames=args.save_frames, save_mp4=args.save_mp4)
    print(success)