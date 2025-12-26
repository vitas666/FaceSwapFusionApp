import streamlit as st
import os
import subprocess
import sys
from PIL import Image

# --- CONFIGURATION ---
TEMP_DIR = "temp_workspace"
OUTPUT_DIR = "output_workspace"

# Create directories if they don't exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(page_title="Local Face Swap", layout="centered")

st.title("Local Face Swap")
st.markdown("Powered by FaceFusion & CoreML")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACEFUSION_SCRIPT = os.path.join(BASE_DIR, "faceSwap.py")

# --- HELPER FUNCTION: CALL FACEFUSION ---
def find_latest_image(directory):
    images = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    if not images:
        return None
    return max(images, key=os.path.getmtime)

def run_facefusion(source_path, target_path, output_path):
    """
    Constructs the command to run FaceFusion in headless mode.
    Adjust 'execution-providers' to 'cpu' if CoreML fails, 
    but 'coreml' is best for M4.
    """
    
    # Absolute paths are safer for subprocess calls
    abs_source = os.path.abspath(source_path)
    abs_target = os.path.abspath(target_path)
    abs_output = os.path.abspath(output_path)
    
    # The command list
    command = [
        sys.executable, FACEFUSION_SCRIPT, 
        "--headless", 
        "--source", abs_source, 
        "--target", abs_target, 
        "--output", abs_output,
        "--execution-providers", "coreml",  # Leveraging your Neural Engine
        "--frame-processors", "face_swapper"
    ]
    
    # Run the command and capture output (for debugging)
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

# --- UI: UPLOAD STEP ---
col1, col2 = st.columns(2)

source_path = None
target_path = None

with col1:
    st.subheader("1. Source Face")
    source_file = st.file_uploader("Face to use", type=["jpg", "png", "jpeg"], key="src")
    if source_file:
        st.image(source_file, width=200)
        source_path = os.path.join(TEMP_DIR, "source.jpg")
        with open(source_path, "wb") as f:
            f.write(source_file.getbuffer())

with col2:
    st.subheader("2. Target Image")
    target_file = st.file_uploader("Image to replace", type=["jpg", "png", "jpeg"], key="tgt")
    if target_file:
        st.image(target_file, width=200)
        target_path = os.path.join(TEMP_DIR, "target.jpg")
        with open(target_path, "wb") as f:
            f.write(target_file.getbuffer())

# --- UI: PROCESSING STEP ---
st.divider()

if source_path and target_path:
    # Generate a unique output name or overwrite a standard one
    final_output_dir = os.path.abspath(OUTPUT_DIR)

    if st.button("Run Swap on Neural Engine", type="primary", use_container_width=True):
        
        with st.status("Processing...", expanded=True) as status:
            st.write("Initializing FaceFusion...")
            st.write("Loading CoreML Providers...")
            
            # Step 3: Call the API
            success, log = run_facefusion(source_path, target_path, final_output_dir)
            
            if success:
                status.update(label="Swap Complete!", state="complete", expanded=False)
                
                # Step 4: Show Result & Download
                st.subheader("Result")
                result_image = find_latest_image(OUTPUT_DIR)

                if not result_image:
                    st.error("FaceFusion finished but no output image was found.")
                    st.code(log)
                    st.stop()

                st.subheader("Result")
                st.image(result_image, caption="Swapped Result")

                with open(result_image, "rb") as file:
                    st.download_button(
                        label="Download Image",
                        data=file,
                        file_name=os.path.basename(result_image),
                        mime="image/jpeg"
                    )
            else:
                status.update(label="Error Occurred", state="error")
                st.error("FaceFusion failed to run.")
                with st.expander("See Error Log"):
                    st.code(log)
else:
    st.info("Upload both images to activate the swap button.")