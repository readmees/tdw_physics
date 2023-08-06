# STATUS: V2 - All the trial types are implemented, can be improved
'''
Readme:
Example usage: python collision.py --pass_masks _img,_mask   
All the masses are fixed to a mass of 1
Trial will start again depending on collision
The frame numbers (starting at 0) for transition and agent are saved, 
it is a list with all the frames where the object had agency

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

        # The framenumbers where a transition happens or agent is acting agentlike
        transition_frames = None if trial_type == 'object' else []


        # Add a collision manager
        collision_manager = CollisionManager(enter=True, stay=False, exit=False, objects=True, environment=True)
        self.add_ons.append(collision_manager)
        collided = False

        # Settings for agent
        if trial_type == 'agent':
            speed = .06

            print('target:', self.target_rec.name)
            print('agent:', self.objects[self.num_objects-2])

            
            #NOTE might be better to exclude height or take rotation into account
            bounds_agent = np.max(TDWUtils.get_bounds_extents(get_record_with_name(self.objects[self.num_objects-2]).bounds))/2 
            bounds_target = np.max(TDWUtils.get_bounds_extents(self.target_rec.bounds))*.2/2 
            bounds = bounds_agent + bounds_target

            force = get_magnitude(get_record_with_name(self.objects[1]))

            agent_success = False

            # Might need to keep count of two agent jumps
            bounds_obstacle, height_obstacle, jump_activated = [], [], []

            hor_distance, last_hor_distance = [], []
            for i in range(self.num_objects-2):
                # Get max bound of x and y
                bounds_obstacle.append(np.max(TDWUtils.get_bounds_extents(get_record_with_name(self.objects[i]).bounds))/2 )
                
                # Get height
                height_obstacle.append(TDWUtils.get_bounds_extents(get_record_with_name(self.objects[i]).bounds)[1])
                jump_activated.append(False)

                hor_distance.append(np.nan)
                last_hor_distance.append(np.nan)

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
                    commands.extend([{"$type": "object_look_at", "other_object_id": self.o_ids[-1], "id": self.o_ids[-2]},
                                             {"$type": "teleport_object_by", "position": {"x": 0, "y": 0, "z": speed}, "id": self.o_ids[-2], "absolute": False}])
                elif (get_distance(resp, self.o_ids[-2], self.o_ids[-1]) - bounds) <.4 or agent_success:
                    if not agent_success:
                        # Target almost reached, apply force in its direction to enable collision
                        commands.extend([{"$type": "object_look_at", "other_object_id": self.o_ids[-1], "id": self.o_ids[-2]},
                                            {"$type": "apply_force_magnitude_to_object",
                                            "magnitude": force,
                                            "id": self.o_ids[-2]}])
                        agent_success = True
                    
                else:
                    commands.extend([{"$type": "object_look_at", "other_object_id": self.o_ids[-1], "id": self.o_ids[-2]},
                                             {"$type": "teleport_object_by", "position": {"x": 0, "y": 0, "z": speed}, "id": self.o_ids[-2], "absolute": False}])
                    
                    for j in range(self.num_objects-2):
                        #NOTE: the following formula might not make sense, aims to calculate the right 'fly' height
                        if (get_distance(resp, self.o_ids[j], self.o_ids[-2]) - (bounds_obstacle[j]+bounds_agent)) < (height_obstacle[j]/speed+speed*3):
                            # Get xy distance for agent and obstacle j disregarding the height; the horizontal distance
                            pos_ag = {val:key for val,key in zip(['x', 'y', 'z'], get_transforms(resp, self.o_ids[-2])[1])}
                            pos_ob = {val:key for val,key in zip(['x', 'y', 'z'], get_transforms(resp, self.o_ids[j])[1])}
                            print(pos_ag, pos_ob)
                            pos_ag['y'], pos_ob['y'] = 0, 0
                            hor_distance[j] = TDWUtils.get_distance(pos_ag, pos_ob)

                            # Only go up if the obstacle is comming closer
                            if hor_distance[j] < last_hor_distance[j]:
                                commands.append({"$type": "teleport_object_by", "position": {"x": 0, "y": speed*2, "z": 0}, "id": self.o_ids[-2], "absolute": True})

                            last_hor_distance[j] = hor_distance[j]
                    
                if 'teleport_object_by' in commands:
                    transition_frames.append(i)
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
        x = random.choice([random.uniform(-2.2, -1.5), random.uniform(1.5, 2.2)])
        z = random.choice([random.uniform(-2.2, -1.5), random.uniform(1.5, 2.2)])
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
        target_pos = deepcopy(self.positions[-1])
        target_pos['z'] = -target_pos['z']
        target_pos['x'] = -target_pos['x']

        #Bring target closer to middle point (to increase chance to be seen by camera)
        random_offset = random.uniform(.3, .5)
        target_pos['z'] += random_offset if target_pos['z'] < 0 else -random_offset
        target_pos['x'] += random_offset if target_pos['x'] < 0 else -random_offset

        # Bring slightly closer to the middle so target is often in sight
        commands, self.target_rec = add_target_commands(target_id, target_pos, commands)
        return commands

    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp'
        '''
        # Add camera
        position, look_at = {"x": -3.2, "y": 3, "z": -3.2}, {"x": 0, "y": 0, "z": 0}
        self.camera = ThirdPersonCamera(position=position,
                                        look_at=look_at,
                                        avatar_id='frames_temp')
        self.add_ons.append(self.camera)
        return position, look_at
        
    def trial_initialization_commands(self):
        # Could be extended to multiple objects one day
        self.num_objects = 2 if self.trial_type != 'agent' else random.randint(3,4)

        # Always store object ids so the main runner knows which to remove
        self.o_ids = [self.get_unique_id() for _ in range(self.num_objects)] 
        coll_id, move_id = self.o_ids[:2]

        # Choose between falling or force collisions
        coll_type = random.choice(['fall', 'force']) if self.trial_type != 'agent' else 'agent'

        # Get positions based on collision type
        self.positions = self.set_force_positions() if coll_type != 'fall' else self.set_fall_postions()

        # Get point non-moving object or more or less middle point from the two non-moving non-target objects
        cam_turn = deepcopy(self.positions[0])

        # Turn camera up/down, if objects falls down
        cam_turn['y'] = 0 # self.positions[1]['y']/10 if coll_type == 'fall' else 1.5

        # Point camera towards non-moving object and up/down
        #TODO 'zoom in' depending on height of object
        self.camera.look_at(cam_turn)

        # Add extra obstacle if needed, idea: move random on left en right from the colliding position
        # self.positions becomes [obstacle_pos, obstacle_pos, moving_pos]
        if self.num_objects == 4:
            # New self.positions becomes 
            self.positions.insert(0, self.positions[0])

            # Choosing only one offset per pos ensures they are in the same angle 
            div1, div2 = random.uniform(1.5, 3), random.uniform(1.5, 3)
            self.positions[0] = {key:val/div1 for key,val in self.positions[-1].items()}
            self.positions[1] = {key:-val/div2 for key,val in self.positions[-1].items()}
        
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
            self.names = {'agent': self.objects[self.num_objects-2], 
                          'target': self.target_rec.name,
                          'obstacles': self.objects[:2]} 

        else:
            self.names = {'object1':self.objects[0], 'object2':self.objects[1]}

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