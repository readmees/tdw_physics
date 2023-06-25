# Status: V1 Experimental
#TODO: shaking doesn't work yet
#TODO: freeze y-axis
from typing import List
from random import choice, uniform
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from tdw.librarian import ModelLibrarian
from tdw_physics.rigidbodies_dataset import RigidbodiesDataset
from tdw_physics.physics_info import PHYSICS_INFO
from tdw_physics.util import get_args
from tdw.add_ons.third_person_camera import ThirdPersonCamera

from runner_main import Runner
class Containment(Runner):
    """
    Create a set of "Containment" trials, where a container object holds a smaller target
    object and is shaken violently, causing the target object to move around and possibly fall out.
    """

    Controller.MODEL_LIBRARIANS["models_core.json"] = ModelLibrarian("models_core.json")
    CONTAINERS = ["b03_696615_object001",
"b03_object05",
"b04_bowl_smooth",
"int_kitchen_accessories_le_creuset_bowl_30cm",
"serving_bowl",
"teatray",
"woven_box"]
    OBJECTS = ["amphora_jar_vase",
"apple",
"b03_burger",
"b04_banana",
"b04_orange_00",
"golf",
"hexagonal_toy",
"jug01",
"moet_chandon_bottle_vray",
"orange",
"star_wood_block"]
    O_X = -1.3
    O_Z = -2.15

    def __init__(self, port: int = 1071):
        super().__init__(port=port)

        self.controller_name = 'containment'

        for key in PHYSICS_INFO:
            # All containers have the same physics values. Set these manually.
            if key in Containment.CONTAINERS:
                PHYSICS_INFO[key].mass = 3

        # Commands to shake the container per frame.
        self._shake_commands: List[List[dict]] = []
        self._max_num_frames: int = 0

    def set_camera(self):
        # Add camera
        camera = ThirdPersonCamera(position={"x": -0.625, "y": 2.0, "z": -0.7},
                           look_at={"x": -1.0, "y": 1.0, "z": -1.5},
                           avatar_id=self.controller_name)
        self.add_ons.append(camera)

    def trial_initialization_commands(self):
        # Teleport the avatar.
        # Look at the target aim-point.
        commands = [
            # {"$type": "teleport_avatar_to",
            #          "position": {"x": -0.625, "y": 2.0, "z": -0.7}},
            #         {"$type": "look_at_position",
            #          "position": {"x": -1.0, "y": 1.0, "z": -1.5}}
                     ]

        # Select a container.
        # Manually set the mass of the container.
        container_name = choice(Containment.CONTAINERS)
        container_scale = TDWUtils.get_unit_scale(PHYSICS_INFO[container_name].record) * 0.6
        container_id = self.get_unique_id()
        commands.extend(self.get_add_physics_object(model_name=container_name,
                                                    library="models_core.json",
                                                    object_id=container_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.25,
                                                              "z": Containment.O_Z},
                                                    rotation=TDWUtils.VECTOR3_ZERO,
                                                    scale_factor={"x": container_scale,
                                                                  "y": container_scale,
                                                                  "z": container_scale}))
        # Add a random target object, with random size, mass, bounciness and initial orientation.
        object_name = choice(Containment.OBJECTS)
        o_id = self.get_unique_id()
        o_record = Controller.MODEL_LIBRARIANS["models_core.json"].get_record(object_name)
        o_scale = TDWUtils.get_unit_scale(o_record) * uniform(0.2, 0.3)
        self.o_ids = [o_id, container_id]
        commands.extend(self.get_add_physics_object(model_name=o_record.name,
                                                    library="models_core.json",
                                                    object_id=o_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.6,
                                                              "z": Containment.O_Z},
                                                    rotation={"x": uniform(0, 360),
                                                              "y": uniform(0, 360),
                                                              "z": uniform(0, 360)},
                                                    default_physics_values=False,
                                                    scale_mass=False,
                                                    mass=uniform(0.1, 0.5),
                                                    dynamic_friction=uniform(0.1, 0.5),
                                                    static_friction=uniform(0.1, 0.5),
                                                    bounciness=uniform(0.5, 0.95),
                                                    scale_factor={"x": o_scale, "y": o_scale, "z": o_scale}))
        # Let the objects settle.
        commands.append({"$type": "step_physics",
                         "frames": self.framerate})
        del self._shake_commands[:]
        # Set the shake commands.
        # Shake the container.
        for i in range(25):
            forceval = uniform(-1.5, 1.5)
            rot_axis = choice(["pitch", "roll", "yaw"])
            rotval = uniform(-2, 2)
            # Shake the container.
            for i in range(3):
                self._shake_commands.append([{"$type": "apply_force_to_object",
                                              "force": {"x": forceval, "y": 0, "z": 0},
                                              "id": container_id},
                                             {"$type": "rotate_object_by",
                                              "angle": rotval,
                                              "id": container_id,
                                              "axis": rot_axis,
                                              "is_world": False}])
            # Reset the rotation.
            for i in range(10):
                self._shake_commands.append([{"$type": "rotate_object_to",
                                              "rotation": {"w": 1, "x": 0, "y": 0, "z": 0},
                                              "id": container_id}])
            # Shake some more.
            for i in range(3):
                self._shake_commands.append([{"$type": "apply_force_to_object",
                                              "force": {"x": 0, "y": 0, "z": forceval},
                                              "id": container_id},
                                             {"$type": "rotate_object_by",
                                              "angle": rotval,
                                              "id": container_id,
                                              "axis": rot_axis,
                                              "is_world": False}])
            # Reset the rotation.
            for i in range(10):
                self._shake_commands.append([{"$type": "rotate_object_to",
                                              "rotation": {"w": 1, "x": 0, "y": 0, "z": 0},
                                              "id": container_id}])
            # Shake some more.
            for i in range(4):
                self._shake_commands.append([{"$type": "apply_force_to_object",
                                              "force": {"x": 0, "y": -forceval * 2.0, "z": 0},
                                              "id": container_id},
                                             {"$type": "rotate_object_by",
                                              "angle": rotval,
                                              "id": container_id,
                                              "axis": rot_axis,
                                              "is_world": False}])
            # Reset the rotation.
            for i in range(10):
                self._shake_commands.append([{"$type": "rotate_object_to",
                                              "rotation": {"w": 1, "x": 0, "y": 0, "z": 0},
                                              "id": container_id}])
        self._max_num_frames = len(self._shake_commands) + 500

        return commands

if __name__ == "__main__":
    c = Containment()
    success = c.run(num=5, pass_masks=['_img', '_id'], room='empty', tot_frames=800, add_slope=False, trial_type='object')
    print(success)