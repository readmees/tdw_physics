# STATUS: V2 Passing OT
'''
Readme:
The core of of this code is taken from tdw_physics, from containment.py 
tdw_physics uses custom/random physics, here we use the default
Now the transition is a force, of course teleport could make sense as well

Possible improvements:
Stop frames when objects is out of screen
'''
from typing import List
from random import choice, uniform
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from tdw.librarian import ModelLibrarian
from tdw.add_ons.third_person_camera import ThirdPersonCamera

import random

from helpers.runner_main import Runner
from helpers.objects import CONTAINERS, CONTAINED
from helpers.helpers import get_two_random_records, message, get_transforms, get_magnitude, get_record_with_name, get_distance

import numpy as np

class Containment(Runner):
    """
    Create a set of "Containment" trials, where a container object holds a smaller target
    object and is shaken violently, causing the target object to move around and possibly fall out.
    """
    def __init__(self, port: int = 1071):
        self.controller_name = 'containment'

        # Randomize x&z where objects will put
        self.o_x = random.uniform(-3, 3)
        self.o_z = random.uniform(-3, 3)
        super().__init__(port=port)
    
    def run_per_frame_commands(self, trial_type, tot_frames):
        # Agent speed
        speed, up_speed = .06, .06
        first_resp = False
        agent_success = False

        bounds = np.max(TDWUtils.get_bounds_extents(self.o_record .bounds))/2 
        bounds += np.max(TDWUtils.get_bounds_extents(get_record_with_name('sphere', json='models_flex.json').bounds))*.2/2 

        if trial_type == 'transition':
            rotations, positions = [], []

            # Define the amount of patience the program has before a transition is enabled
            patience = random.randint(20, 40)

            commands = []
            transitions_avoided = 0
            for i in range(tot_frames):
                print(i)
                resp = self.communicate(commands)
                commands = []
                o_rotation_deg, container_position, _ = get_transforms(resp, self.o_ids[0])
                rotations.append(o_rotation_deg)
                positions.append(container_position)

                # Only look back at the last x frames and only consider transition after x frames
                if len(rotations) == patience:
                    # See if the container stopped mostly shaking the last x frames
                    rotation_sleep = np.array([np.std(np.array(rotations)[:,i]) < .3 for i in range(3)]).all()
                    positions_sleep = np.array([np.std(np.array(positions)[:,i]) < .3 for i in range(3)]).all()
                    
                    if rotation_sleep and positions_sleep:
                        # Get position of transtions object
                        o_position = get_transforms(resp, self.o_ids[1])[1]
              
                        # Check how far away the object is from the center of the container
                        o_relative_position = np.abs(np.array(container_position) - np.array(o_position))

                        # Get roughly the maximum discance the object may be from the center
                        # Moreover, for x and z this is to the border of the container,
                        # for y, this is halfway the container
                        max_distance = np.abs(np.array([bound for bound in self.bounds[1]]))

                        # Activatie transition only if the object is inside container #NOTE this is not perfect
                        activate_transition = (o_relative_position<max_distance).all()

                        if activate_transition:
                            print('transition!!!')
                            # commands.append({"$type": "object_look_at_position",
                            #                 "position":  {"x": random.uniform(-10, 10), 
                            #                               "y": random.uniform(0, o_position[1]), 
                            #                               "z": random.uniform(-10, 10)},
                            #                 "id": self.o_ids[1]})

                            # Get suitable random force
                            force = get_magnitude(self.o_record)*.25

                            # Apply a force to the object
                            commands.append({"$type": "apply_force_at_position", 
                                             "id": self.o_ids[1], 
                                             "force": {"x":force, "y": 0, "z": force}, 
                                             "position": {"x": random.uniform(-10, 10), 
                                                        "y": 0, 
                                                        "z": random.uniform(-10, 10)}})

                            # Reset patience before next transition starts
                            rotations, positions = [], []
                            patience = random.randint(20, 40)
                            transitions_avoided = 0
                        else:
                            transitions_avoided += 1 
                            if transitions_avoided > 10:
                                break

                    # Make room for the next frame
                    rotations, positions = rotations[1:], positions[1:]
        for i in range(tot_frames):
            if trial_type == 'object':
                self.communicate([])

            if trial_type == 'agent':
                up_speed -= .005 if up_speed > 0 else 0
                commands = [{"$type": "teleport_object_by", 
                                              "position": {"x": 0, "y": up_speed, "z": 0}, 
                                              "id": self.o_ids[1], 
                                              "absolute": True},
                                             {"$type": "teleport_object_by", 
                                              "position": {"x": 0, "y": 0, "z": speed}, 
                                              "id": self.o_ids[1], 
                                              "absolute": False},
                                              {"$type": "object_look_at", 
                                               "other_object_id": self.o_ids[2], 
                                               "id": self.o_ids[1]},]
                if not first_resp:
                    resp = self.communicate(commands)
                    first_resp = True
                elif (get_distance(resp, self.o_ids[1], self.o_ids[2])- bounds) <.06  or agent_success:
                    resp = self.communicate([])
                    agent_success = True
                else:
                    resp = self.communicate(commands)

            
                            
        # Reset the scene by destroying the objects
        destroy_commands = []
        for o_id in self.o_ids:
            destroy_commands.append({"$type": "destroy_object",
                            "id": o_id})
        destroy_commands.append({"$type": "send_rigidbodies",
                            "frequency": "never"})
        self.communicate(destroy_commands)

    def add_target(self, commands):
        # self.o_ids = [agent_id, occ_id, target_id]
        target_id = self.o_ids[2]

        # Put target on same position as agent 
        # But moved in the z position, so it is in front
        x = self.o_x + random.uniform(1,.5) if random.choice([True, False]) else self.o_x - random.uniform(1,.5)
        z = self.o_z + random.uniform(1,.5) if random.choice([True, False]) else self.o_z - random.uniform(1,.5)

        position={"x": x,
                "y": random.uniform(0, 0.3),
                "z": z}

        # Set scale
        scale = .2

        # Add object1
        commands.extend(self.get_add_physics_object(model_name='sphere',
                                                    library='models_flex.json',
                                                    object_id=target_id,
                                                    position=position,
                                                    scale_factor={"x": scale, "y": scale, "z": scale},
                                                    ))
        # Make target red
        commands.append({"$type": "set_color",
                        "color": {"r": 1., "g": 0., "b": 0., "a": 1.},
                        "id": target_id})
        return commands

    def add_object_to_scene(self, commands):
        '''This method will add a fixed object to the scene that the container has something to balance/shake on,
        since the object will not change during trials and is fixed in place, it will be added to the background shot'''
        balancer_name = random.choice([record.name for record in ModelLibrarian('models_flex.json').records])

        # Get good scale for balancer, compared to most of the containers
        balancer_scale = .45

        # Get height of balancer
        balancer_rec = get_record_with_name(balancer_name, json='models_flex.json') 
        self.balancer_height = TDWUtils.get_bounds_extents(balancer_rec.bounds)[1] * balancer_scale

        object_id = self.get_unique_id()

        # Add the balancer object
        commands.extend(self.get_add_physics_object(model_name=balancer_name,
                                                library="models_flex.json",
                                                object_id=object_id,
                                                position={"x": self.o_x,
                                                            "y": 0,
                                                            "z":self.o_z},
                                                rotation=TDWUtils.VECTOR3_ZERO,
                                                scale_factor={"x": balancer_scale,
                                                                "y": balancer_scale,
                                                                "z": balancer_scale}))
        
        # Freeze position and rotation for each axis
        commands.extend([{"$type": "set_rigidbody_constraints", "id": object_id, "freeze_position_axes": {"x": 1, "y": 1, "z": 1}, "freeze_rotation_axes": {"x": 1, "y": 1, "z": 1}}])
        
        # Set a random color.
        commands.append({"$type": "set_color",
                        "color": {"r": random.random(), "g": random.random(), "b": random.random(), "a": 1.0},
                        "id": object_id})
        return commands
    
    def set_camera(self):
        ''' The avatar_id of the camera should be 'frames_temp' '''
        # Add camera
        camera = ThirdPersonCamera(position={"x": self.o_x+uniform(-1,1), "y": uniform(3.2,3.4), "z": self.o_z+uniform(-1, 1)},
                           look_at={"x": self.o_x, "y": 1.0, "z": self.o_z},
                           avatar_id='frames_temp')
        self.add_ons.append(camera)

    def trial_initialization_commands(self):
        commands = []
        # Select a random container and contained object
        records, self.bounds = get_two_random_records(smaller_list=CONTAINED, larger_list=CONTAINERS)
        
        # Get balancer height to see how hight container should be placed
        height = self.balancer_height
        y = height + random.uniform(.1, .2)

        # Select a container.
        container_id = self.get_unique_id()
        commands.extend(self.get_add_physics_object(model_name=records[1].name,
                                                    library="models_core.json",
                                                    object_id=container_id,
                                                    position={"x": self.o_x,
                                                              "y": y,
                                                              "z": self.o_z},
                                                    rotation={"x": uniform(-10, 10),
                                                              "y": uniform(-10, 10),
                                                              "z": uniform(-10, 10)}))
        
        # Add a random agent object
        self.o_record = records[0]
        o_id = self.get_unique_id()
        self.o_ids = [container_id, o_id] if self.trial_type != 'agent' else [container_id, o_id, self.get_unique_id()]
        commands.extend(self.get_add_physics_object(model_name=self.o_record.name,
                                                    library="models_core.json",
                                                    object_id=o_id,
                                                    position={"x": self.o_x,
                                                              "y": 0.8,
                                                              "z": self.o_z},
                                                    rotation={"x": uniform(-45, 45),
                                                              "y": uniform(-45, 45),
                                                              "z": uniform(-45, 45)}))
        if self.trial_type == 'agent':
            commands = self.add_target(commands)
            
        commands.extend([{"$type": "send_rigidbodies",
                                  "frequency": "always"},
                                 {"$type": "send_transforms",
                                  "frequency": "always"}])

        return commands

if __name__ == "__main__":
    c = Containment()
    success = c.run(num=5, pass_masks=['_img', '_mask'] , room='empty', tot_frames=200, add_object_to_scene=True, trial_type='agent')
    print(success)