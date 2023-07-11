from typing import Dict
import numpy as np
import random
import ffmpeg
import sys

# For get_two_random_records()
from tdw.librarian import ModelLibrarian
from tdw.tdw_utils import TDWUtils

# For get_sleeping() and get_transforms()
from tdw.output_data import OutputData, Transforms, Rigidbodies

# For rotation in degrees (get_transforms)
from scipy.spatial.transform import Rotation

# For mass in get_transforms()
from tdw.output_data import StaticRigidbodies

class ObjectInfo:
    """
    Based on ObjectPosition from &tdw_physics
    """

    def __init__(self, position: Dict[str, float], radius: float, id: int):
        """
        :param position: The position of the object.
        :param radius: The maximum radius swept by the object's bounds.
        :param id: The object id
        """

        self.position = position
        self.radius = radius
        self.id = id
 
def get_random_avatar_position(radius_min: float, radius_max: float, y_min: float, y_max: float,
                                center: Dict[str, float], angle_min: float = 0,
                                angle_max: float = 360) -> Dict[str, float]:
        """
        The same as get_random_avatar_position from &tdw_physics
        :param radius_min: The minimum distance from the center.
        :param radius_max: The maximum distance from the center.
        :param y_min: The minimum y positional coordinate.
        :param y_max: The maximum y positional coordinate.
        :param center: The centerpoint.
        :param angle_min: The minimum angle of rotation around the centerpoint.
        :param angle_max: The maximum angle of rotation around the centerpoint.

        :return: A random position for the avatar around a centerpoint.
        """

        a_r = random.uniform(radius_min, radius_max)
        a_x = center["x"] + a_r
        a_z = center["z"] + a_r
        theta = np.radians(random.uniform(angle_min, angle_max))
        a_x = np.cos(theta) * (a_x - center["x"]) - np.sin(theta) * (a_z - center["z"]) + center["x"]
        a_y = random.uniform(y_min, y_max)
        a_z = np.sin(theta) * (a_x - center["x"]) + np.cos(theta) * (a_z - center["z"]) + center["z"]

        return {"x": a_x, "y": a_y, "z": a_z}

def images_to_video(image_folder, video_name, fps, pass_masks, png):
    '''From https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md#assemble-video-from-sequence-of-frames'''


    for mask_type in pass_masks:
        # Added for good order of frames
        input_names = f'{image_folder}/{mask_type.replace("_", "")}_*'
        file_ex = '.jpg' if not png and mask_type == '_img' else '.png'
        input_names += file_ex

        # Create the video for every mask type, loglevel="quiet" to mute output
        # Every first frame is skipped
        (
            ffmpeg
            .input(input_names, pattern_type='glob', framerate=fps)
            .filter('select', 'gte(n, 1)')
            .output(video_name+f'{mask_type}.mp4', loglevel="quiet")
            .run()

        )

def message(message, message_type, progress=None):
    '''
    Example usage:
    print_message('error_message', "error")
    print_message('warning_message', "warning")
    print_message('success_message', "success")

    Example usage with progress:
    for i in range(11):
        print_message("Processing", "success", i)
        time.sleep(0.5)
    '''
    prefix = ""
    color_code = ""

    if message_type == "error":
        prefix = "❌ ERROR: "
        color_code = "\033[91m"  # Red color
    elif message_type == "warning":
        prefix = "⚠️ WARNING: "
        color_code = "\033[93m"  # Yellow color
    elif message_type == "success":
        prefix = "✅ SUCCESS: "
        color_code = "\033[92m"  # Green color

    reset_code = "\033[0m"
    full_message = f"{prefix}{message}"

    if progress is None:
        formatted_message = f"{color_code}{full_message}{reset_code}"
    else:
        progress_bar = "[" + "#" * progress + "-" * (10 - progress) + "]"
        formatted_message = f"{color_code}{full_message}{reset_code} {progress_bar} {progress * 10}%"
        print(formatted_message, end="\r")
        sys.stdout.flush()
        
    return formatted_message+"\r"

def get_record_with_name(name):
    '''Get record of object by name
    param name: type str, should be in models_full.json
    '''
    lib = ModelLibrarian('models_full.json')
    records = {record.name:record for record in lib.records}
    return records[name]
        
def get_two_random_records(smaller_list, larger_list, axis = [0, 1, 2]):
        '''This method gets two objects, where one is smaller then the other

        param smaller_list: record list where a random smaller object will be selected (e.g. occluded)
        param larger_list: record list where a random larger object will be selected (e.g. occluder)
        param axis: decides if x, y and/or z should be larger

        returns: 1. a list of the record of the smaller object and the record of the larger object
                 2. a list of the bounds extends, [bounds_extents_small, bounds_extents_large]
        ''' 
        #NOTE this will create an infinite loop if all smaller objects are larger then the larger objects
        while True:
            # Choose a random smaller object
            o_smaller_name = random.choice(smaller_list)
            o_smaller_rec = get_record_with_name(o_smaller_name)

            # Get height and width of moving object #TODO check this formula
            bounds_extents_small = TDWUtils.get_bounds_extents(o_smaller_rec.bounds)

            # Loop through random occluder objects without putting back
            random.shuffle(larger_list)
            for name in larger_list:
                # Get record of moving object
                o_larger_rec = get_record_with_name(name)

                # Calculate height and width of occluder #TODO check this formula
                bounds_extents_large = TDWUtils.get_bounds_extents(o_larger_rec.bounds)

                # Check if the larger object is larger for all relevant axis
                axis_met = []
                for i in axis:
                    if bounds_extents_large[i] > bounds_extents_small[i]:
                        axis_met.append(i)

                # Return objects if all relevant axis are larger
                if axis_met == axis:
                    return [o_smaller_rec, o_larger_rec], [bounds_extents_small, bounds_extents_large]
                
def get_sleeping(resp, o_id):
    ''' This function finds out if an object is sleeping or not
    param resp: responce of the last communicate
    o_id: type int, should be the '''
    #NOTE: does not always work
    sleeping = False
    for i in range(len(resp) - 1):
        r_id = OutputData.get_data_type_id(resp[i])
        if r_id == "rigi":
            rigidbodies = Rigidbodies(resp[i])
            for j in range(rigidbodies.get_num()):
                if rigidbodies.get_id(j) == o_id:
                    sleeping = rigidbodies.get_sleeping(j)
    return sleeping

def get_transforms(resp, o_id):
    ''' Get mass, position and rotation of object with object id o_id'''
    o_rotation_deg, o_position, o_mass = None, None, None
    for i in range(len(resp) - 1):
        r_id = OutputData.get_data_type_id(resp[i])
        # Parse Transforms output data to get the object's position.
        if r_id == "tran":
            transforms = Transforms(resp[i])
            for j in range(transforms.get_num()):
                if transforms.get_id(j) == o_id:
                    o_position = transforms.get_position(j)
                    q = transforms.get_rotation(j)
                    
                    # Create a Rotation object from the quaternion #NOTE: by ChatGPT might be wrong
                    r = Rotation.from_quat(q)

                    # Convert the rotation to Euler angles (in radians) #NOTE: by ChatGPT might be wrong
                    euler_angles = r.as_euler('xyz')

                    # Convert the Euler angles to degrees #NOTE: by ChatGPT might be wrong
                    o_rotation_deg = np.degrees(euler_angles)
        elif r_id == "srig":
                srig = StaticRigidbodies(resp[i])
                for j in range(srig.get_num()):
                    o_mass = srig.get_mass(j)

    return o_rotation_deg, o_position, o_mass