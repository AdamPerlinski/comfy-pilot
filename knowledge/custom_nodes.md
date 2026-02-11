---
id: custom_nodes
title: Custom Nodes Guide
keywords: [custom nodes, ComfyUI Manager, AnimateDiff, VideoHelperSuite, Impact Pack, ControlNet, IPAdapter, InstantID, upscale, WAN, SVI, installation, ReActor, face, KJNodes, rgthree]
category: custom_nodes
priority: low
---

## CUSTOM NODE DETECTION

### How to Check if a Node Pack is Installed

**By Node Availability:**
When building a workflow, check if key nodes exist:
- If node not found → suggest installation
- Provide installation instructions

**Common Node → Pack Mapping:**

| If you see this node... | Pack is installed |
|------------------------|-------------------|
| ADE_AnimateDiffLoaderWithContext | ComfyUI-AnimateDiff-Evolved |
| VHS_VideoCombine | ComfyUI-VideoHelperSuite |
| IPAdapterApply | ComfyUI_IPAdapter_plus |
| ControlNetApplyAdvanced | Built-in (no pack needed) |
| UltimateSDUpscale | ComfyUI_UltimateSDUpscale |
| DetailerForEach | ComfyUI-Impact-Pack |
| WAS_Image_Save | WAS_Node_Suite |
| KSampler Efficient | efficiency-nodes-comfyui |
| SVI_FrameInterpolation | ComfyUI-SVI |
| WAN_Sampler | ComfyUI-WAN |

### When to Suggest Custom Nodes

**Always suggest if task requires:**
- Video generation → AnimateDiff-Evolved, VideoHelperSuite
- Face fixing → Impact-Pack, ReActor
- Style transfer → IPAdapter_plus
- Large images → UltimateSDUpscale
- Advanced upscaling → Tiled-Diffusion
- WAN 2.2 features → ComfyUI-WAN
- Frame interpolation → ComfyUI-SVI

### How to Recommend Installation

```
For [TASK], you'll need these custom nodes:

1. **[Pack Name]** - [What it does]
   Install via ComfyUI Manager:
   - Open Manager → Install Custom Nodes
   - Search: "[pack name]"
   - Click Install → Restart ComfyUI

   OR manually:
   ```
   cd ComfyUI/custom_nodes
   git clone [repo URL]
   pip install -r requirements.txt
   ```
```

## ESSENTIAL NODE PACKS

### ComfyUI Manager (MUST HAVE)
**Repo:** https://github.com/ltdrdata/ComfyUI-Manager
**Purpose:** Install/manage other custom nodes

**Key Features:**
- One-click custom node installation
- Model downloads
- Missing node detection
- Update management

**Installation:**
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager
# Restart ComfyUI
```

### Efficiency Nodes
**Repo:** https://github.com/jags111/efficiency-nodes-comfyui
**Purpose:** Streamlined workflow nodes

**Key Nodes:**
- `Efficient Loader` - Combined checkpoint+VAE+LoRA loader
- `KSampler (Efficient)` - Sampler with preview
- `XY Plot` - Parameter comparison grids
- `LoRA Stacker` - Stack multiple LoRAs easily
- `Control Net Stacker` - Stack ControlNets

**When to Use:**
- Building complex workflows
- Parameter exploration
- Combining multiple LoRAs/ControlNets

### WAS Node Suite
**Repo:** https://github.com/WASasquatch/was-node-suite-comfyui
**Purpose:** 100+ utility nodes

**Key Nodes:**
- `WAS_Image_Save` - Advanced save options
- `WAS_Text_Concatenate` - Text manipulation
- `WAS_Image_Resize` - Flexible resizing
- `WAS_Mask_*` - Mask operations
- `WAS_Number_*` - Math operations
- `WAS_Logic_*` - Conditional logic

**When to Use:**
- Image processing pipelines
- Text manipulation
- Conditional workflows
- Batch processing

### rgthree Nodes
**Repo:** https://github.com/rgthree/rgthree-comfy
**Purpose:** Quality of life improvements

**Key Nodes:**
- `Context` - Bundle multiple outputs
- `Power Lora Loader` - Advanced LoRA loading
- `Image Comparer` - Compare images side-by-side
- `Any Switch` - Conditional routing
- `Bookmark` - Navigate large workflows

**When to Use:**
- Complex workflows with many connections
- Comparing generation results
- Conditional logic

## VIDEO GENERATION NODES

### ComfyUI-AnimateDiff-Evolved
**Repo:** https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved
**Purpose:** AnimateDiff video generation

**Required Models:**
- Motion modules in `ComfyUI/models/animatediff_models/`
- mm_sd_v15_v2.ckpt (standard)
- mm_sd_v15_v3.ckpt (improved)
- mm_sdxl_v10_beta.ckpt (SDXL)

**Key Nodes:**
- `ADE_AnimateDiffLoaderWithContext` - Load motion module
- `ADE_AnimateDiffUniformContextOptions` - Context settings
- `ADE_AnimateDiffLoRALoader` - Motion LoRAs
- `ADE_AnimateDiffCombine` - Combine frames
- `ADE_EmptyLatentImageLarge` - Video-sized latent

**Parameters:**
```
context_length: 16 (frames in context)
context_overlap: 4-8 (overlap between contexts)
context_stride: 1 (usually keep at 1)
closed_loop: True for seamless loops
```

**Basic Workflow:**
```
1. CheckpointLoader (SD 1.5 model)
2. ADE_AnimateDiffLoaderWithContext
3. ADE_AnimateDiffUniformContextOptions
4. EmptyLatentImage (batch_size = frame count)
5. KSampler
6. VAEDecode
7. VHS_VideoCombine
```

### ComfyUI-VideoHelperSuite
**Repo:** https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
**Purpose:** Video I/O and manipulation

**Key Nodes:**
- `VHS_VideoCombine` - Frames to video
- `VHS_LoadVideo` - Load video file
- `VHS_LoadVideoPath` - Load from path
- `VHS_SplitImages` - Split video to frames
- `VHS_DuplicateImages` - Duplicate frames
- `VHS_SelectEveryNthImage` - Sample frames

**VHS_VideoCombine Parameters:**
```
frame_rate: 8-30 (output FPS)
format: video/h264-mp4, video/webm, gif
loop_count: 0 for infinite (GIF)
pingpong: True for back-and-forth
```

### ComfyUI-WAN (WAN 2.2)
**Repo:** https://github.com/kijai/ComfyUI-WAN
**Purpose:** Advanced video generation framework

**Required Models:**
- Hunyuan Video models in `models/diffusion_models/`
- Video VAE in `models/vae/`
- LLaVA encoder in `models/LLM/`
- CLIP-L in `models/clip/`

**Key Nodes:**
- `WAN_ModelLoader` - Load video model
- `WAN_CLIPLoader` - Load text encoders
- `WAN_VAELoader` - Load video VAE
- `WAN_EmptyLatentVideo` - Create video latent
- `WAN_Sampler` - Video sampling
- `WAN_TextEncode` - Encode prompts
- `WAN_ImageEncode` - Image-to-video init
- `WAN_CameraControl` - Camera movements
- `WAN_VAEDecode` - Decode to frames

**Key Parameters:**
```
flow_shift: 7-12 (motion intensity)
embedded_guidance_scale: 5-8 (prompt adherence)
cfg: 4-7 (lower than images!)
steps: 25-40
```

### ComfyUI-SVI (Frame Interpolation)
**Repo:** https://github.com/Fannovel16/ComfyUI-SVI
**Purpose:** Frame interpolation and video enhancement

**Key Nodes:**
- `SVI_FrameInterpolation` - Interpolate frames
- `SVI_TemporalSmooth` - Reduce flicker
- `SVI_SceneDetect` - Detect scene cuts
- `SVI_VideoEnhance` - All-in-one enhance

**Interpolation Parameters:**
```
factor: 2, 4, 8 (multiply frames)
method: RIFE (fast), FILM (quality), AMT (best)
scene_cuts: Connect to SceneDetect output
```

## CONTROLNET NODES

### ControlNet Auxiliary Preprocessors
**Repo:** https://github.com/Fannovel16/comfyui_controlnet_aux
**Purpose:** All ControlNet preprocessors

**Preprocessor Nodes:**
| Node | Purpose | Best For |
|------|---------|----------|
| CannyEdgePreprocessor | Edge detection | Line art, structure |
| MiDaS-DepthMapPreprocessor | Depth estimation | 3D composition |
| LeReS-DepthMapPreprocessor | Detailed depth | Complex scenes |
| ZoeDepthPreprocessor | Fast depth | Quick previews |
| OpenposePreprocessor | Body pose | Characters, poses |
| DWPreprocessor | Face+hands+body | Full body poses |
| LineartPreprocessor | Line extraction | Manga, illustration |
| AnimeLineartPreprocessor | Anime lines | Anime style |
| SoftEdge_HED | Soft edges | Soft guidance |
| Scribble_XDoG | Scribble-like | Rough sketches |
| Normal_BAE | Normal maps | 3D lighting |
| OneFormer_COCO | Segmentation | Object separation |
| TilePreprocessor | Tile/detail | Upscaling, detail |

**Usage Pattern:**
```
1. LoadImage (reference)
2. [Preprocessor] (e.g., CannyEdgePreprocessor)
3. ControlNetLoader
4. ControlNetApplyAdvanced
5. Connect to KSampler positive
```

**ControlNet Models Location:**
`ComfyUI/models/controlnet/`

**Popular ControlNet Models:**
- control_v11p_sd15_canny
- control_v11f1p_sd15_depth
- control_v11p_sd15_openpose
- control_v11p_sd15_lineart
- control_v11p_sd15_softedge
- diffusers_xl_canny_mid (SDXL)
- diffusers_xl_depth_mid (SDXL)

### Built-in ControlNet Nodes

**Core Nodes (no custom pack needed):**
- `ControlNetLoader` - Load ControlNet model
- `ControlNetApply` - Basic application
- `ControlNetApplyAdvanced` - With strength/timing

**ControlNetApplyAdvanced Parameters:**
```
strength: 0.0-1.0 (control intensity)
start_percent: 0.0 (when to start)
end_percent: 1.0 (when to stop)
```

**Multi-ControlNet Strategy:**
```
Total strength should be ~1.0-1.5
Primary control: 0.6-0.8
Secondary: 0.3-0.5
Example: Depth 0.7 + Canny 0.4 = 1.1 total
```

## UPSCALING NODES

### Built-in Upscale Nodes

**ImageUpscaleWithModel:**
- Uses ESRGAN-style models
- Models in `ComfyUI/models/upscale_models/`

**Popular Upscale Models:**
```
RealESRGAN_x4plus.pth - General (4x)
RealESRGAN_x4plus_anime_6B.pth - Anime (4x)
RealESRGAN_x2plus.pth - General (2x)
4x_NMKD-Siax_200k.pth - Detailed (4x)
4x-UltraSharp.pth - Sharp details (4x)
SwinIR_4x.pth - High quality (4x)
```

**LatentUpscale:**
- Upscale in latent space
- Methods: nearest, bilinear, area, bicubic
- Faster but lower quality than image upscale

### ComfyUI_UltimateSDUpscale
**Repo:** https://github.com/ssitu/ComfyUI_UltimateSDUpscale
**Purpose:** Tiled upscaling with img2img

**Key Node:**
`UltimateSDUpscale` - All-in-one tiled upscaler

**Parameters:**
```
upscale_by: 2.0-4.0 (scale factor)
tile_width: 512-1024 (tile size)
tile_height: 512-1024
tile_padding: 32-64 (overlap)
seam_fix_mode: BAND, HALF, BOTH
seam_fix_denoise: 0.2-0.4
seam_fix_width: 64 (seam blend width)
```

**When to Use:**
- Upscaling without VRAM for full image
- Need img2img refinement while upscaling
- Want automatic seam handling

### ComfyUI-TiledDiffusion
**Repo:** https://github.com/shiimizu/ComfyUI-TiledDiffusion
**Purpose:** Tiled sampling for large images

**Key Nodes:**
- `TiledDiffusion` - Apply tiled sampling to model
- `VAEDecodeTiled_TiledDiffusion` - Tiled VAE decode

**Parameters:**
```
method: MultiDiffusion, Mixture of Diffusers
tile_width: 768-1024
tile_height: 768-1024
tile_overlap: 64-128
batch_size: 1-4 (per tile)
```

**When to Use:**
- Generating images larger than model native
- Very low VRAM situations
- Need consistent style across large image

## FACE PROCESSING NODES

### ComfyUI-Impact-Pack
**Repo:** https://github.com/ltdrdata/ComfyUI-Impact-Pack
**Purpose:** Face/hand detection and fixing

**Key Nodes:**
- `FaceDetailer` - Auto-detect and fix faces
- `DetailerForEach` - Process each detected area
- `SAMDetectorCombined` - Segment Anything detection
- `BboxDetectorSEGS` - Bounding box detection
- `SegmDetectorSEGS` - Segmentation detection
- `Segs & Mask` - Various mask operations

**FaceDetailer Parameters:**
```
guide_size: 384-512 (face crop size)
max_size: 1024 (max detection size)
seed: -1 for random
steps: 20
cfg: 7
denoise: 0.4-0.6
```

**Detection Models (in models/ultralytics/):**
- face_yolov8m.pt - Face detection
- hand_yolov8s.pt - Hand detection
- person_yolov8m-seg.pt - Person segmentation

### ReActor (Face Swap)
**Repo:** https://github.com/Gourieff/comfyui-reactor-node
**Purpose:** Face swapping in images/video

**Key Nodes:**
- `ReActorFaceSwap` - Main face swap
- `ReActorLoadFaceModel` - Load saved face
- `ReActorSaveFaceModel` - Save face embedding
- `ReActorMaskHelper` - Face masking

**Parameters:**
```
swap_model: inswapper_128.onnx
facedetection: retinaface_resnet50
face_restore_model: codeformer-v0.1.0.pth
codeformer_weight: 0.5-0.8
```

### IPAdapter Face
**Repo:** https://github.com/cubiq/ComfyUI_IPAdapter_plus
**Purpose:** Face consistency using reference

**Key Nodes:**
- `IPAdapterApplyFaceID` - Apply face reference
- `IPAdapterLoadFaceID` - Load FaceID model
- `InsightFaceLoader` - Face analysis

**FaceID Models:**
- ip-adapter-faceid_sd15.bin
- ip-adapter-faceid-plusv2_sd15.bin
- ip-adapter-faceid_sdxl.bin

**When to Use:**
- Maintain face consistency across images
- Character creation with reference
- Less "copy" effect than ReActor

### InstantID
**Repo:** https://github.com/cubiq/ComfyUI_InstantID
**Purpose:** Identity-preserving generation

**Key Nodes:**
- `InstantIDModelLoader` - Load InstantID
- `InstantIDFaceAnalysis` - Analyze face
- `ApplyInstantID` - Apply to generation

**Best For:**
- Generating new images with same person
- More control than face swap
- Works with prompts for poses/styles

## UTILITY NODES

### KJNodes
**Repo:** https://github.com/kijai/ComfyUI-KJNodes
**Purpose:** Various utility nodes

**Key Nodes:**
- `ConditioningSetMaskAndCombine` - Regional prompting
- `BatchCropFromMask` - Crop using masks
- `CreateTextMask` - Text to mask
- `FlipSigmas` - Sigma manipulation
- `INTConstant`, `FloatConstant` - Value nodes

### Crystools
**Repo:** https://github.com/crystian/ComfyUI-Crystools
**Purpose:** Metadata and utilities

**Key Nodes:**
- `Load metadata` - Extract generation info
- `Save with metadata` - Embed parameters
- `Debug` - Debug any value
- `Stats system` - Performance monitoring

### ComfyUI-Custom-Scripts
**Repo:** https://github.com/pythongosssss/ComfyUI-Custom-Scripts
**Purpose:** UI improvements

**Features:**
- Auto-arrange nodes
- Image feed (history)
- Favicon status
- Workflow templates
- Better node search

### ComfyUI-Easy-Use
**Repo:** https://github.com/yolain/ComfyUI-Easy-Use
**Purpose:** Simplified workflow nodes

**Key Nodes:**
- `easy fullLoader` - All-in-one loader
- `easy kSampler` - Simplified sampler
- `easy preDetailerFix` - Auto face/hand fix
- `easy XYInputs` - Easy XY plots

### Derfuu Math Nodes
**Repo:** https://github.com/Derfuu/Derfuu_ComfyUI_ModdedNodes
**Purpose:** Math and calculations

**Key Nodes:**
- `DF_Multiply`, `DF_Divide`, `DF_Add`
- `DF_Ceil`, `DF_Floor`, `DF_Round`
- `DF_Random` - Random numbers
- `DF_Clamp` - Value clamping

### Prompt Utilities

**ComfyUI-Prompt-Control:**
- Schedule prompts over steps
- Prompt interpolation
- Conditional prompts

**ComfyUI-SDXL-EmptyLatentImage:**
- Pre-set SDXL resolutions
- Aspect ratio picker

## WAN 2.2 & SVI DETAILED NODES

### ComfyUI-WAN Complete Node Reference

**Model Loading:**
```
WAN_ModelLoader
  - model_name: hunyuan_video_720_cfgdistill_fp8_e4m3fn.safetensors
  - Outputs: MODEL

WAN_CLIPLoader
  - clip_name: llava-llama-3-8b-v1.1 (or path)
  - clip_name2: clip_l.safetensors
  - Outputs: CLIP

WAN_VAELoader
  - vae_name: hunyuan_video_vae_fp32.safetensors
  - Outputs: VAE
```

**Latent Creation:**
```
WAN_EmptyLatentVideo
  - width: 848 (must be multiple of 16)
  - height: 480 (must be multiple of 16)
  - num_frames: 49 (or 81, 129)
  - batch_size: 1
  - Outputs: LATENT
```

**Text Encoding:**
```
WAN_TextEncode
  - text: "your prompt"
  - clip: [from WAN_CLIPLoader]
  - Outputs: CONDITIONING
```

**Image Encoding (for i2v):**
```
WAN_ImageEncode
  - image: [from LoadImage]
  - vae: [from WAN_VAELoader]
  - Outputs: LATENT (init latent)
```

**Sampling:**
```
WAN_Sampler
  - model: [from WAN_ModelLoader]
  - positive: [from WAN_TextEncode]
  - negative: [from WAN_TextEncode]
  - latent: [from WAN_EmptyLatentVideo or WAN_ImageEncode]
  - seed: 12345
  - steps: 30
  - cfg: 6.0
  - flow_shift: 9.0
  - embedded_guidance_scale: 6.0
  - Outputs: LATENT
```

**Camera Control:**
```
WAN_CameraControl
  - pan_x: -1.0 to 1.0 (left/right)
  - pan_y: -1.0 to 1.0 (up/down)
  - zoom: -1.0 to 1.0 (out/in)
  - rotate: -1.0 to 1.0 (ccw/cw)
  - tilt: -1.0 to 1.0
  - num_frames: 49
  - Outputs: CAMERA_CONTROL
```

**Decoding:**
```
WAN_VAEDecode
  - samples: [from WAN_Sampler]
  - vae: [from WAN_VAELoader]
  - tile_size: 256 (for low VRAM)
  - Outputs: IMAGE (frame sequence)
```

### SVI Complete Node Reference

**Frame Interpolation:**
```
SVI_FrameInterpolation
  - images: [frame sequence]
  - factor: 2, 4, or 8
  - method: "RIFE", "FILM", "AMT"
  - scene_cuts: [optional, from SVI_SceneDetect]
  - Outputs: IMAGE (interpolated frames)
```

**Temporal Smoothing:**
```
SVI_TemporalSmooth
  - images: [frame sequence]
  - strength: 0.0-1.0 (0.2-0.4 recommended)
  - window_size: 3, 5, or 7
  - scene_cuts: [optional]
  - Outputs: IMAGE
```

**Scene Detection:**
```
SVI_SceneDetect
  - images: [frame sequence]
  - threshold: 0.3-0.7 (0.4-0.5 recommended)
  - Outputs: SCENE_CUTS (list)
```

**Video Enhancement:**
```
SVI_VideoEnhance
  - images: [frame sequence]
  - denoise: 0.0-1.0
  - sharpen: 0.0-1.0
  - temporal_smooth: 0.0-1.0
  - color_correct: True/False
  - Outputs: IMAGE
```

### Combining WAN + SVI Pipeline

```
Complete high-quality video pipeline:

1. WAN_ModelLoader → MODEL
2. WAN_CLIPLoader → CLIP
3. WAN_VAELoader → VAE
4. WAN_EmptyLatentVideo → LATENT
5. WAN_TextEncode (positive) → CONDITIONING
6. WAN_TextEncode (negative) → CONDITIONING
7. WAN_CameraControl → CAMERA (optional)
8. WAN_Sampler → LATENT
9. WAN_VAEDecode → IMAGE (frames)
10. SVI_SceneDetect → SCENE_CUTS
11. SVI_TemporalSmooth (strength=0.2) → IMAGE
12. SVI_FrameInterpolation (2x, FILM) → IMAGE
13. VHS_VideoCombine → VIDEO FILE
```

## CUSTOM NODE INSTALLATION

### Method 1: ComfyUI Manager (Recommended)

1. Ensure ComfyUI Manager is installed
2. In ComfyUI, click "Manager" button
3. Click "Install Custom Nodes"
4. Search for the pack name
5. Click "Install"
6. Restart ComfyUI

### Method 2: Git Clone

```bash
cd ComfyUI/custom_nodes
git clone [REPO_URL]
cd [PACK_NAME]
pip install -r requirements.txt  # if exists
# Restart ComfyUI
```

### Method 3: Download ZIP

1. Download ZIP from GitHub
2. Extract to `ComfyUI/custom_nodes/`
3. Rename folder (remove `-main` suffix)
4. Install requirements if needed
5. Restart ComfyUI

### Common Installation Issues

**"Module not found" error:**
```bash
cd ComfyUI/custom_nodes/[PACK_NAME]
pip install -r requirements.txt
# Or install specific package:
pip install [package_name]
```

**"CUDA out of memory":**
- Some packs load models on startup
- Reduce batch size
- Use fp8 models

**Node not appearing:**
- Check ComfyUI console for errors
- Verify folder structure
- Restart ComfyUI completely

**Version conflicts:**
- Update ComfyUI first
- Check pack's GitHub issues
- Try older pack version

### Model Downloads for Custom Nodes

**AnimateDiff Motion Modules:**
```
Location: ComfyUI/models/animatediff_models/
Files:
- mm_sd_v15_v2.ckpt
- mm_sd_v15_v3.ckpt
Source: HuggingFace guoyww/animatediff
```

**WAN/Hunyuan Video:**
```
Location: ComfyUI/models/diffusion_models/
Files:
- hunyuan_video_720_cfgdistill_fp8_e4m3fn.safetensors
Source: HuggingFace tencent/HunyuanVideo

VAE Location: ComfyUI/models/vae/
- hunyuan_video_vae_fp32.safetensors

Text Encoders: ComfyUI/models/LLM/
- llava-llama-3-8b-v1.1 (folder)
```

**IPAdapter Models:**
```
Location: ComfyUI/models/ipadapter/
Files:
- ip-adapter_sd15.safetensors
- ip-adapter-plus_sd15.safetensors
- ip-adapter-faceid_sd15.bin
```

**ControlNet:**
```
Location: ComfyUI/models/controlnet/
Files: Various control_v11* files
Source: HuggingFace lllyasviel/ControlNet-v1-1
```

## NODE PACK DEPENDENCIES

### Video Generation Stack

**For AnimateDiff videos:**
```
Required:
1. ComfyUI-AnimateDiff-Evolved
2. ComfyUI-VideoHelperSuite

Recommended:
3. ComfyUI-SVI (interpolation)
4. ComfyUI-Impact-Pack (face fix)
```

**For WAN 2.2 / Hunyuan videos:**
```
Required:
1. ComfyUI-WAN

Recommended:
2. ComfyUI-VideoHelperSuite
3. ComfyUI-SVI
```

### Image Enhancement Stack

**For high-quality upscaling:**
```
Required:
1. Built-in (ImageUpscaleWithModel)

Recommended:
2. ComfyUI_UltimateSDUpscale (tiled)
3. ComfyUI-TiledDiffusion (large images)
```

**For face/detail fixing:**
```
Required:
1. ComfyUI-Impact-Pack

Recommended:
2. comfyui_controlnet_aux (preprocessors)
```

### Style Transfer Stack

**For image-based prompting:**
```
Required:
1. ComfyUI_IPAdapter_plus

Recommended:
2. ComfyUI_InstantID (faces)
3. comfyui_controlnet_aux
```

### Workflow Building Stack

**For complex workflows:**
```
Recommended:
1. efficiency-nodes-comfyui
2. ComfyUI-Custom-Scripts
3. rgthree-comfy
4. was-node-suite-comfyui
```

### Dependency Installation Order

When setting up from scratch:
```
1. ComfyUI Manager (first!)
2. VideoHelperSuite (video I/O)
3. ControlNet Aux (preprocessors)
4. Impact Pack (detection/fixing)
5. AnimateDiff-Evolved OR ComfyUI-WAN
6. IPAdapter Plus
7. SVI (interpolation)
8. UltimateSDUpscale
9. Efficiency nodes
10. WAS Node Suite
```

### Checking What's Installed

In ComfyUI Manager:
- Click "Manager"
- Click "Installed Custom Nodes"
- Shows all installed packs with update status

Via filesystem:
```bash
ls ComfyUI/custom_nodes/
```

Via node search:
- Right-click canvas → "Add Node"
- Search for pack-specific node
- If found → pack is installed
