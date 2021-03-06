from car_parts.clock import Timestamp
from car_parts.donkey_tub_library import TubGroup, TubWriter
from car_parts.transform import Lambda,PIDController
from car_parts.camera_handler.picamera_handler import CarPiCamera
from car_parts.web_handler.donkeycar_web_handler import LocalWebController
from controllers.ps3_controller.controller import PS3JoystickController
from car_parts.actuators import PWM_MG996R_Steering,PWM_L298N_Throttle
from vehicle_handler import VehicleHandler
import os
import config as cfg


def drive(cfg):
	v=VehicleHandler()
	clock=Timestamp()
	cam=CarPiCamera(res=cfg.CAMERA_RESOLUTION)
	web_ctr=LocalWebController(use_chaos=False)
	pwm_mg996r_steering=PWM_MG996R_Steering()
	pwm_l298n_throttle=PWM_L298N_Throttle()

	v.add(web_ctr,
			inputs=["cam/image_array"],
			outputs=["user/angle","user/throttle","user/mode","recording"],
			threaded=True)
	v.add(cam, outputs=['cam/image_array'], threaded=True)
	def drive_mode(mode,
					user_angle, user_throttle,
					pilot_angle, pilot_throttle):
		if mode == 'user':
			return user_angle, user_throttle

		elif mode == 'local_angle':
			return pilot_angle, user_throttle

		else:
			return pilot_angle, pilot_throttle

	drive_mode_part = Lambda(drive_mode)
	v.add(drive_mode_part,
			inputs=['user/mode', 'user/angle', 'user/throttle',
					'pilot/angle', 'pilot/throttle'],
			outputs=['angle', 'throttle'])
	v.add(
		pwm_mg996r_steering,
		inputs=['angle'],
                threaded=False,
	)
	v.add(
		pwm_l298n_throttle,
		inputs=['throttle'],
                threaded=False,
	)
	inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode', 'timestamp']
	types = ['image_array', 'float', 'float',  'str', 'str']
	tub= TubWriter(path=cfg.TUB_PATH,inputs=inputs,types=types)
	v.add(tub,inputs=inputs,run_condition="recording")
	v.start(
			rate_hz=cfg.DRIVE_LOOP_HZ,
			max_loop_count=cfg.MAX_LOOPS
			)
drive(cfg)

