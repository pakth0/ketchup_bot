import cv2
from deepface import DeepFace
import os
import argparse

def compare_faces(img1, img2):
    return DeepFace.verify(img1_path=img1, img2_path=img2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--img1", type=str, required=True, help="Path to the first image")
    parser.add_argument("--img2", type=str, required=True, help="Path to the second image")
    args = parser.parse_args()
    result = compare_faces(args.img1, args.img2)
    print(result)

if __name__ == "__main__":
    main()
    
    