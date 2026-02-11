---
id: video_advanced
title: Advanced Video Generation
keywords: [video, WAN, Hunyuan, AnimateDiff, SVI, interpolation, frames, motion, camera, temporal, flickering, upscale, slow-motion, loop, face, style transfer]
category: video
priority: low
---

## WAN 2.2 (ComfyUI-WAN)

### Overview
WAN 2.2 is an advanced video generation framework for ComfyUI that supports multiple video models including Hunyuan Video, CogVideoX, and custom models.

### Key Features WAN 2.2
- **Multi-model support**: Hunyuan, CogVideoX, LTX, custom models
- **Text-to-video** and **image-to-video**
- **Video-to-video** style transfer
- **Camera control**: Pan, zoom, tilt, rotate
- **Motion control**: Keyframe animation
- **Temporal consistency**: Better frame coherence
- **Memory optimization**: Chunked processing

### WAN 2.2 Node Types

**Loaders:**
- `WAN_ModelLoader`: Load WAN-compatible video model
- `WAN_CLIPLoader`: Text encoder for WAN models
- `WAN_VAELoader`: Video VAE (3D convolutions)

**Latent:**
- `WAN_EmptyLatentVideo`: Create empty video latent
  - width, height, num_frames, fps
- `WAN_LatentVideoComposite`: Combine video latents

**Sampling:**
- `WAN_Sampler`: Main video sampler
  - Inputs: model, positive, negative, latent, seed, steps, cfg, denoise
  - flow_shift: Motion intensity (5-15 typical)
  - embedded_guidance_scale: Internal guidance

**Conditioning:**
- `WAN_TextEncode`: Encode text for video
- `WAN_ImageEncode`: Encode image for i2v
- `WAN_CameraControl`: Add camera motion
  - pan_x, pan_y, zoom, rotate, tilt

**Output:**
- `WAN_VAEDecode`: Decode video latent to frames
- `WAN_VideoSave`: Save as video file

### WAN 2.2 Workflow - Text to Video
```
1. WAN_ModelLoader (hunyuan_video_720_fp8)
2. WAN_CLIPLoader (llava-llama-3-8b + clip_l)
3. WAN_TextEncode (positive prompt)
4. WAN_TextEncode (negative prompt)
5. WAN_EmptyLatentVideo (848x480, 81 frames)
6. WAN_Sampler (steps=30, cfg=6, flow_shift=9)
7. WAN_VAEDecode
8. WAN_VideoSave (fps=24)
```

### WAN 2.2 Workflow - Image to Video
```
1. LoadImage (start frame)
2. WAN_ModelLoader
3. WAN_ImageEncode (encode start image)
4. WAN_TextEncode (describe motion)
5. WAN_Sampler (connect image latent)
6. WAN_VAEDecode
7. WAN_VideoSave
```

### WAN 2.2 Parameters Guide

**flow_shift (Motion Intensity)**
```
5-7:   Subtle motion, stable camera
7-9:   Moderate motion (RECOMMENDED)
9-12:  Dynamic motion, action scenes
12-15: Extreme motion (may be unstable)
```

**embedded_guidance_scale**
```
3-5:   More creative, less prompt adherence
5-7:   Balanced (RECOMMENDED)
7-10:  Strict prompt following
```

**CFG Scale for WAN**
- Unlike images, video often needs lower CFG
- Recommended: 4-7 (not 7-9 like images)
- Too high CFG = flickering, artifacts

**Frame Count vs VRAM**
```
Frames   Resolution   VRAM (fp8)
49       848x480      12GB
81       848x480      16GB
129      848x480      24GB
49       1280x720     20GB
81       1280x720     32GB+
```

### WAN 2.2 Camera Control
```python
# Pan left to right
WAN_CameraControl:
  pan_x: 0.1  # -1 to 1, negative=left, positive=right
  pan_y: 0
  zoom: 0

# Zoom in
WAN_CameraControl:
  pan_x: 0
  pan_y: 0
  zoom: 0.2  # positive=zoom in, negative=zoom out

# Cinematic tilt
WAN_CameraControl:
  tilt: 0.05
  rotate: 0
```

### WAN 2.2 Common Issues

**"Video is static/no motion"**
- Increase flow_shift: 7→10
- Add motion words to prompt: "walking", "moving", "dynamic"
- Check frame count (more frames = more motion potential)

**"Video is too chaotic"**
- Decrease flow_shift: 10→7
- Lower CFG: 7→5
- Add "smooth motion, steady camera" to prompt

**"Faces look bad in video"**
- Use face-specific prompts
- Apply frame-by-frame face fix after generation
- Use IP-Adapter for face consistency

**"Out of VRAM"**
- Use fp8 model
- Reduce frame count
- Reduce resolution (848x480 instead of 1280x720)
- Enable chunked temporal processing

## SVI Pro (Stable Video Interpolation Pro)

### What is SVI Pro?
SVI Pro is an advanced frame interpolation and video enhancement system that:
- Interpolates between generated frames for smoother video
- Enhances temporal consistency
- Fixes flickering and artifacts
- Upscales video while maintaining coherence

### SVI Pro Nodes

**Core Nodes:**
- `SVI_FrameInterpolation`: Main interpolation node
  - interpolation_factor: 2x, 4x, 8x frames
  - model: RIFE, FILM, AMT
  - scene_detect: Auto-detect scene changes

- `SVI_TemporalSmooth`: Reduce flickering
  - strength: 0.0-1.0
  - window_size: frames to consider (3, 5, 7)

- `SVI_VideoEnhance`: All-in-one enhancement
  - denoise, sharpen, color_correct
  - temporal_smooth, upscale

- `SVI_SceneDetect`: Detect scene boundaries
  - threshold: sensitivity (0.3-0.7)

### SVI Pro Interpolation Methods

**RIFE (Real-Time Intermediate Flow Estimation)**
- Very fast
- Good quality
- Best for real-time or quick processing
- Artifacts at high interpolation (8x+)

**FILM (Frame Interpolation for Large Motion)**
- Higher quality
- Better for large motion
- Slower than RIFE
- Recommended for final output

**AMT (Adaptive Motion Transfer)**
- Best for complex motion
- Handles occlusion well
- Slowest but highest quality
- Use for professional output

### SVI Pro Workflow - Smooth Video
```
1. [Video generation workflow]
2. VHS_VideoCombine (frames as list)
3. SVI_SceneDetect (detect cuts)
4. SVI_FrameInterpolation (FILM, 2x)
5. SVI_TemporalSmooth (0.3 strength)
6. VHS_VideoSave
```

### SVI Pro Workflow - Upscale Video
```
1. Load video frames
2. SVI_TemporalSmooth (pre-smooth)
3. ImageUpscaleWithModel (per-frame, ESRGAN)
4. SVI_FrameInterpolation (2x for 60fps)
5. SVI_TemporalSmooth (post-smooth, 0.2)
6. VHS_VideoSave
```

### SVI Pro Parameters

**Interpolation Factor**
```
2x:  24fps → 48fps, subtle smoothing
4x:  24fps → 96fps, very smooth (then reduce to 60)
8x:  24fps → 192fps, extreme slow-mo possible
```

**Temporal Smooth Strength**
```
0.1-0.2: Subtle, preserve detail
0.3-0.4: Moderate, good for most videos
0.5-0.7: Strong, may blur fast motion
0.8+:    Very strong, only for static scenes
```

**Scene Detect Threshold**
```
0.2-0.3: Sensitive, many scene cuts detected
0.4-0.5: Balanced (RECOMMENDED)
0.6-0.7: Conservative, only major cuts
```

### SVI Pro Tips

1. **Always use scene detection** before interpolation
   - Prevents artifacts at scene boundaries
   - Let interpolation restart at each scene

2. **Order matters:**
   - Temporal smooth → Upscale → Interpolate → Light smooth
   - NOT: Interpolate first (amplifies artifacts)

3. **For AI-generated video:**
   - Apply light temporal smooth (0.2-0.3) FIRST
   - Then interpolate
   - This reduces AI flickering before amplification

4. **Memory management:**
   - Process in batches for long videos
   - SVI_BatchProcessor node helps

## Hunyuan Video (Tencent)

### Overview
Hunyuan Video is a state-of-the-art video generation model from Tencent.
- High quality motion
- Good text understanding (Chinese + English)
- Multiple resolutions supported
- Native ComfyUI support

### Hunyuan Video Models

**Main Models:**
- `hunyuan_video_720_cfgdistill_fp8_e4m3fn.safetensors` (Recommended)
  - 720p capable, fp8 quantized, ~12GB
- `hunyuan_video_720_bf16.safetensors`
  - Full precision, ~24GB
- `hunyuan_video_t2v_720p.safetensors`
  - Text-to-video specific

**Required Components:**
- Video VAE: `hunyuan_video_vae_fp32.safetensors`
- Text Encoder: LLaVA-Llama-3-8B-v1.1
- CLIP: `clip_l.safetensors`

### Hunyuan Native Nodes

**Loading:**
- `HunyuanVideoModelLoader`: Load video model
- `HunyuanVideoVAELoader`: Load video VAE
- `HunyuanVideoTextEncode`: Text encoding

**Generation:**
- `EmptyHunyuanLatentVideo`: Create video latent
  - width, height (multiples of 16)
  - length: frames (must be 4n+1: 5, 9, 13, 17, 21, 25...)
  - batch_size: usually 1

- `HunyuanVideoSampler`: Sampling
  - steps: 30-50
  - cfg: 1.0 (uses embedded guidance!)
  - embedded_guidance_scale: 6.0 (this is the real guidance)
  - flow_shift: 7.0-9.0

### Hunyuan Video Resolutions

**Supported:**
```
Resolution    Aspect   Frames   VRAM(fp8)
848x480       16:9     49       12GB
848x480       16:9     81       16GB
720x480       3:2      49       10GB
1280x720      16:9     49       20GB
480x848       9:16     49       12GB (vertical)
```

**Frame Count Rules:**
- Must be 4n+1: 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, ...
- Or multiples like: 49, 81, 97, 113, 129

### Hunyuan Video Prompt Tips

**Good prompts include:**
- Clear subject description
- Motion/action words
- Camera movement (optional)
- Atmosphere/lighting

**Example prompts:**
```
"A cat walking through a garden, sunlight filtering through leaves,
gentle camera follow, cinematic lighting, 4K quality"

"Ocean waves crashing on rocky shore, dramatic sunset,
wide angle shot, slow motion, nature documentary style"
```

**Avoid:**
- Very complex multi-subject scenes
- Rapid scene changes in single generation
- Extreme close-ups of faces (unless using face model)

### Hunyuan vs WAN 2.2

| Feature | Hunyuan Native | WAN 2.2 |
|---------|---------------|---------|
| Setup | Simpler | More complex |
| Flexibility | Limited | High |
| Camera control | Basic | Advanced |
| Multi-model | No | Yes |
| Memory | Optimized | Varies |
| Best for | Quick generation | Advanced control |

**Recommendation:**
- Use Hunyuan native for simple t2v/i2v
- Use WAN 2.2 for camera control, advanced workflows

## ADVANCED VIDEO TRICKS

### 1. Multi-Shot Video (Scene Composition)
Generate multiple short clips and combine:
```
1. Generate clip 1 (establishing shot)
2. Generate clip 2 (action) - use last frame of clip 1 as reference
3. Generate clip 3 (close-up)
4. SVI_FrameInterpolation for transitions
5. Combine with crossfade
```

### 2. Consistent Character Across Shots
```
1. Generate first clip with character
2. Extract key frame with character
3. Use IP-Adapter + face reference for subsequent clips
4. OR use InstantID for face consistency
5. All clips share same seed base
```

### 3. Loop Creation
Perfect loops for GIFs/backgrounds:
```
Method A - Ping-Pong:
1. Generate normally
2. Reverse frames
3. Concatenate (forward + reverse)
4. Interpolate at join point

Method B - Circular Generation:
1. WAN_EmptyLatentVideo with closed_loop=True
2. Forces end frame to match start
3. Works with AnimateDiff context options too
```

### 4. Slow Motion from Generated Video
```
1. Generate at normal speed (24fps, 49 frames = 2 sec)
2. SVI_FrameInterpolation 4x (196 frames)
3. Export at 24fps = 8 seconds of slow motion
4. Temporal smooth at 0.2 for cleaner result
```

### 5. Video Style Transfer
Apply artistic style to real video:
```
1. Load source video
2. Extract frames
3. Process each frame:
   - VAEEncode
   - KSampler (img2img, denoise 0.4-0.6)
   - VAEDecode
4. SVI_TemporalSmooth (reduce flicker from frame-by-frame)
5. Recombine
```

### 6. Temporal ControlNet
Use motion from reference video:
```
1. Load reference video
2. Extract depth/flow maps per frame
3. Use as ControlNet sequence
4. Generate with new style/content
5. Motion preserved, content changed
```

### 7. Face Replacement in Video
```
1. Generate base video
2. Extract frames
3. Detect faces per frame (Impact Pack)
4. For each frame:
   - Inpaint face region
   - Use InstantID/IP-Adapter face
5. SVI_TemporalSmooth on face region
6. Recombine
```

### 8. Upscale Video Without Losing Motion
```
WRONG: Upscale → Interpolate (amplifies artifacts)

RIGHT:
1. SVI_TemporalSmooth (light, 0.2)
2. Upscale frames (ESRGAN/SwinIR)
3. SVI_FrameInterpolation (2x only)
4. SVI_TemporalSmooth (very light, 0.1)
```

### 9. Fix Flickering in Generated Video
```
Method A - Post-process:
1. SVI_TemporalSmooth (0.3-0.5)
2. May slightly blur motion

Method B - Regenerate:
1. Use consistent seed
2. Add motion LoRA
3. Lower CFG (5-6 instead of 7+)
4. Increase context overlap (AnimateDiff)

Method C - Hybrid:
1. Extract frames with worst flicker
2. Inpaint/regenerate those frames
3. SVI_FrameInterpolation to blend
```

### 10. Long Video Generation (>10 seconds)
```
Method A - Chunked Generation:
1. Generate 5-second chunks
2. Use last frame as init for next chunk
3. Slight denoise (0.5-0.7) for coherence
4. Crossfade at boundaries

Method B - Hierarchical:
1. Generate keyframes (every 8th frame)
2. Interpolate between keyframes
3. Refine interpolated frames
4. Results in longer coherent video

Method C - AnimateDiff Context:
1. Use sliding window context
2. context_length=16, overlap=8
3. Generates seamlessly
```

### 11. Audio-Reactive Video
```
1. Analyze audio for beats/peaks
2. Map to generation parameters:
   - Beat → flow_shift spike
   - Bass → zoom
   - Melody → color shift
3. Generate with keyframed parameters
4. Sync with audio in post
```

### 12. Depth-Guided Camera Moves
```
1. Generate static image
2. Create depth map (MiDaS)
3. Use depth for 3D camera simulation:
   - Parallax effects
   - Focus pulls
   - Dolly zoom
4. Process through video model for naturalness
```

## VIDEO WORKFLOW TEMPLATES

### Template: Basic WAN 2.2 Text-to-Video
```json
{
  "1": {
    "class_type": "WAN_ModelLoader",
    "inputs": {
      "model_name": "hunyuan_video_720_cfgdistill_fp8_e4m3fn.safetensors"
    }
  },
  "2": {
    "class_type": "WAN_CLIPLoader",
    "inputs": {
      "clip_name": "llava-llama-3-8b-v1.1",
      "clip_name2": "clip_l.safetensors"
    }
  },
  "3": {
    "class_type": "WAN_TextEncode",
    "inputs": {
      "text": "A majestic eagle soaring through clouds, golden sunset light, cinematic",
      "clip": ["2", 0]
    }
  },
  "4": {
    "class_type": "WAN_TextEncode",
    "inputs": {
      "text": "blurry, low quality, distorted",
      "clip": ["2", 0]
    }
  },
  "5": {
    "class_type": "WAN_EmptyLatentVideo",
    "inputs": {
      "width": 848,
      "height": 480,
      "num_frames": 49,
      "batch_size": 1
    }
  },
  "6": {
    "class_type": "WAN_Sampler",
    "inputs": {
      "model": ["1", 0],
      "positive": ["3", 0],
      "negative": ["4", 0],
      "latent": ["5", 0],
      "seed": 12345,
      "steps": 30,
      "cfg": 6.0,
      "flow_shift": 9.0
    }
  },
  "7": {
    "class_type": "WAN_VAELoader",
    "inputs": {
      "vae_name": "hunyuan_video_vae_fp32.safetensors"
    }
  },
  "8": {
    "class_type": "WAN_VAEDecode",
    "inputs": {
      "samples": ["6", 0],
      "vae": ["7", 0]
    }
  },
  "9": {
    "class_type": "VHS_VideoCombine",
    "inputs": {
      "images": ["8", 0],
      "frame_rate": 24,
      "format": "video/h264-mp4"
    }
  }
}
```

### Template: Image-to-Video with Camera Control
```json
{
  "1": {"class_type": "LoadImage", "inputs": {"image": "start_frame.png"}},
  "2": {"class_type": "WAN_ModelLoader", "inputs": {"model_name": "..."}},
  "3": {"class_type": "WAN_ImageEncode", "inputs": {"image": ["1", 0]}},
  "4": {"class_type": "WAN_CameraControl", "inputs": {
    "pan_x": 0.1,
    "pan_y": 0,
    "zoom": 0.05,
    "num_frames": 49
  }},
  "5": {"class_type": "WAN_Sampler", "inputs": {
    "camera_control": ["4", 0],
    "image_latent": ["3", 0]
  }}
}
```

### Template: Video Enhancement Pipeline
```json
{
  "1": {"class_type": "VHS_LoadVideo", "inputs": {"video": "input.mp4"}},
  "2": {"class_type": "SVI_SceneDetect", "inputs": {
    "images": ["1", 0],
    "threshold": 0.4
  }},
  "3": {"class_type": "SVI_TemporalSmooth", "inputs": {
    "images": ["1", 0],
    "strength": 0.25,
    "scene_cuts": ["2", 0]
  }},
  "4": {"class_type": "ImageUpscaleWithModel", "inputs": {
    "image": ["3", 0],
    "model_name": "RealESRGAN_x4plus"
  }},
  "5": {"class_type": "SVI_FrameInterpolation", "inputs": {
    "images": ["4", 0],
    "factor": 2,
    "method": "FILM",
    "scene_cuts": ["2", 0]
  }},
  "6": {"class_type": "VHS_VideoCombine", "inputs": {
    "images": ["5", 0],
    "frame_rate": 48
  }}
}
```

### Template: AnimateDiff with Temporal Fix
```json
{
  "context": {
    "class_type": "ADE_AnimateDiffUniformContextOptions",
    "inputs": {
      "context_length": 16,
      "context_stride": 1,
      "context_overlap": 4,
      "closed_loop": false
    }
  },
  "motion_lora": {
    "class_type": "ADE_AnimateDiffLoRALoader",
    "inputs": {
      "lora_name": "v2_lora_ZoomIn.safetensors",
      "strength": 0.7
    }
  }
}
```

## VIDEO QUALITY TROUBLESHOOTING

### "Video looks like slideshow / no smooth motion"

**Causes:**
- Too few frames
- Low FPS output
- Missing interpolation

**Fixes:**
1. Increase frame count: 25 → 49 → 81
2. Use SVI interpolation (2x-4x)
3. Output at proper FPS (24-30)
4. Add flow_shift if using WAN

### "Colors shift/flicker between frames"

**Causes:**
- VAE inconsistency
- CFG too high
- Per-frame processing without temporal awareness

**Fixes:**
1. Lower CFG: 8 → 5-6
2. Apply SVI_TemporalSmooth (0.3-0.5)
3. Use consistent VAE settings
4. Add "consistent lighting" to prompt

### "Subject morphs/changes through video"

**Causes:**
- Weak conditioning
- High flow_shift
- No reference image

**Fixes:**
1. Use IP-Adapter with subject reference
2. Lower flow_shift: 10 → 7
3. Increase embedded_guidance_scale
4. More specific prompt with details locked

### "Motion is jittery/unnatural"

**Causes:**
- Incompatible motion settings
- Scene transitions mid-generation
- Post-processing artifacts

**Fixes:**
1. Use motion LoRA for specific motion type
2. Increase context overlap (AnimateDiff)
3. Apply temporal smoothing BEFORE other processing
4. Lower denoise if using video-to-video

### "Blurry output"

**Causes:**
- Resolution too low
- Temporal smooth too strong
- Bad upscaling

**Fixes:**
1. Generate at native resolution
2. Reduce temporal smooth strength (0.5 → 0.2)
3. Use better upscaler (SwinIR > basic bicubic)
4. Add sharpening as final step (carefully)

### "Artifacts at edges/seams"

**Causes:**
- Tiled processing without overlap
- Resolution not multiple of 16
- Edge handling issues

**Fixes:**
1. Ensure width/height are multiples of 16 (ideally 32)
2. Increase tile overlap in tiled processing
3. Use seamless/circular padding if available

### "VRAM crash during generation"

**Causes:**
- Too many frames
- Resolution too high
- FP16 model on limited VRAM

**Fixes:**
1. Use FP8 models
2. Reduce frames: 81 → 49 → 25
3. Reduce resolution: 720p → 480p
4. Enable chunked temporal processing
5. Close other GPU applications

### "Video generation extremely slow"

**Causes:**
- Non-optimized settings
- FP16 when FP8 available
- Too many steps

**Fixes:**
1. Use FP8 model
2. Reduce steps: 50 → 30
3. Lower resolution for tests
4. Enable attention optimization
5. Use faster sampler (euler vs dpm++ sde)

## FRAME INTERPOLATION DEEP DIVE

### Available Methods

**RIFE (Recommended for Speed)**
```
Pros:
- Very fast (real-time capable)
- Good quality for moderate motion
- Low VRAM usage

Cons:
- Struggles with large motion
- Artifacts at high factors (8x+)
- Scene boundary issues

Best for:
- Quick previews
- Subtle slow-motion
- Real-time applications
```

**FILM (Recommended for Quality)**
```
Pros:
- Excellent motion handling
- Better large motion interpolation
- Fewer artifacts

Cons:
- Slower than RIFE (3-5x)
- Higher VRAM
- Still scene boundary issues

Best for:
- Final renders
- Professional output
- Large motion scenes
```

**AMT (Premium Quality)**
```
Pros:
- Best occlusion handling
- Highest quality
- Complex motion support

Cons:
- Very slow (10x slower than RIFE)
- High VRAM requirement
- Overkill for simple content

Best for:
- Complex scenes with occlusion
- Maximum quality requirements
- Post-production work
```

### Interpolation Strategies

**For AI-Generated Video:**
```
1. Smooth first (SVI_TemporalSmooth 0.2-0.3)
2. Interpolate 2x (FILM)
3. Optional: Light smooth again (0.1)

Why: AI video has frame-level inconsistency
that interpolation amplifies if not smoothed first
```

**For Slow-Motion Effect:**
```
1. Interpolate 4x or 8x
2. Keep original FPS in output
3. Result: 4x or 8x slower playback
4. Use FILM for best quality
```

**For Smooth Playback:**
```
1. Start: 24fps source
2. Interpolate 2x
3. Output: 48fps
4. OR Interpolate 2.5x → 60fps
```

### Frame Timing Formulas

```
Output FPS = Source FPS × Interpolation Factor

Slow-mo factor = Interpolation Factor (keeping same output FPS)

Example:
- 24fps source, 4x interpolate, 24fps output = 4x slow motion
- 24fps source, 2x interpolate, 48fps output = smooth playback
- 30fps source, 2x interpolate, 60fps output = smooth 60fps
```

### Handling Scene Cuts

**Problem:** Interpolation between different scenes creates artifacts

**Solution:**
```
1. SVI_SceneDetect (threshold 0.4-0.5)
2. Outputs: scene_cuts list
3. Feed to SVI_FrameInterpolation
4. Interpolation restarts at each cut
```

### Memory vs Quality Trade-off

```
| Setting | VRAM | Quality | Speed |
|---------|------|---------|-------|
| RIFE 2x | Low  | Good    | Fast  |
| RIFE 4x | Low  | Medium  | Fast  |
| FILM 2x | Med  | Great   | Slow  |
| FILM 4x | Med  | Great   | Slow  |
| AMT 2x  | High | Best    | Very Slow |
```

## VIDEO-TO-VIDEO TECHNIQUES

### Style Transfer (Maintain Motion)

**Method: Per-Frame img2img**
```
For each frame:
1. VAEEncode
2. KSampler (denoise 0.4-0.6)
3. VAEDecode

Post-process:
4. SVI_TemporalSmooth (0.3-0.4)
5. Recombine frames
```

**denoise guide:**
```
0.3-0.4: Subtle style change, preserve detail
0.5-0.6: Noticeable change, may lose some detail
0.7-0.8: Major restyle, motion may drift
```

### ControlNet Video Transfer

**Preserve Structure + Change Style:**
```
1. Extract depth maps per frame (MiDaS batch)
2. For each frame:
   - ControlNet depth
   - New style prompt
   - KSampler
3. SVI_TemporalSmooth
4. Recombine
```

**Preserve Motion + Change Subject:**
```
1. Extract optical flow / pose per frame
2. Use as ControlNet sequence
3. Generate new subject following motion
4. Post-smooth
```

### Upscale Video Pipeline

**Standard Pipeline:**
```
1. Load video → frames
2. Light temporal smooth (0.15)
3. Per-frame upscale (RealESRGAN)
4. OPTIONAL: Per-frame refinement (img2img denoise 0.2)
5. Interpolate 2x for smooth playback
6. Final temporal smooth (0.1)
7. Export at target FPS
```

**Best Upscale Models for Video:**
```
RealESRGAN_x4plus - General purpose, good motion
RealESRGAN_x4plus_anime_6B - Anime content
SwinIR - High detail preservation
ESRGAN_4x - Classic, reliable
```

### Colorize/Restore Old Video

```
1. Load B&W or damaged video
2. Per frame:
   - Colorization model (DeOldify, etc)
   - OR ControlNet with color reference
3. Heavy temporal smooth (0.4-0.5) for consistency
4. Interpolate if source was low FPS
5. Export
```

### Replace Background in Video

```
1. Segment foreground per frame (SAM)
2. Generate new background sequence
3. Composite foreground onto new background
4. Edge blend/feather
5. Temporal smooth edges only
```

### Face Swap in Video

```
1. Extract frames
2. Detect faces per frame (RetinaFace)
3. For each frame with face:
   - Crop face region
   - Apply face swap (ReActor, roop)
   - Blend back
4. Temporal smooth on face region
5. Color match if needed
6. Recombine
```

### Denoising/Restoration

```
For noisy/compressed video:
1. Load video
2. Per-frame denoise (or use video denoiser)
3. Light sharpening to recover detail
4. Temporal smooth (light, 0.1-0.2)
5. OPTIONAL: AI upscale to enhance
```

### Combine Real + AI Video

```
1. Record real footage
2. Extract relevant elements (mask)
3. Generate AI background/elements
4. Composite with proper masking
5. Match lighting/color
6. Add temporal consistency
```
