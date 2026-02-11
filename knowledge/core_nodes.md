---
id: core_nodes
title: Core ComfyUI Nodes
keywords: [KSampler, checkpoint, VAEDecode, CLIPTextEncode, latent, LoRA, ControlNet, sampler, scheduler, EmptyLatentImage, SaveImage, LoadImage, SDXL, FLUX, SD3, UNETLoader, DualCLIPLoader, VAELoader, LoraLoader, ControlNetApply, ImageUpscaleWithModel, tiling, VAEDecodeTiled, optimization, VRAM]
category: core
priority: high
---

## Core ComfyUI Nodes

### Checkpoint & Model Loading

- **CheckpointLoaderSimple**: Loads .safetensors/.ckpt checkpoint
  - Outputs: MODEL, CLIP, VAE
  - Input: ckpt_name (filename in models/checkpoints/)

- **UNETLoader**: Loads just the UNET (for FLUX, SD3, etc.)
  - Outputs: MODEL
  - Input: unet_name, weight_dtype (fp8_e4m3fn, fp8_e5m2, etc.)

- **DualCLIPLoader**: Loads two CLIP models (for SDXL, FLUX)
  - Outputs: CLIP
  - Input: clip_name1, clip_name2, type (sdxl, flux)

- **TripleCLIPLoader**: For SD3 (three text encoders)
  - Outputs: CLIP
  - Input: clip_name1, clip_name2, clip_name3

- **VAELoader**: Loads separate VAE
  - Outputs: VAE
  - Input: vae_name

- **LoraLoader**: Applies LoRA to model
  - Inputs: model, clip, lora_name, strength_model, strength_clip
  - Outputs: MODEL, CLIP

- **LoraLoaderModelOnly**: LoRA without CLIP modification
  - Inputs: model, lora_name, strength_model
  - Outputs: MODEL

### Text Encoding

- **CLIPTextEncode**: Basic text encoding
  - Inputs: text, clip
  - Outputs: CONDITIONING

- **CLIPTextEncodeSDXL**: SDXL-specific encoding with dimensions
  - Inputs: text_g, text_l, clip, width, height, crop_w, crop_h, target_width, target_height
  - Outputs: CONDITIONING

- **CLIPTextEncodeFlux**: FLUX text encoding
  - Inputs: clip, clip_l, t5xxl, guidance
  - Outputs: CONDITIONING

- **ConditioningCombine**: Combines multiple conditionings
- **ConditioningConcat**: Concatenates conditionings
- **ConditioningSetArea**: Sets area for regional prompting
- **ConditioningSetMask**: Applies mask to conditioning

### Latent Operations

- **EmptyLatentImage**: Creates empty latent
  - Inputs: width, height, batch_size
  - Outputs: LATENT

- **EmptySD3LatentImage**: For SD3 (16-channel latent)
- **EmptyMochiLatentVideo**: For Mochi video
- **EmptyHunyuanLatentVideo**: For Hunyuan video

- **VAEEncode**: Image to latent
- **VAEDecode**: Latent to image
- **VAEDecodeTiled**: Tiled decoding for large images (low VRAM)
  - tile_size: 512 default, lower = less VRAM
- **VAEEncodeTiled**: Tiled encoding for large images

- **LatentUpscale**: Upscale latent (nearest/bilinear/area/bicubic)
- **LatentUpscaleBy**: Upscale by factor
- **LatentComposite**: Composite latents together
- **LatentBlend**: Blend two latents

### Samplers

- **KSampler**: Main sampler
  - Inputs: model, positive, negative, latent_image, seed, steps, cfg, sampler_name, scheduler, denoise
  - Outputs: LATENT
  - Samplers: euler, euler_ancestral, heun, dpm_2, dpm_2_ancestral, lms, dpm_fast, dpm_adaptive, dpmpp_2s_ancestral, dpmpp_sde, dpmpp_2m, dpmpp_2m_sde, ddim, uni_pc
  - Schedulers: normal, karras, exponential, sgm_uniform, simple, ddim_uniform, beta

- **KSamplerAdvanced**: More control over start/end steps
- **SamplerCustom**: Full custom sampler configuration
- **SamplerCustomAdvanced**: For advanced sampling workflows

### Image Operations

- **LoadImage**: Load image from disk
- **SaveImage**: Save image to output folder
- **PreviewImage**: Preview without saving
- **ImageScale**: Resize image
- **ImageScaleBy**: Resize by factor
- **ImageUpscaleWithModel**: Use upscale model (ESRGAN, etc.)
- **ImageBlend**: Blend images
- **ImageComposite**: Composite with mask
- **ImageInvert**: Invert colors
- **ImageSharpen**: Sharpen image
- **ImageBlur**: Blur image

## Model Types & Architectures

### Stable Diffusion 1.5

- Resolution: 512x512 native
- VRAM: ~4GB minimum
- Latent: 4 channels
- Checkpoint: Single file with UNET, CLIP, VAE
- Fast, many LoRAs available

### Stable Diffusion 2.x

- Resolution: 512x512 or 768x768
- Uses different CLIP (OpenCLIP)
- Less community adoption

### SDXL (Stable Diffusion XL)

- Resolution: 1024x1024 native
- VRAM: ~8GB minimum, 12GB+ recommended
- Two text encoders (CLIP-G, CLIP-L)
- Better quality, more detail
- Loading: CheckpointLoaderSimple or separate UNET+CLIP+VAE

### SDXL Turbo / Lightning

- Distilled SDXL for fast generation
- 1-4 steps only
- CFG: 1.0-2.0
- No negative prompt needed

### SD3 / SD3.5

- Resolution: 1024x1024
- Three text encoders (CLIP-G, CLIP-L, T5-XXL)
- 16-channel latent
- Nodes: TripleCLIPLoader, EmptySD3LatentImage
- Better text rendering

### FLUX

- Resolution: Various (512-2048)
- Two text encoders (CLIP-L, T5-XXL)
- Guidance embedded in model
- Very high quality
- VRAM: 12GB+ (fp8), 24GB+ (fp16)
- Loading: UNETLoader + DualCLIPLoader + VAELoader
- Variants: FLUX.1-dev, FLUX.1-schnell (fast)

### Cascade

- Two-stage generation
- Stage A: 1024x1024 latent
- Stage B: Decode to full resolution
- Very high quality

### PixArt

- Transformer-based
- Good quality, efficient
- PixArt-Sigma, PixArt-Alpha

### Hunyuan-DiT

- Chinese/English bilingual
- Good quality
- Different architecture

## Common Workflow Patterns

### Basic txt2img

1. CheckpointLoaderSimple -> MODEL, CLIP, VAE
2. CLIPTextEncode (positive) -> CONDITIONING
3. CLIPTextEncode (negative) -> CONDITIONING
4. EmptyLatentImage -> LATENT
5. KSampler -> LATENT
6. VAEDecode -> IMAGE
7. SaveImage

### img2img

1. LoadImage -> IMAGE
2. VAEEncode -> LATENT (instead of EmptyLatentImage)
3. KSampler with denoise < 1.0 (0.4-0.8 typical)

### Inpainting

1. LoadImage (original)
2. LoadImage (mask) - white = inpaint area
3. VAEEncodeForInpaint or SetLatentNoiseMask
4. KSampler
5. VAEDecode

### ControlNet

1. Load ControlNet model (ControlNetLoader)
2. Preprocess image if needed (Canny, OpenPose, Depth, etc.)
3. ControlNetApply or ControlNetApplyAdvanced
4. Connect to KSampler positive conditioning

### Two-Pass / Hires Fix

Pass 1: Generate at lower resolution
1. EmptyLatentImage (512x512 or 768x768)
2. KSampler (full steps)
3. VAEDecode

Pass 2: Upscale and refine
4. ImageScale or LatentUpscale (to target res)
5. VAEEncode (if using ImageScale)
6. KSampler (denoise 0.4-0.6, fewer steps)
7. VAEDecode
8. SaveImage

### SDXL with Refiner

1. Base model generation (steps 1-20)
2. Switch to refiner model
3. Continue sampling (steps 20-30)
- Use KSamplerAdvanced for step control

### Regional Prompting

1. Create masks for regions
2. ConditioningSetMask for each region
3. ConditioningCombine all regions
4. Single KSampler

### IP-Adapter (Image Prompt)

1. LoadImage (reference)
2. IPAdapterLoader
3. IPAdapterApply
4. Connect to model before KSampler

## Tiling & Large Image Generation

### Why Tiling?

- VRAM limited: Can't process entire large image at once
- Tiling processes image in chunks
- Essential for high-resolution (2K, 4K+)

### VAE Tiling (Built-in)

- **VAEDecodeTiled**: Decode large latents with low VRAM
  - tile_size: 512 default, lower = less VRAM
- **VAEEncodeTiled**: Encode large images with low VRAM

### Tiled Diffusion (Custom Node)

- **TiledDiffusion**: Process sampling in tiles
  - Inputs: model, tile_width, tile_height, tile_overlap
  - Enables generation of very large images
  - Requires: ComfyUI-TiledDiffusion

### Tiled KSampler

- Some custom nodes offer tiled sampling
- Process each tile separately
- Blend at seams

### Recommended Tile Sizes

- SD 1.5: 512x512 tiles
- SDXL: 1024x1024 tiles
- Overlap: 64-128 pixels

### Memory Optimization

```
Low VRAM workflow for large images:
1. Generate at native resolution
2. VAEDecodeTiled (tile_size=256-512)
3. ImageUpscaleWithModel (tiled automatically)
4. Or use Ultimate SD Upscale node
```

### Ultimate SD Upscale

- Custom node for tiled upscaling
- Combines upscale + img2img in tiles
- Handles seams intelligently
- Inputs: image, model, tile_width, tile_height, seam_fix_mode

## Video Generation

### AnimateDiff

- Adds motion to SD 1.5 checkpoints
- Motion modules: mm_sd_v15_v2, mm_sdxl_v10_beta
- Typical: 16-32 frames
- Nodes:
  - AnimateDiffLoaderWithContext
  - AnimateDiffUniformContextOptions
  - AnimateDiffCombine (output)
- VRAM: 8GB+ for 16 frames

### SVD (Stable Video Diffusion)

- Image-to-video
- Input: Single image
- Output: 14-25 frames
- Nodes: SVD_img2vid_Conditioning, VideoLinearCFGGuidance
- VRAM: 12GB+

### WAN 2.1 / WAN 2.2 (Wan Show / Hunyuan Video)

- High quality video generation
- Text-to-video and image-to-video
- WAN 2.1: Original release
- WAN 2.2: Improved quality, better motion

WAN Workflow:
1. Download WAN model (HunyuanVideo or similar)
2. EmptyHunyuanLatentVideo (frames, height, width)
3. Use appropriate text encoder
4. Special sampler settings
5. VAE decode frames

### Mochi

- Text-to-video model
- High quality motion
- Nodes: EmptyMochiLatentVideo
- Requires specific VAE

### CogVideoX

- Another video model
- Good quality, efficient
- Specific loading nodes

### LTX Video

- Fast video generation
- Lower VRAM requirements
- Growing popularity

### Video Workflow Tips

1. Start with fewer frames (8-16) for testing
2. Use fp8 models when possible
3. Batch size 1 for video
4. Consider temporal consistency nodes
5. Frame interpolation for smoother output

### Video Frame Handling

- **VHS_VideoCombine**: Combine frames to video
- **LoadVideoPath**: Load video as frames
- **FILM**: Frame interpolation (2x, 4x frames)

## Advanced Techniques

### Two-Pass Generation (Hires Fix)

Purpose: Generate higher quality images than native resolution allows

Method 1: Latent Upscale
1. Generate at 512x512 (SD1.5) or 1024x1024 (SDXL)
2. LatentUpscale to 2x
3. KSampler with denoise 0.5-0.7
4. VAEDecode

Method 2: Image Upscale + img2img
1. Generate at native resolution
2. VAEDecode
3. ImageUpscaleWithModel (ESRGAN, etc.)
4. VAEEncode
5. KSampler with denoise 0.3-0.5
6. VAEDecode

### Multi-LoRA Stacking

- Apply multiple LoRAs sequentially
- Each LoraLoader chains: model -> LoRA -> model
- Adjust strengths (0.5-0.8 each typically)
- Order can matter!

### CFG Rescale / Dynamic CFG

- Reduce artifacts at high CFG
- ModelSamplingDiscrete nodes
- RescaleCFG custom node

### Perturbed Attention Guidance (PAG)

- Better detail without artifacts
- PerturbedAttention node
- Alternative to high CFG

### Self-Attention Guidance (SAG)

- Improved coherence
- SelfAttentionGuidance node

### FreeU

- Enhanced detail, free improvement
- FreeU_V2 node
- Parameters: b1, b2, s1, s2

### Kohya Deep Shrink

- Memory optimization
- Processes at lower resolution internally
- PatchModelAddDownscale node

### IP-Adapter

- Use images as prompts
- Face consistency
- Style transfer
- Variants: Plus, Plus Face, Full Face

### InstantID

- Face identity preservation
- Better than IP-Adapter for faces
- Requires face embedding

### ControlNet Types

- Canny: Edge detection
- Depth: Depth maps (MiDaS, Zoe)
- OpenPose: Body/hand/face poses
- Scribble: Rough sketches
- Tile: Detail preservation
- Inpaint: Inpainting control
- Lineart: Line drawings
- SoftEdge: Soft edges (HED, PiDi)
- Shuffle: Style transfer
- Reference: Image reference (not true ControlNet)

## Essential Custom Nodes

### ComfyUI Manager (MUST HAVE)

- Install/update custom nodes
- Missing node detection
- Model downloads

### Efficiency Nodes

- Efficient Loader: Combined checkpoint+VAE+LoRA
- Efficient KSampler: Preview + save in one
- XY Plot: Parameter comparison

### WAS Node Suite

- Tons of image processing nodes
- Text operations
- Math nodes
- Essential utilities

### Impact Pack

- Detailer: Face/hand fixing
- SAM (Segment Anything)
- SEGS operations
- Batch processing

### ControlNet Auxiliary

- All preprocessors for ControlNet
- Canny, OpenPose, Depth, etc.

### ComfyUI-AnimateDiff-Evolved

- AnimateDiff implementation
- Motion modules
- Video output

### ComfyUI-VideoHelperSuite

- Video loading/saving
- Frame manipulation
- Essential for video workflows

### Ultimate SD Upscale

- Tiled upscaling
- img2img in tiles
- Seam handling

### ComfyUI-TiledDiffusion

- Tiled sampling
- Large image generation

### rgthree

- Context nodes
- Power LoRA Loader
- Image Comparer
- Useful utilities

### Crystools

- Various quality of life nodes
- Metadata handling
- Useful for automation

### KJNodes

- Conditioning manipulation
- Mask operations
- Useful utilities

### IPAdapter Plus

- Latest IP-Adapter implementation
- Face models
- Style models

## Optimization & VRAM Tips

### VRAM Requirements (Approximate)

- SD 1.5: 4GB minimum, 6GB comfortable
- SDXL: 8GB minimum, 12GB comfortable
- FLUX fp8: 12GB minimum, 16GB comfortable
- FLUX fp16: 24GB minimum
- Video (16 frames): 12GB+
- Video (32+ frames): 16GB+

### Memory Saving Techniques

1. **Use fp8 models when available**
   - FLUX fp8, SDXL fp8
   - Half the memory of fp16

2. **VAE Tiling**
   - Always use VAEDecodeTiled for large images
   - tile_size=256 for very low VRAM

3. **Attention Optimization**
   - --use-pytorch-cross-attention (startup flag)
   - xformers if compatible

4. **Model Offloading**
   - --lowvram or --medvram flags
   - Moves unused models to CPU

5. **Batch Size**
   - Use batch_size=1 for low VRAM
   - Higher batch = more VRAM but faster

6. **Resolution**
   - Generate at native res, upscale after
   - Don't generate directly at 4K!

7. **Disable Preview**
   - Previews use VRAM
   - Disable for maximum available memory

### Speed Optimization

1. **Compiled Models**
   - --use-compiled-model (startup)
   - Faster after first run

2. **TensorRT**
   - Significant speedup for NVIDIA
   - Requires conversion

3. **Appropriate Step Count**
   - SD 1.5: 20-30 steps
   - SDXL: 25-40 steps
   - FLUX: 20-30 steps
   - Turbo/Lightning: 1-4 steps

4. **Sampler Choice**
   - DPM++ 2M Karras: Good quality/speed
   - Euler: Fast, good for many steps
   - DPM++ SDE: High quality, slower

### Common Mistakes to Avoid

- Don't generate at resolution model wasn't trained for
- Don't use CFG > 10 without rescale
- Don't forget negative prompt (except for Turbo/Lightning)
- Don't stack too many LoRAs at full strength
- Don't use wrong VAE for model
