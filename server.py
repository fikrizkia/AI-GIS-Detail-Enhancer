import os
import sys
import time
import zipfile
import urllib.request
import io
import subprocess
from math import gcd

# -----------------------------------------------------------------
# 1. AUTO-DEPENDENCY CHECK
# -----------------------------------------------------------------
def check_dependencies():
    missing_deps = []
    
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")
        
    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn")
        
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
        
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("pillow")
        
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
        
    if missing_deps:
        print(f"Installing missing backend dependencies: {missing_deps}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
            print("Dependencies installed successfully!")
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            sys.exit(1)

# Run dependency check
check_dependencies()

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import numpy as np
import cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import requests

# -----------------------------------------------------------------
# 2. FILE PATH CONTEXT
# -----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Move heavy binaries and models outside of the GIS folder (to prevent uploading to GitHub)
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".upscaler_cache")
MODELS_DIR = os.path.join(CACHE_DIR, "models")
BIN_DIR = os.path.join(CACHE_DIR, "bin")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(BIN_DIR, exist_ok=True)

app = FastAPI(title="AI GIS & Satellite Map Detail Upscaler")

# Mount GIS directory to serve images directly (e.g. /gis_files/image 6.png)
app.mount("/gis_files", StaticFiles(directory=BASE_DIR), name="gis_files")

# -----------------------------------------------------------------
# 3. DOWNLOAD & UTILITY LOGIC
# -----------------------------------------------------------------
OPENCV_MODELS = {
    "edsr": {
        2: "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x2.pb",
        3: "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x3.pb",
        4: "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x4.pb",
    },
    "fsrcnn": {
        2: "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x2.pb",
        3: "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x3.pb",
        4: "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x4.pb",
    }
}

REAL_ESRGAN_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"

def download_file(url, dest_path):
    """Downloads a file synchronously from a URL to a path"""
    print(f"Downloading: {url} -> {dest_path}")
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return False

def get_opencv_model(model_name, scale):
    """Retrieves or downloads the OpenCV model path"""
    model_filename = f"{model_name.upper()}_x{scale}.pb"
    model_path = os.path.join(MODELS_DIR, model_filename)
    if os.path.exists(model_path):
        return model_path
    
    url = OPENCV_MODELS[model_name][scale]
    if download_file(url, model_path):
        return model_path
    return None

def find_realesrgan_exe():
    """Recursively search for realesrgan-ncnn-vulkan.exe inside bin/"""
    for root, _, files in os.walk(BIN_DIR):
        if "realesrgan-ncnn-vulkan.exe" in files:
            return os.path.join(root, "realesrgan-ncnn-vulkan.exe")
    return None

def get_realesrgan():
    """Ensures Real-ESRGAN is downloaded and extracted"""
    exe_path = find_realesrgan_exe()
    if exe_path and os.path.exists(exe_path):
        return exe_path
        
    print("Real-ESRGAN binary not found. Downloading portable package...")
    zip_path = os.path.join(BIN_DIR, "realesrgan.zip")
    if download_file(REAL_ESRGAN_URL, zip_path):
        try:
            extract_dir = os.path.join(BIN_DIR, "realesrgan-ncnn-vulkan")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            os.remove(zip_path)
            
            new_exe_path = find_realesrgan_exe()
            if new_exe_path:
                return new_exe_path
        except Exception as e:
            print(f"Extraction failed: {e}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
    return None

# -----------------------------------------------------------------
# 4. UPSCALING LOGIC
# -----------------------------------------------------------------
def upscale_pillow(image, scale):
    w, h = image.size
    return image.resize((w * scale, h * scale), Image.Resampling.LANCZOS)

def upscale_opencv_tiled(image_pil, model_path, model_name, scale, tile_size=400, overlap=32):
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(model_path)
    sr.setModel(model_name.lower(), scale)
    
    img = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    H, W, C = img.shape
    
    out_img = np.zeros((H * scale, W * scale, C), dtype=np.uint8)
    stride = tile_size - overlap
    
    y_starts = list(range(0, H - overlap, stride))
    if not y_starts or y_starts[-1] + tile_size < H:
        y_starts.append(max(0, H - tile_size))
        
    x_starts = list(range(0, W - overlap, stride))
    if not x_starts or x_starts[-1] + tile_size < W:
        x_starts.append(max(0, W - tile_size))
        
    for y1 in y_starts:
        y2 = min(y1 + tile_size, H)
        for x1 in x_starts:
            x2 = min(x1 + tile_size, W)
            
            tile = img[y1:y2, x1:x2]
            upscaled_tile = sr.upsample(tile)
            
            crop_top = (overlap * scale) // 2 if y1 > 0 else 0
            crop_bottom = (overlap * scale) // 2 if y2 < H else 0
            crop_left = (overlap * scale) // 2 if x1 > 0 else 0
            crop_right = (overlap * scale) // 2 if x2 < W else 0
            
            out_y1 = y1 * scale + crop_top
            out_y2 = y2 * scale - crop_bottom
            out_x1 = x1 * scale + crop_left
            out_x2 = x2 * scale - crop_right
            
            tile_h, tile_w, _ = upscaled_tile.shape
            tile_y1 = crop_top
            tile_y2 = tile_h - crop_bottom
            tile_x1 = crop_left
            tile_x2 = tile_w - crop_right
            
            out_img[out_y1:out_y2, out_x1:out_x2] = upscaled_tile[tile_y1:tile_y2, tile_x1:tile_x2]
            
    out_img_rgb = cv2.cvtColor(out_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(out_img_rgb)

def upscale_realesrgan(image_pil, exe_path, scale, tile_size=200):
    temp_in = os.path.join(BASE_DIR, "temp_in.png")
    temp_out = os.path.join(BASE_DIR, "temp_out.png")
    
    image_pil.save(temp_in, format="PNG")
    model_name = "realesrgan-x4plus"
    
    cmd = [
        exe_path,
        "-i", temp_in,
        "-o", temp_out,
        "-s", str(scale),
        "-n", model_name,
        "-t", str(tile_size),
        "-f", "png"
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        if os.path.exists(temp_out):
            upscaled = Image.open(temp_out)
            upscaled.load()
            os.remove(temp_in)
            os.remove(temp_out)
            return upscaled
    except Exception as e:
        print(f"Real-ESRGAN execution error: {e}")
        
    if os.path.exists(temp_in):
        os.remove(temp_in)
    if os.path.exists(temp_out):
        os.remove(temp_out)
    return None

# -----------------------------------------------------------------
# 5. REST API ENDPOINTS
# -----------------------------------------------------------------
class UpscaleRequest(BaseModel):
    filename: str
    method: str
    scale: int
    tile_size: int
    overlap: int

@app.get("/", response_class=HTMLResponse)
def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/images")
def get_images():
    images = {}
    for f in os.listdir(BASE_DIR):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            if "upscaled" in f.lower() or "temp_" in f:
                continue
            path = os.path.join(BASE_DIR, f)
            try:
                with Image.open(path) as img:
                    w, h = img.size
                    g = gcd(w, h)
                    images[f] = {
                        "width": w,
                        "height": h,
                        "ratio": f"{w//g}:{h//g}",
                        "format": img.format,
                    }
            except Exception:
                pass
    return {"images": images}

@app.post("/api/upscale")
def post_upscale(req: UpscaleRequest):
    img_path = os.path.join(BASE_DIR, req.filename)
    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Target image not found.")
        
    # Load input
    try:
        input_img = Image.open(img_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open image: {e}")
        
    start_time = time.time()
    upscaled = None
    
    # Execute method
    if req.method == "realesrgan":
        exe_path = get_realesrgan()
        if not exe_path:
            raise HTTPException(status_code=500, detail="Failed to initialize Real-ESRGAN binary.")
        upscaled = upscale_realesrgan(input_img, exe_path, req.scale, req.tile_size)
        
    elif req.method in ["edsr", "fsrcnn"]:
        model_path = get_opencv_model(req.method, req.scale)
        if not model_path:
            raise HTTPException(status_code=500, detail=f"Failed to load OpenCV {req.method.upper()} model.")
        upscaled = upscale_opencv_tiled(input_img, model_path, req.method, req.scale, req.tile_size, req.overlap)
        
    elif req.method == "lanczos":
        upscaled = upscale_pillow(input_img, req.scale)
        
    else:
        raise HTTPException(status_code=400, detail="Unknown upscaling method.")
        
    if upscaled is None:
        raise HTTPException(status_code=500, detail="Upscaling algorithm failed.")
        
    # Save output as PNG in GIS folder
    elapsed = time.time() - start_time
    clean_name = os.path.splitext(req.filename)[0]
    out_filename = f"{clean_name}_upscaled_{req.scale}x_{req.method}.png"
    out_path = os.path.join(BASE_DIR, out_filename)
    
    upscaled.save(out_path, format="PNG")
    
    return {
        "success": True,
        "output_filename": out_filename,
        "output_url": f"/gis_files/{out_filename}",
        "new_width": upscaled.width,
        "new_height": upscaled.height,
        "elapsed": elapsed
    }

@app.get("/api/crop")
def get_crop(filename: str, upscale: bool, scale: int = 4):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        with Image.open(path) as img:
            w, h = img.size
            cx, cy = w // 2, h // 2
            crop_size = 300
            if upscale:
                crop_size = 300 * scale
                
            box = (
                max(0, cx - crop_size // 2),
                max(0, cy - crop_size // 2),
                min(w, cx + crop_size // 2),
                min(h, cy + crop_size // 2)
            )
            cropped = img.crop(box)
            
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cropping failed: {e}")

# -----------------------------------------------------------------
# 6. SERVER RUNNER
# -----------------------------------------------------------------
if __name__ == "__main__":
    print("Starting High-Performance Local Upscaling Server on http://localhost:8050 ...")
    uvicorn.run(app, host="127.0.0.1", port=8050)
