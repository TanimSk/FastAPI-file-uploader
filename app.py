from fastapi import FastAPI, File, UploadFile, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from io import BytesIO
from PIL import Image
import ffmpeg
import os
import shutil
import tempfile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from dotenv import load_dotenv
import uuid


load_dotenv()
API_KEY = os.getenv("KEY")
BASE_URL = os.getenv("BASE_URL")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def compress_image(image_bytes: bytes, output_path: str, quality: int):
    """Compress an image and save it to disk."""
    img = Image.open(BytesIO(image_bytes))
    img.save(output_path, format="JPEG", quality=quality)


def compress_video(video_bytes: bytes, output_path: str, bitrate: str):
    """Compress a video and save it to disk."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
        temp_input.write(video_bytes)
        temp_input.flush()

        ffmpeg.input(temp_input.name).output(output_path, video_bitrate=bitrate).run(
            overwrite_output=True
        )

        os.unlink(temp_input.name)  # Delete temp input file after compression


def background_compress_image(input_path: str, output_path: str, quality: int):
    """Reads file from disk and compresses it in the background."""
    with open(input_path, "rb") as f:
        image_bytes = f.read()
    compress_image(image_bytes, output_path, quality)


def background_compress_video(input_path: str, output_path: str, bitrate: str):
    """Reads file from disk and compresses it in the background."""
    with open(input_path, "rb") as f:
        video_bytes = f.read()
    compress_video(video_bytes, output_path, bitrate)


@app.get("/", response_class=HTMLResponse)
async def serve_html():
    """Serve the HTML file for the upload form."""
    return FileResponse("static/index.html")


@app.post("/upload/")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    compression_level: int = Query(
        None,
        description="Compression level (1-100 for images, lower is more compressed).",
    ),
    path: str = Query(
        None,
        description="Path to store the file in (relative to the uploads directory).",
    ),
    key: str = Query(
        None,
        description="API key",
    ),
):
    # Validate API Key
    if key != API_KEY:
        return Response(content="Invalid API Key!", media_type="text/plain", status_code=403)
    
    
    """Upload a file and store it, with optional compression in the background."""
    folder_path = os.path.join(UPLOAD_DIR, path) if path else UPLOAD_DIR
    os.makedirs(folder_path, exist_ok=True)  # Ensure the directory exists

    file_path = os.path.join(folder_path, f"{uuid.uuid4()}_{file.filename}")
    await file.seek(0)

    # Save file immediately
    with open(file_path, 'wb') as f:
        while contents := await file.read(1024 * 1024):
            if contents:
                f.write(contents)
            else:
                break  # Stop when no more content is available


    response_data = {
        "filename": file.filename,
        "stored_path": f"{BASE_URL}/{file_path}",
        "compression_started": False,
    }

    # If compression is enabled, process in the background
    if compression_level is not None and file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mkv")):
        compressed_path = os.path.join(folder_path, f"compressed_{uuid.uuid4()}{file.filename}")

        if file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            background_tasks.add_task(
                background_compress_image, file_path, compressed_path, compression_level
            )
        elif file.filename.lower().endswith((".mp4", ".avi", ".mkv")):
            video_bitrate = f"{int(compression_level * 10)}k"
            background_tasks.add_task(
                background_compress_video, file_path, compressed_path, video_bitrate
            )

        response_data["compression_started"] = True
        response_data["compressed_path"] = f"{BASE_URL}/{compressed_path}"

    return response_data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
