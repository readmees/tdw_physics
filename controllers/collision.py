# STATUS: V2 - All the trial types are implemented, can be improved
'''
Readme:
Example usage: python collision.py --pass_masks _img,_mask   
All the masses are fixed to a mass of 1
Trial will start again depending on collision

Possible improvements:
There will be more fall collisions, since force collisions fail more often
Add rolling down collision
Noise in position could be dependend on width of objects
Random force positions could better
Make sure objects stop at wall
Check if it's likely target is visible: 
-ball category is in screen, 
-albedo is empty where id is not (ball is not spotted on albedo)
-assumed ball is completely in camera view
'''
# Added for collisions
from helpers.runner_main import Runner

# To keep track of where the moving objects is
from tdw.output_data import Transforms, OutputData
import random 
from helpers.objects import *
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from helpers.helpers import *
from copy import deepcopy
from tdw.tdw_utils import TDWUtils
from random import uniform
import numpy as np
from tdw.add_ons.collision_manager import CollisionManager

from PIL import Image
import os
import numpy as np

class Collision(Runner):

    def __init__(self, port=1071):
        self.controller_name = 'collision'

        # Concatenate the lists and remove duplicates 
        # NOTE: Exclude OCCLUDERS & OCCLUDERS_SEE_THROUGH, because they then to need a lot of force
        self.objects = list(set(CONTAINERS + OCCLUDED + ROLLING_FLIPPED))
      
        self.camera_pos = {"x": random.uniform(1.5, 2), "y": 0.5, "z": random.uniform(-1, 1)}
        super().__init__(port=port)

    def run_per_frame_commands(self, trial_type, tot_frames):
        speed = [random.choice([-.1, 0, .1]), random.choice([-.1, 0, .1])]

        # Check if transition is done
        transition_compl = False  
        transition_frames = None if trial_type != 'transition' else []


        # Add a collision manager
        collision_manager = CollisionManager(enter=True, stay=False, exit=False, objects=True, environment=True)
        self.add_ons.append(collision_manager)
        collided = False

        # Settings for agent
        if trial_type == 'agent':
            speed = .06
            
            #NOTE might be better to exclude height or take rotation into account
            bounds_obstacle = np.max(TDWUtils.get_bounds_extents(get_record_with_name(self.objects[0]).bounds))/2 
            height_obstacle = TDWUtils.get_bounds_extents(get_record_with_name(self.objects[0]).bounds)[1]
            bounds_agent = np.max(TDWUtils.get_bounds_extents(get_record_with_name(self.objects[1]).bounds))/2 
            bounds_target = np.max(TDWUtils.get_bounds_extents(get_record_with_name('sphere', json='models_flex.json').bounds))*.2/2 
            bounds = bounds_agent + bounds_target
            agent_success = False

            last_height = 0

            force = get_magnitude(get_record_with_name(self.objects[1]))
        if trial_type == 'transition':
            tot_bounds = np.max(TDWUtils.get_bounds_extents(get_record_with_name(self.objects[0]).bounds))/2 
            tot_bounds += np.max(TDWUtils.get_bounds_extents(get_record_with_name(self.objects[1]).bounds))/2 

        for i in range(tot_frames):
            # Check if this is object based or transition trial
            if trial_type == 'transition':
                # Start transition when the objects are close #NOTE size is not considered
                
                if transition_compl:
                    # Start moving the collider
                    resp = self.communicate([{"$type": "teleport_object_by", 
                                       "position": {"x": speed[0], 
                                                    "y": 0.0,
                                                    "z": speed[1]}, 
                                       "id": self.o_ids[0], 
                                       "absolute": True}])
                    
                    # Save frame number of transition(s)
                    transition_frames.append(i)
                else:
                    # Store response and make frame
                    resp = self.communicate([])
                    if (get_distance(resp, self.o_ids[0], self.o_ids[1]) - tot_bounds) < random.uniform(.5,.6):
                        transition_compl = True
            
            if trial_type == 'agent':
                success = True #TODO maybe remove
                commands = []
                if i == 0:
                    commands.extend([{"$type": "object_look_at", "other_object_id": self.o_ids[-1], "id": self.o_ids[1]},
                                             {"$type": "teleport_object_by", "position": {"x": 0, "y": 0, "z": speed}, "id": self.o_ids[1], "absolute": False}])
                elif (get_distance(resp, self.o_ids[1], self.o_ids[-1]) - bounds) <.4 or agent_success:
                    print('Succes')
                    if not agent_success:
                        # Target almost reached, apply force in its direction to enable collision
                        commands.extend([{"$type": "object_look_at", "other_object_id": self.o_ids[-1], "id": self.o_ids[1]},
                                            {"$type": "apply_force_magnitude_to_object",
                                            "magnitude": force,
                                            "id": self.o_ids[1]}])
                        agent_success = True
                    
                else:
                    commands.extend([{"$type": "object_look_at", "other_object_id": self.o_ids[-1], "id": self.o_ids[1]},
                                             {"$type": "teleport_object_by", "position": {"x": 0, "y": 0, "z": speed}, "id": self.o_ids[1], "absolute": False}])
                    
                    #NOTE: the following formula might not make sense, aims to calculate the right 'fly' height
                    if (get_distance(resp, self.o_ids[0], self.o_ids[1]) - (bounds_obstacle+bounds_agent)) < (height_obstacle/speed+speed*3):
                        height = get_transforms(resp, self.o_ids[1])[1][1]

                        # Go up if flight is not already descending #NOTE: might be shocky
                        if height > last_height:
                            commands.append({"$type": "teleport_object_by", "position": {"x": 0, "y": speed*2, "z": 0}, "id": self.o_ids[1], "absolute": True})
                            print('fly succes')
                            last_height = height
                        else:
                            print('fly avoid')
                            # Will only fly up once 
                            last_height = np.inf 

                resp = self.communicate(commands)
                 
            if trial_type == 'object':
                self.communicate([])

            # Check if the objects collided (at least once)
            if collision_manager.obj_collisions:
                collided = True
        
        # Reset the scene by destroying the objects
        destroy_commands = []
        for o_id in self.o_ids:
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)

        # Check if collision happened
        if trial_type == 'object':
            if not collided:
                print(message(f'Objects did not collide even though this is required for object trial...', 'error'))
            success = collided
        
        # Check if transition stopped collision
        if trial_type == 'transition':
            if collided:
                print(message(f'Objects did collide even though the transition object should avoid...', 'error'))
            if not transition_compl:
                print(message(f'Transition didn\'t happend for this trial', 'warning'))
            success = not collided  

        return transition_frames if transition_frames != [] else -1, success 
    
    def set_fall_postions(self):
        '''This method implements objects falling on top of each other, 
        by placing one above the other'''
        # Add postions for falling object
        fall_pos = {"x": random.uniform(-1, 1), "y": random.uniform(3, 5), "z": random.uniform(-1, 1)}
        
        # One object should be on the ground, underneath the falling object
        # Add some noise in position
        ground_pos = {'x':fall_pos['x'] + random.uniform(-.1, .1), 'y':0, 'z':fall_pos['z'] + random.uniform(-.1, .1)}

        return [ground_pos, fall_pos]
    
    def set_force_positions(self):
        # Add postions for moving object
        x = random.choice([random.uniform(-2.2, -.8), random.uniform(.8, 2.2)])
        z = random.choice([random.uniform(-2.2, -.8), random.uniform(.8, 2.2)])
        moving_pos = {"x": x, "y": 0, "z": z}
        
        # Add position of the object that will be in the way of the moving object
        coll_pos = {"x": random.uniform(-.5, .5), "y": 0, "z": random.uniform(-.5, .5)}

        return [coll_pos, moving_pos]

    def add_objects(self, commands, rotation):
        # If it's an agent trial one object should be the target so it'll be added seperately with self.add_target
        for i in range(self.num_objects if self.trial_type != 'agent' else self.num_objects - 1):
            commands.extend(self.get_add_physics_object(model_name=self.objects[i],
                                                        library='models_core.json',
                                                        object_id=self.o_ids[i],
                                                        position=self.positions[i],
                                                        rotation=rotation if i == 1 else {"x": 0, "y": 0, "z": 0},
                                                        mass=1
                                                        ))
        return commands

    def get_ob_pos(self, o_id, resp):
        '''Get object position'''
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            # Parse Transforms output data to get the object's position.
            if r_id == "tran":
                transforms = Transforms(resp[i])
                for j in range(transforms.get_num()):
                    if transforms.get_id(j) == o_id:
                        # Return position of object with o_id as object id
                        return transforms.get_position(j)
    
    def add_target(self, commands):
        target_id = self.o_ids[-1]
        
        #NOTE occluding object is perfectly in the middle?
        agent_pos = deepcopy(self.positions[1])
        agent_pos['z'] = -agent_pos['z']
        agent_pos['x'] = -agent_pos['x']
       
        return add_target_commands(target_id, agent_pos, commands)

    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp'
        '''
        # Add camera
        position, look_at = {"x": -1, "y": 1.5, "z": -3}, {"x": 0, "y": 0, "z": 0}
        self.camera = ThirdPersonCamera(position=position,
                           look_at=look_at,
                           avatar_id='frames_temp')
        self.add_ons.append(self.camera)
        return position, look_at
        
    def trial_initialization_commands(self):
        # Could be extended to multiple objects one day
        self.num_objects = 2 if self.trial_type != 'agent' else 3 #random.randint(3,4)

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [self.get_unique_id() for _ in range(self.num_objects)] 
        coll_id, move_id = self.o_ids[:2]

        # Choose between falling or force collisions
        coll_type = random.choice(['fall', 'force']) if self.trial_type != 'agent' else 'agent'

        # Get positions based on collision type 
        self.positions = self.set_force_positions() if coll_type != 'fall' else self.set_fall_postions()

        #TODO let it work with more positions, idea: move random on left en right from the collidion position
        
        
        # To choose random object without putting back
        random.shuffle(self.objects)

        # Set rotation for falling objects
        rotation = {"x": uniform(0, 360) if random.choice([True, False]) else 0, 
                    "y": uniform(0, 360) if random.choice([True, False]) else 0, 
                    "z": uniform(0, 360) if random.choice([True, False]) else 0} if coll_type == 'fall' else {"x": 0, "y": 0, "z": 0}
        
        commands = self.add_objects(commands=[], rotation=rotation)
        if coll_type == 'force':
            # Get suitable magnitude
            magnitude = get_magnitude(get_record_with_name(self.objects[1]))/2
            magnitude = magnitude * 2.5 if self.objects[1] in EXTRA_FORCE else magnitude * .6

            commands.extend([{"$type": "object_look_at",
                    "other_object_id": coll_id,
                    "id": move_id},
                    {"$type": "apply_force_magnitude_to_object",
                    "magnitude": magnitude,
                    "id": move_id}])
            
        if coll_type == 'agent':
             #NOTE occluding object is perfectly in the middle?
            commands = self.add_target(commands)

        # self.names is put in the csv files, so the developers know which object(s) are chosen
        self.names = {'object1':self.objects[0], 'object2':self.objects[1]} #TODO update for agent


        # Get point non-moving object
        cam_turn = deepcopy(self.positions[0])

        # Turn camera up/down, if objects falls down
        cam_turn['y'] = 0 # self.positions[1]['y']/10 if coll_type == 'fall' else 1.5

        # Point camera towards non-moving object and up/down
        #TODO 'zoom in' depending on height of object
        self.camera.look_at(cam_turn)

        # Send transforms in order to keep track of locations
        commands.extend([{"$type": "send_transforms",
                                  "frequency": "always"},
                        {"$type": "send_rigidbodies",
                       "frequency": "always"},
                      {"$type": "send_static_rigidbodies",
                       "frequency": "once"}])
        
        # Request collisions data.
        commands.append({"$type": "send_collisions",
                        "enter": True, 
                        "stay": False,
                        "exit": False, 
                        "collision_types": ["obj"]})
        return commands
    
if __name__ == "__main__":
    c = Collision()

    # Retrieve the right arguments
    args = create_arg_parser()
    print(message('add_object_to_scene is set to False and tot_frames to 200', 'warning'))
    if '_category' not in args.pass_masks:
        args.pass_masks.append('_category')
        print(message('_category is added to pass_masks', 'warning'))
    success = c.run(num=args.num, pass_masks=args.pass_masks, room=args.room, tot_frames=150,
                    add_object_to_scene=False, trial_type=args.trial_type,
                    png=args.png, save_frames=args.save_frames, save_mp4=args.save_mp4)
    print(success)