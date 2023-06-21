from typing import Dict
import numpy as np
import random
from tdw.controller import Controller
import ffmpeg
import sys


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
        (
            ffmpeg
            .input(input_names, pattern_type='glob', framerate=fps)
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

