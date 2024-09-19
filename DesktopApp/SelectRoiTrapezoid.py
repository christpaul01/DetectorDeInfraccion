import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, simpledialog

# Global variables
roi_selected = False
roi_vertices = []
max_vertices = 4
num_pressed = 0
max_angle = 50
selection = ""

global line_start, line_end
line_selected = False

# Create a root window and hide it
root = tk.Tk()
root.withdraw()

# Create popup window to select ROI type
popup = tk.Tk()
popup.geometry("250x75")
popup.wm_title("ROI Selection")
popup.attributes("-topmost", True)
popup.eval('tk::PlaceWindow . center')


# Button functions
def select_normal():
    global selection
    selection = "normal"
    popup.destroy()


def select_prohibited():
    global selection
    selection = "prohibited"
    popup.destroy()


def calculate_angle(x1, y1, x2, y2):
    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
    print(angle)
    return abs(angle)


def is_inside_trapezoid(x, y, roi_vertices):
    # Check if the point x is inside the trapezoid
    return cv2.pointPolygonTest(np.array(roi_vertices), (x, y), False) >= 0


def draw_speedline(frame, roi_vertices):
    # Draw the previously selected ROI on the frame
    cv2.polylines(frame, [np.array(roi_vertices)], isClosed=True, color=(0, 255, 0), thickness=2)
    cv2.putText(frame, 'ROI: {}'.format(roi_vertices), (roi_vertices[0][0], roi_vertices[0][1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 210), 2, cv2.LINE_AA)

    # Create a window named "Video"
    cv2.namedWindow("Video")
    # Set the mouse callback function for line selection
    cv2.setMouseCallback("Video", select_speed_line)
    # Update the frame with the selected Speed Line
    cv2.imshow("Video", frame)
    # Wait for line selection
    cv2.waitKey(0)
    # Return the start and end points of the line
    return line_start, line_end

def select_speed_line(event, x, y, flags, param):
    global line_start, line_end, line_selected

    if event == cv2.EVENT_LBUTTONDOWN and is_inside_trapezoid(x, y, roi_vertices):
        line_start = (x, y)
        line_selected = False

    elif event == cv2.EVENT_LBUTTONUP and is_inside_trapezoid(x, y, roi_vertices):
        line_end = (x, y)
        line_selected = True
        cv2.line(frame, line_start, line_end, (0, 255, 0), 2)
        cv2.putText(frame, 'Speed Line: ({}, {})'.format(line_start[0], line_start[1]) + ' ({}, {})'.format(line_end[0], line_end[1])
                    , (line_start[0], line_start[1] - 5)
                    , cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 210), 2, cv2.LINE_AA)
        cv2.imshow("Frame", frame)


# Mouse callback function
def select_roi(event, x, y, flags, param):
    global roi_vertices, roi_selected, num_pressed
    if (event == cv2.EVENT_LBUTTONDOWN) and num_pressed <= max_vertices:
        num_pressed += 1
        roi_vertices.append((x, y))
        roi_selected = False

    elif event == cv2.EVENT_LBUTTONUP and num_pressed <= max_vertices:
        if roi_vertices[num_pressed - 1] != (x, y):
            num_pressed += 1
            print(num_pressed)
            roi_vertices.append((x, y))
            if (num_pressed == 2):
                angle = calculate_angle(roi_vertices[0][0], roi_vertices[0][1], roi_vertices[1][0], roi_vertices[1][1])
                if (angle > max_angle):
                    roi_vertices.remove(roi_vertices[1])
                    roi_vertices.remove(roi_vertices[0])
                    num_pressed -= 2
                print(angle)
            if (num_pressed == 4):
                angle = calculate_angle(roi_vertices[2][0], roi_vertices[2][1], roi_vertices[3][0], roi_vertices[3][1])
                if (angle > max_angle):
                    roi_vertices.remove(roi_vertices[3])
                    roi_vertices.remove(roi_vertices[2])
                    num_pressed -= 2
                print(angle)
        else:
            roi_vertices.remove(roi_vertices[num_pressed - 1])
            num_pressed -= 1
        if num_pressed == max_vertices:
            # Verify that the order of the vertices is correct, if not, swap them
            if roi_vertices[0][0] - roi_vertices[1][0] < 0 < roi_vertices[3][0] - roi_vertices[2][0]:
                roi_vertices[2], roi_vertices[3] = roi_vertices[3], roi_vertices[2]

        for i in range(len(roi_vertices)):
            print(roi_vertices[i])
        roi_selected = True
        # Draw the trapezoid on the frame
        cv2.polylines(frame, [np.array(roi_vertices)], isClosed=True, color=(0, 255, 0), thickness=2)
        cv2.putText(frame, 'ROI: {}'.format(roi_vertices), (roi_vertices[0][0], roi_vertices[0][1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 210), 2, cv2.LINE_AA)
        cv2.imshow('Video', frame)


# Add buttons
btn_normal = tk.Button(popup, text="Normal", command=select_normal)
btn_normal.pack()

btn_prohibited = tk.Button(popup, text="Prohibited", command=select_prohibited)
btn_prohibited.pack()

# Wait for button click event
# Asking the user to select the type of ROI
popup.wait_window()

# this is the path to the video folder
VIDEOS_DIR = os.path.join('.', 'videos')
# Open file dialog and get the selected file path
#video_path = filedialog.askopenfilename()

# make video path 127.0.0.1/8080
video_path = 'http://127.0.0.1:8080'

if not video_path:
    print("No file selected.")
    exit()
cap = cv2.VideoCapture(video_path)

video_name = os.path.basename(video_path).split('.')[0]
# Create a directory named 'ROI' if it doesn't exist
roi_dir = os.path.join('.', 'ROI')
os.makedirs(roi_dir, exist_ok=True)

# Set ROI file path based on selection
if selection == "prohibited":
    roi_file_path = os.path.join(roi_dir, f'ProhibitedROI_{video_name}.txt')
else:
    roi_file_path = os.path.join(roi_dir, f'ROI_{video_name}.txt')

# Set speed line file path
speed_line_path = os.path.join(roi_dir, f'SpeedLine_{video_name}.txt')

# Read the first frame
ret, frame = cap.read()
if not ret:
    print("Error reading video.")
    exit()

# Display the first frame to draw the ROI
cv2.imshow('Video', frame)
cv2.setMouseCallback('Video', select_roi)
# Wait for the user to select ROI
cv2.waitKey(0)
cv2.destroyAllWindows()
# Save ROI vertices to a file
if roi_selected:
    with open(roi_file_path, 'w') as file:
        file.write(','.join([f"{x},{y}" for x, y in roi_vertices]))
    if selection != "prohibited":
        # Draw the speed line on the frame
        line_start, line_end = draw_speedline(frame, roi_vertices)
        # Save line points in the speed line file
        if line_selected:
            with open(speed_line_path, 'w') as f:
                f.write(f"{line_start[0]},{line_start[1]},{line_end[0]},{line_end[1]}")
# Release resources
cap.release()
cv2.destroyAllWindows()
