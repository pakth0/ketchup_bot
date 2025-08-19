#!/usr/bin/env python3
import argparse
import time
from typing import Union

import cv2


def parse_source(source_arg: str) -> Union[int, str]:
	# Try to interpret numeric strings as camera indices (e.g., "0", "1")
	try:
		return int(source_arg)
	except ValueError:
		return source_arg  # path/URL


def open_capture(source: Union[int, str], backend: str) -> cv2.VideoCapture:
	if backend == "auto":
		return cv2.VideoCapture(source)
	if backend == "avfoundation":
		# Recommended on macOS
		return cv2.VideoCapture(source, cv2.CAP_AVFOUNDATION)
	if backend == "qt":
		return cv2.VideoCapture(source, cv2.CAP_QT)
	if backend == "v4l2":
		return cv2.VideoCapture(source, cv2.CAP_V4L2)
	# Fallback
	return cv2.VideoCapture(source)


def main():
	parser = argparse.ArgumentParser(
		description="Stream video from a camera or URL using OpenCV."
	)
	parser.add_argument(
		"--source",
		default="0",
		help="Camera index (e.g., 0) or a path/URL (e.g., file.mp4, rtsp://...). Default: 0",
	)
	parser.add_argument("--width", type=int, default=None, help="Requested frame width.")
	parser.add_argument("--height", type=int, default=None, help="Requested frame height.")
	parser.add_argument("--fps", type=int, default=None, help="Requested capture FPS.")
	parser.add_argument(
		"--backend",
		choices=["auto", "avfoundation", "qt", "v4l2"],
		default="auto",
		help="Capture backend. On macOS, try 'avfoundation' if default fails.",
	)
	parser.add_argument(
		"--mirror",
		action="store_true",
		help="Mirror the preview horizontally (useful for front-facing cameras).",
	)
	parser.add_argument(
		"--display-fps",
		action="store_true",
		help="Overlay FPS on the preview window.",
	)
	parser.add_argument(
		"--window",
		default="Camera",
		help="Window title. Default: 'Camera'",
	)

	args = parser.parse_args()
	source = parse_source(args.source)

	cap = open_capture(source, args.backend)

	if not cap.isOpened():
		raise SystemExit(
			f"Failed to open source '{args.source}' with backend '{args.backend}'. "
			f"Check camera permissions and availability."
		)

	# Try setting capture properties if provided
	if args.width is not None:
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
	if args.height is not None:
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
	if args.fps is not None:
		cap.set(cv2.CAP_PROP_FPS, args.fps)

	cv2.namedWindow(args.window, cv2.WINDOW_NORMAL)

	# FPS calculation (updated every ~1s)
	last_fps_time = time.time()
	frame_counter = 0
	current_fps = 0.0

	try:
		while True:
			ok, frame = cap.read()
			if not ok:
				print("End of stream or read error.")
				break

			if args.mirror:
				frame = cv2.flip(frame, 1)

			# Update FPS once per second
			frame_counter += 1
			now = time.time()
			elapsed = now - last_fps_time
			if elapsed >= 1.0:
				current_fps = frame_counter / elapsed
				frame_counter = 0
				last_fps_time = now

			if args.display_fps:
				text = f"{current_fps:.1f} FPS"
				cv2.putText(
					frame,
					text,
					(10, 30),
					cv2.FONT_HERSHEY_SIMPLEX,
					1.0,
					(0, 255, 0),
					2,
					cv2.LINE_AA,
				)

			cv2.imshow(args.window, frame)

			key = cv2.waitKey(1) & 0xFF
			if key in (ord("q"), 27):  # q or ESC to quit
				break
	finally:
		cap.release()
		cv2.destroyAllWindows()


if __name__ == "__main__":
	main()