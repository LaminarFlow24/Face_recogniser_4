import streamlit as st
import cv2
import numpy as np
import joblib
from PIL import Image
from face_recognition import preprocessing
from huggingface_hub import hf_hub_download
import os
import shutil

# Download the model from Hugging Face Hub
def download_model_from_huggingface():
    repo_id = "your-username/your-repo"  # Replace with your Hugging Face repository
    filename = "face_recogniser.pkl"  # Replace with your model filename

    st.info("Downloading model from Hugging Face...")
    try:
        model_path = hf_hub_download(repo_id=repo_id, filename=filename, cache_dir="model_cache")
        st.success("Model downloaded successfully!")
        return model_path
    except Exception as e:
        st.error(f"Error downloading model: {e}")
        raise

# Load the model
if not os.path.exists('face_recogniser.pkl'):
    try:
        model_path = download_model_from_huggingface()
        st.write(f"Downloaded model path: {model_path}")

        # Move the model to the current working directory
        destination_path = os.path.join(os.getcwd(), 'face_recogniser.pkl')
        shutil.move(model_path, destination_path)
        st.success("Model downloaded and moved successfully!")

        # Verify the file move
        if not os.path.exists(destination_path):
            st.error(f"Model file not found at {destination_path} after moving.")
            st.stop()
    except Exception as e:
        st.error(f"Failed to download or move the model: {e}")
        st.stop()

# Verify the model file
if not os.path.exists('face_recogniser.pkl'):
    st.error("Model file 'face_recogniser.pkl' not found. Please ensure the file exists or the Hugging Face repo is configured correctly.")
    st.stop()

face_recogniser = joblib.load('face_recogniser.pkl')
preprocess = preprocessing.ExifOrientationNormalize()

# Streamlit app
st.title("Live Face Recognition")
st.write("This app performs face recognition on live webcam feed.")

# Helper function to process and predict faces
def process_frame(frame):
    # Convert frame to PIL Image for preprocessing
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    pil_img = preprocess(pil_img)
    pil_img = pil_img.convert('RGB')

    # Predict faces
    faces = face_recogniser(pil_img)

    # Annotate the frame with bounding boxes and labels
    for face in faces:
        bb = face.bb._asdict()
        top_left = (int(bb['left']), int(bb['top']))
        bottom_right = (int(bb['right']), int(bb['bottom']))
        label = face.top_prediction.label
        confidence = face.top_prediction.confidence

        # Draw bounding box and label on the frame
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(
            frame, f"{label} ({confidence:.2f})", (top_left[0], top_left[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1
        )

    return frame

# Start the webcam feed
run = st.checkbox('Start Webcam')
frame_placeholder = st.empty()

if run:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Unable to access the webcam. Make sure it is connected and try again.")
    else:
        st.info("Press 'q' to stop the webcam.")

    while run:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to read frame from webcam.")
            break

        # Process the frame for face recognition
        annotated_frame = process_frame(frame)

        # Display the annotated frame in Streamlit
        frame_placeholder.image(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB), channels="RGB")

        # Stop the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
