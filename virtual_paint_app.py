import mediapipe as mp
import cv2
import numpy as np
import time

# Constants
ml = 150
max_x, max_y = 300 + ml, 50
curr_tool = "select tool"
time_init = True
rad = 40
var_inits = False
thick = 4
prevx, prevy = 0, 0
keyboard_open = False
typed_text = ""

# Global variables for keyboard handling
key_press_time = 0
KEY_PRESS_DELAY = 3.0  # Adjust this value as needed
backspace_pressed_time = 0

# Get tool function
def getTool(x):
    if x < 50 + ml:
        return "line"
    elif x < 100 + ml:
        return "rectangle"
    elif x < 150 + ml:
        return "draw"
    elif x < 200 + ml:
        return "circle"
    elif x < 250 + ml:
        return "erase"
    elif x < 300 + ml:
        return "keyboard"
    else:
        return "no tool"

# Check if index is raised
def index_raised(yi, y9):
    if (y9 - yi) > 40:
        return True
    return False

canvas = np.ones((480, 640, 3), dtype="uint8") * 255
hands = mp.solutions.hands
hand_landmark = hands.Hands(min_detection_confidence=0.6, min_tracking_confidence=0.6, max_num_hands=1)
draw = mp.solutions.drawing_utils

# Drawing tools
tools = cv2.imread("tools1.jpeg")
tools = tools.astype('uint8')

mask = np.ones((480, 640), dtype="uint8") * 255

# Keyboard layout
keys = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M'],
    ['Space', 'Backspace']
]

cap = cv2.VideoCapture(0)

def draw_keyboard(frm):
    global keys
    start_x, start_y = 10, 60
    key_width, key_height = 40, 40
    for row in keys:
        for key in row:
            cv2.rectangle(frm, (start_x, start_y), (start_x + key_width, start_y + key_height), (0, 255, 0), 2)
            cv2.putText(frm, key, (start_x + 10, start_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            start_x += key_width + 10
        start_x = 10
        start_y += key_height + 10

def draw_canvas_with_text(canvas, typed_text):
    canvas[:] = 255  # Clear the canvas
    cv2.putText(canvas, typed_text, (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

def handle_key_press(x, y):
    global keys, typed_text, key_press_time, backspace_pressed_time
    start_x, start_y = 10, 60
    key_width, key_height = 40, 40
    current_time = time.time()

    for row_idx, row in enumerate(keys):
        for col_idx, key in enumerate(row):
            key_x = start_x + col_idx * (key_width + 10)
            key_y = start_y + row_idx * (key_height + 10)

            if key_x <= x <= key_x + key_width and key_y <= y <= key_y + key_height:
                if key == 'Space':
                    typed_text += ' '
                elif key == 'Backspace':
                    if current_time - backspace_pressed_time > KEY_PRESS_DELAY:
                        typed_text = typed_text[:-1]
                        backspace_pressed_time = current_time
                else:
                    # Check if enough time has passed since last key press
                    if current_time - key_press_time > KEY_PRESS_DELAY:
                        typed_text += key
                        key_press_time = current_time
                return

while True:
	_, frm = cap.read()
	frm = cv2.flip(frm, 1)

	rgb = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB)

	op = hand_landmark.process(rgb)
	if keyboard_open:
		draw_keyboard(frm)

	tools_resized = cv2.resize(tools, (300, 50))
	frm[0:50, ml:300 + ml] = tools_resized

	if op.multi_hand_landmarks:
		for i in op.multi_hand_landmarks:
			draw.draw_landmarks(frm, i, hands.HAND_CONNECTIONS)
			x, y = int(i.landmark[8].x*640), int(i.landmark[8].y*480)

			if x < max_x and y < max_y and x > ml:
				if time_init:
					ctime = time.time()
					time_init = False
				ptime = time.time()

				cv2.circle(frm, (x, y), rad, (0,255,255), 2)
				rad -= 1

				if (ptime - ctime) > 0.8:
					curr_tool = getTool(x)
					print("your current tool set to : ", curr_tool)
					time_init = True
					rad = 40
					if curr_tool == "keyboard":
						keyboard_open = not keyboard_open

			else:
				time_init = True
				rad = 40

			if curr_tool == "keyboard" and keyboard_open:
				handle_key_press(x,y)
				draw_canvas_with_text(canvas, typed_text)

			if curr_tool == "draw":
				xi, yi = int(i.landmark[12].x*640), int(i.landmark[12].y*480)
				y9  = int(i.landmark[9].y*480)

				if index_raised(yi, y9):
					cv2.line(mask, (prevx, prevy), (x, y), 0, thick)
					cv2.line(canvas, (prevx, prevy), (x, y), 0, thick)
					prevx, prevy = x, y

				else:
					prevx = x
					prevy = y



			elif curr_tool == "line":
				xi, yi = int(i.landmark[12].x*640), int(i.landmark[12].y*480)
				y9  = int(i.landmark[9].y*480)

				if index_raised(yi, y9):
					if not(var_inits):
						xii, yii = x, y
						var_inits = True

					cv2.line(frm, (xii, yii), (x, y), (50,152,255), thick)

				else:
					if var_inits:
						cv2.line(mask, (xii, yii), (x, y), 0, thick)
						cv2.line(canvas, (xii, yii), (x, y), 0, thick)
						var_inits = False

			elif curr_tool == "rectangle":
				xi, yi = int(i.landmark[12].x*640), int(i.landmark[12].y*480)
				y9  = int(i.landmark[9].y*480)

				if index_raised(yi, y9):
					if not(var_inits):
						xii, yii = x, y
						var_inits = True

					cv2.rectangle(frm, (xii, yii), (x, y), (0,255,255), thick)

				else:
					if var_inits:
						cv2.rectangle(mask, (xii, yii), (x, y), 0, thick)
						cv2.rectangle(canvas, (xii, yii), (x, y), 0, thick)
						var_inits = False

			elif curr_tool == "circle":
				xi, yi = int(i.landmark[12].x*640), int(i.landmark[12].y*480)
				y9  = int(i.landmark[9].y*480)

				if index_raised(yi, y9):
					if not(var_inits):
						xii, yii = x, y
						var_inits = True

					cv2.circle(frm, (xii, yii), int(((xii-x)**2 + (yii-y)**2)**0.5), (255,255,0), thick)

				else:
					if var_inits:
						cv2.circle(mask, (xii, yii), int(((xii-x)**2 + (yii-y)**2)**0.5), (0,255,0), thick)
						cv2.circle(canvas, (xii, yii), int(((xii-x)**2 + (yii-y)**2)**0.5), (0,255,0), thick)
						var_inits = False

			elif curr_tool == "erase":
				xi, yi = int(i.landmark[12].x*640), int(i.landmark[12].y*480)
				y9  = int(i.landmark[9].y*480)

				if index_raised(yi, y9):
					cv2.circle(mask, (x, y), 30, (255,255,255), -1)
					cv2.circle(canvas, (x, y), 30, (255, 255, 255), -1)
					
	cv2.putText(canvas, typed_text, (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
	op = cv2.bitwise_and(frm, frm, mask=mask)
	frm[:, :, 1] = op[:, :, 1]
	frm[:, :, 2] = op[:, :, 2]
	frm[:max_y, ml:max_x] = cv2.addWeighted(frm[:max_y, ml:max_x], 0.3, tools_resized, 0.7, 0)
	cv2.putText(frm, curr_tool, (270 + ml, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
	cv2.imshow("camera", frm)
	cv2.imshow("paint app", canvas)
	if cv2.waitKey(1) == 27:
		cv2.destroyAllWindows()
		cap.release()
		break
