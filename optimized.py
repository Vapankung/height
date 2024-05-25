import math
import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_js_eval import streamlit_js_eval

def marker(point, to_mark, another):
    if list(point) not in st.session_state[to_mark] and list(point) not in st.session_state[another]:
        if to_mark == 'ref_positions':
            if not st.session_state[to_mark] or len(st.session_state[to_mark][-1]) >= 2:
                st.session_state[to_mark].append([])
            st.session_state[to_mark][-1].append([point[0], point[1]])
        else:
            st.session_state[to_mark].append([point[0], point[1]])
        # Only rerun when necessary
        if to_mark == 'ref_positions' and len(st.session_state[to_mark][-1]) == 1:
            st.rerun()

def get_distance(pos1, pos2):
    return math.dist(pos1, pos2)

def calculate_average_pixel_per_unit(ref_values, ref_positions):
    total_pixel_distance = 0
    total_ref_value = 0
    
    for i in range(len(ref_positions)):
        ref_distance = sum([get_distance(ref_positions[i][j], ref_positions[i][j + 1]) for j in range(len(ref_positions[i]) - 1)])
        total_pixel_distance += ref_distance
        total_ref_value += ref_values[i]
    
    return total_ref_value / total_pixel_distance

def stage3():
    if len(st.session_state['pos']) > 1:
        st.session_state['heightinpixel'] = [
            get_distance(st.session_state['pos'][i], st.session_state['pos'][i + 1])
            for i in range(len(st.session_state['pos']) - 1)
        ]
        st.session_state['heightsum'] = sum(st.session_state['heightinpixel'])

    if st.session_state['ref_values'] and st.session_state['ref_positions']:
        avg_pixel_per_unit = calculate_average_pixel_per_unit(st.session_state['ref_values'], st.session_state['ref_positions'])
        height_estimated = st.session_state['heightsum'] * avg_pixel_per_unit

        st.image(st.session_state['img'])
        if st.session_state['display_unit'] == "feet":
            height_in_feet = height_estimated / 30.48
            feet = int(height_in_feet)
            inches = (height_in_feet - feet) * 12
            st.text(f"The estimated height is {feet} feet {inches:.2f} inches")
        else:
            st.text(f"The estimated height is {int(height_estimated)} cm")
    else:
        st.text("Please mark the reference objects and input their heights.")

    if st.button("Back to main page"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

def undo():
    if st.session_state['currentmark'] == 'person' and st.session_state["pos"]:
        st.session_state["pos"].pop()
    elif st.session_state['currentmark'] == 'object' and st.session_state["ref_positions"]:
        if st.session_state['ref_positions'][-1]:
            st.session_state['ref_positions'][-1].pop()
        if not st.session_state['ref_positions'][-1]:
            st.session_state['ref_positions'].pop()
    st.rerun()

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = 0

session_defaults = {
    'pos': [],
    'ref_positions': [],
    'ref_values': [],
    'refinpixel': [],
    'refsum': 0,
    'img': None,
    'heightinpixel': [],
    'heightsum': 0,
    'currentmark': 'person',
    'unit': 'cm',
    'display_unit': 'cm'
}

for key, value in session_defaults.items():
    st.session_state.setdefault(key, value)

# Add JavaScript to listen for Ctrl + Z and call the undo function
undo_js = """
document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.key === 'z') {
        window.streamlitApi.runMethod('undo')
    }
});
"""
streamlit_js_eval(js_expressions=undo_js)

st.title("Height Estimating")

if st.session_state.stage == 0:
    option = st.selectbox("Choose image source", ("Upload an image", "Capture from webcam"))

    if option == "Upload an image":
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            imgraw = Image.open(uploaded_file).resize((600, 600))
            st.session_state['img'] = np.array(imgraw)
    elif option == "Capture from webcam":
        try:
            camera_image = st.camera_input("Take a picture")
            if camera_image is not None:
                imgraw = Image.open(camera_image)
                st.session_state['img'] = np.array(imgraw)
            else:
                st.warning("Please capture an image using the webcam.")
        except Exception as e:
            st.error(f"Error accessing the camera: {e}")

    if st.session_state['img'] is not None:
        imgraw = Image.fromarray(st.session_state['img'])
        st.session_state['img'] = np.array(imgraw)
        col1, col2, col3, col4, col5 = st.columns(5)

        st.text("Click to mark positions of your body parts")
        draw = ImageDraw.Draw(imgraw)

        with col1:
            if st.button("Undo"):
                undo()
        with col2:
            if st.button("Person"):
                st.session_state["currentmark"] = 'person'
        with col3:
            if st.button("Object"):
                st.session_state['currentmark'] = 'object'
        with col4:
            if st.button("Add Another Reference Object"):
                st.session_state['ref_positions'].append([])
        with col5:
            if st.button("Reset"):
                streamlit_js_eval(js_expressions="parent.window.location.reload()") # F5

        st.text("Currently working on: " + st.session_state['currentmark'])

        # Draw circles
        for pos in st.session_state["pos"]:
            circle = [pos[0] - 3, pos[1] - 3, pos[0] + 3, pos[1] + 3]
            draw.ellipse(circle, fill="red")

        for ref_group in st.session_state['ref_positions']:
            for refpos in ref_group:
                circle = [refpos[0] - 3, refpos[1] - 3, refpos[0] + 3, refpos[1] + 3]
                draw.ellipse(circle, fill=(0, 0, 255))

        # Draw lines
        if len(st.session_state["pos"]) > 1:
            for i in range(len(st.session_state["pos"]) - 1):
                draw.line(
                    [st.session_state['pos'][i][0], st.session_state['pos'][i][1],
                     st.session_state['pos'][i + 1][0], st.session_state['pos'][i + 1][1]], fill="red", width=0)

        for ref_group in st.session_state['ref_positions']:
            if len(ref_group) > 1:
                for i in range(len(ref_group) - 1):
                    draw.line(
                        [ref_group[i][0], ref_group[i][1],
                         ref_group[i + 1][0], ref_group[i + 1][1]], fill=(0, 0, 255), width=0)

        value = streamlit_image_coordinates(imgraw, key="pil")

        if value is not None:
            point = value["x"], value["y"]
            if st.session_state['currentmark'] == 'person':
                marker(point, 'pos', 'ref_positions')
            elif st.session_state['currentmark'] == 'object':
                marker(point, 'ref_positions', 'pos')        

        unit_option = st.selectbox("Select unit for reference object height", ("cm", "inch"))
        st.session_state['unit'] = unit_option

        ref_value_key = f"ref_value_{len(st.session_state['ref_values'])}"
        ref_height = st.number_input(f"Input height of the reference object ({unit_option})", key=ref_value_key)
        if unit_option == "inch":
            ref_height *= 2.54  # Convert inches to cm
        st.session_state['ref_values'].append(ref_height)

        display_unit_option = st.selectbox("Select display unit", ("cm", "feet"))
        st.session_state['display_unit'] = display_unit_option

        st.button("Continue", on_click=stage3)

if st.session_state.stage == 3:
    img = st.session_state['img']
    for i in range(len(st.session_state['ref_positions'])):
        for j in range(len(st.session_state['ref_positions'][i]) - 1):
            st.session_state['refinpixel'].append(get_distance(st.session_state['ref_positions'][i][j], st.session_state['ref_positions'][i][j + 1]))

    st.session_state['refsum'] = sum(st.session_state['refinpixel'])

    avg_pixel_per_unit = calculate_average_pixel_per_unit(st.session_state['ref_values'], st.session_state['ref_positions'])
    height_estimated = st.session_state['heightsum'] * avg_pixel_per_unit

    st.image(img)
    if st.session_state['display_unit'] == "feet":
        height_in_feet = height_estimated / 30.48
        feet = int(height_in_feet)
        inches = (height_in_feet - feet) * 12
        st.text(f"The estimated height is {feet} feet {inches:.2f} inches")
    else:
        st.text(f"The estimated height is {int(height_estimated)} cm")

    if st.button("Back to main page"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
