import math
import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_js_eval import streamlit_js_eval

def marker(point, to_mark, another):
    if list(point) not in st.session_state[to_mark] and list(point) not in st.session_state[another]:
        st.session_state[to_mark].append([point[0], point[1]])
        st.experimental_rerun()

def get_distance(pos1, pos2):
    return math.dist(pos1, pos2)

def stage3():
    if len(st.session_state['pos']) > 1:
        for i in range(len(st.session_state['pos']) - 1):
            st.session_state['heightinpixel'].append(get_distance(st.session_state['pos'][i], st.session_state['pos'][i + 1]))
    
    st.session_state['heightsum'] = sum(st.session_state['heightinpixel'])

    if st.session_state['refvalue'] != 0 and st.session_state['refpos']:
        st.session_state['refvalue'] = float(st.session_state['refvalue'])
        st.session_state.stage = 3
        st.session_state['img'] = imgraw
    elif not st.session_state['refpos']:
        st.text("Please mark the locations.")
    elif st.session_state['refvalue'] == 0:
        st.text(f"Please input the height of the reference object in {st.session_state['unit']}.")
    elif not st.session_state['refpos']:
        st.text("Please mark the positions of the reference object.")

def undo():
    if st.session_state['currentmark'] == 'person' and st.session_state["pos"]:
        st.session_state["pos"].pop()
    elif st.session_state['currentmark'] == 'object' and st.session_state["refpos"]:
        st.session_state["refpos"].pop()
    st.experimental_rerun()

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = 0

st.session_state.setdefault('pos', [])
st.session_state.setdefault('refpos', [])
st.session_state.setdefault('refinpixel', [])
st.session_state.setdefault('refsum', 0)
st.session_state.setdefault('img', None)
st.session_state.setdefault('heightinpixel', [])
st.session_state.setdefault('heightsum', 0)
st.session_state.setdefault('currentmark', 'person')
st.session_state.setdefault('unit', 'cm')
st.session_state.setdefault('display_unit', 'cm')

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
            imgraw = Image.open(uploaded_file)
            imgraw = imgraw.resize((600, 600))
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
        col1, col2, col3, col4 = st.columns(4)

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
            if st.button("Reset"):
                streamlit_js_eval(js_expressions="parent.window.location.reload()") # F5

        st.text("Currently working on: " + st.session_state['currentmark'])

        # Draw circles
        for pos in st.session_state["pos"]:
            circle = [pos[0] - 3, pos[1] - 3, pos[0] + 3, pos[1] + 3]
            draw.ellipse(circle, fill="red")

        for refpos in st.session_state['refpos']:
            circle = [refpos[0] - 3, refpos[1] - 3, refpos[0] + 3, refpos[1] + 3]
            draw.ellipse(circle, fill=(0, 0, 255))

        # Draw lines
        if len(st.session_state["pos"]) > 1:
            for i in range(len(st.session_state["pos"]) - 1):
                draw.line([st.session_state['pos'][i][0], st.session_state['pos'][i][1], st.session_state['pos'][i + 1][0], st.session_state['pos'][i + 1][1]], fill="red", width=0)

        if len(st.session_state['refpos']) > 1:
            for i in range(len(st.session_state['refpos']) - 1):
                draw.line([st.session_state['refpos'][i][0], st.session_state['refpos'][i][1], st.session_state['refpos'][i + 1][0], st.session_state['refpos'][i + 1][1]], fill=(0, 0, 255), width=0)

        value = streamlit_image_coordinates(imgraw, key="pil")

        if value is not None:
            point = value["x"], value["y"]
            if st.session_state['currentmark'] == 'person':
                marker(point, 'pos', 'refpos')
            elif st.session_state['currentmark'] == 'object':
                marker(point, 'refpos', 'pos')        

        unit_option = st.selectbox("Select unit for reference object height", ("cm", "inch"))
        st.session_state['unit'] = unit_option

        if unit_option == "cm":
            st.session_state['refvalue'] = st.number_input("Input height of the reference object (cm)")
        elif unit_option == "inch":
            st.session_state['refvalue'] = st.number_input("Input height of the reference object (inch)")

        display_unit_option = st.selectbox("Select display unit", ("cm", "feet"))
        st.session_state['display_unit'] = display_unit_option

        st.button("Continue", on_click=stage3)

if st.session_state.stage == 3:
    img = st.session_state['img']
    for i in range(len(st.session_state['refpos']) - 1):
        st.session_state['refinpixel'].append(get_distance(st.session_state['refpos'][i], st.session_state['refpos'][i + 1]))

    st.session_state['refsum'] = sum(st.session_state['refinpixel'])

    # Calculation
    pixel_per_unit = st.session_state['refvalue'] / st.session_state['refsum']
    height_estimated = st.session_state['heightsum'] * pixel_per_unit

    if st.session_state['display_unit'] == "feet":
        height_in_feet = height_estimated / 30.48
        feet = int(height_in_feet)
        inches = (height_in_feet - feet) * 12
        st.text(f"The estimated height is {feet} feet {inches:.2f} inches")
    else:
        st.text(f"The estimated height is {int(height_estimated)} cm")

    st.image(img)
    if st.button("Back to main page"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
