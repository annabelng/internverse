from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import subprocess
import os
import time
from pathlib import Path

app = FastAPI()

# Define the input model for the API
class VideoInput(BaseModel):
    video_path: str

# Paths for scripts and output
# CHANGE YOUR OWN PATHS HERE
COLMAP_SCRIPT = "/Users/t-annabelng/Projects/instant-ngp/scripts/colmap2nerf.py"
GUI_SCRIPT = "/Users/t-annabelng/Projects/instant-ngp/scripts/train_gui.py"
OUTPUT_VIDEO_PATH = "/Users/t-annabelng/Projects/instant-ngp/output/final_video.mp4"
UPLOAD_DIR = "/Users/t-annabelng/Projects/instant-ngp/uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process-video/")
async def process_video(file: UploadFile = File(...)):
    # Step 1: Save the uploaded video to the upload directory
    video_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # Step 2: Run colmap2nerf.py
    try:
        colmap_command = [
            "python3", COLMAP_SCRIPT,
            "--video_in", video_path,
            "--out", UPLOAD_DIR,
            "--run_colmap",
            "--overwrite"
        ]
        subprocess.run(colmap_command, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error running colmap2nerf.py: {e}")

    # Step 3: Dummy statement for GUI training
    try:
        print("GUI training process...")
        # Here you would normally run the GUI training script but we had to run it locally
        # due to only one team member having the gpu setup and weren't able to connect it to the route
        gui_command = [
            "python3", GUI_SCRIPT,
            "--images", os.path.join(UPLOAD_DIR, "images"),
        ]
        time.sleep(10)  # Simulate a delay for the training process
        print("GUI training complete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating training GUI: {e}")

    # Step 4: Wait for the output video to be saved and render
    timeout = 10  # 1 hour timeout
    start_time = time.time()
    while not os.path.exists(OUTPUT_VIDEO_PATH):
        if time.time() - start_time > timeout:
            raise HTTPException(status_code=500, detail="Training GUI timed out.")
        time.sleep(5)  # Check every 5 seconds

    return {"message": "Processing complete. Video is ready.", "video_path": OUTPUT_VIDEO_PATH}

@app.get("/get-video/")
async def get_video():
    # Step 5: Serve the processed video
    if not os.path.exists(OUTPUT_VIDEO_PATH):
        raise HTTPException(status_code=404, detail="Processed video not found.")
    return {"video_url": f"/static/{Path(OUTPUT_VIDEO_PATH).name}"}