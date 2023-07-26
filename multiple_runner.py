from os import system
from controllers.helpers.helpers import create_arg_parser, message


args = create_arg_parser(process_pass_masks=False)
print(message('The trial_type param will be ignored', 'warning'))
input_passed = False
while input_passed != True:
    try:
        user_input = int(input('How many sets of trials would you like to run?'))
        input_passed = True
    except ValueError:
        print(message("Invalid input. Please enter an integer.", 'error'))
        
for i in range(user_input):
    for controller in ['collision', 'containment', 'occlusion', 'rolling_down']:
        for trial_type in ['object', 'transition', 'agent']:
            command = f'python controllers/{controller}.py'
            command += f' --num {args.num} --trial_type {trial_type} --png {args.png} --pass_masks {args.pass_masks} --framerate {args.framerate}'
            command += f' --room {args.room} --tot_frames {args.tot_frames} --add_object_to_scene {args.add_object_to_scene}'
            command += f' --save_frames {args.save_frames} --save_mp4 {args.save_mp4}'
            print(command)
            system(command)