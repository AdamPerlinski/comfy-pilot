---
id: models
title: Models, Checkpoints & LoRAs
keywords: [FLUX, SDXL, SD1.5, SD3, checkpoint, model, LoRA, Pony, Juggernaut, RealVisXL, CyberRealistic, DreamShaper, anime, NSFW, VAE, CivitAI, HuggingFace, download, video, AnimateDiff, Hunyuan, WAN, Mochi]
category: models
priority: medium
---

## TOP MODELS 2025

### FLUX Models (Current Best Quality)
- **FLUX.1-dev**: Best overall quality, 12GB+ VRAM (fp8)
- **FLUX.1-schnell**: Fast version, 4 steps, slightly lower quality
- **FLUX.1-dev-fp8**: Quantized for lower VRAM
- **FLUX-Realism**: Fine-tuned for photorealistic images
- **FLUX-Anime**: Anime/illustration style

### SDXL Top Picks
- **Juggernaut XL V9/V10**: Best all-around SDXL, photorealistic
- **RealVisXL V5.0**: Excellent photorealism
- **DreamShaper XL**: Great for fantasy/artistic
- **SDXL Lightning**: 4-step turbo model
- **SDXL Turbo**: 1-step generation
- **Zavychroma XL**: Vivid colors, artistic
- **CopaxTimelessXL**: Cinematic look
- **AlbedoBase XL**: Good base for LoRAs

### SD 1.5 Modern Picks (Still Relevant)
- **CyberRealistic V4.2**: Top photorealistic SD1.5
- **AbsoluteReality V1.8**: Another excellent realistic
- **DreamShaper 8**: Versatile all-rounder
- **ReV Animated**: Best for animation style
- **MeinaMix V11**: Anime specialist

### SD3.5 Models
- **SD3.5-Large**: Best SD3 quality
- **SD3.5-Medium**: Balanced quality/speed
- **SD3.5-Turbo**: Fast generation

## CLASSIC MODELS (Still Popular)

### Pony Diffusion (Anime/Furry Specialist)
- **Pony Diffusion V6 XL**: Most popular anime SDXL model
  - Excellent for anime, cartoon, furry art
  - Very responsive to style tags
  - Good at NSFW content (with proper tags)
  - Special tags: `score_9, score_8_up, score_7_up` for quality
  - Negative: `score_6, score_5, score_4`
  - Resolution: 1024x1024, supports various aspect ratios
  - Many LoRAs specifically made for Pony

- **AutismMix Pony**: Pony variant with enhanced quality
- **PonyXL-based merges**: Many community variants

### Deliberate (Realistic Legend)
- **Deliberate V6**: Classic photorealistic model
- Excellent skin textures, natural lighting
- Good for portraits and general photography
- Works great with negative embeddings

### RealisticVision
- **RealisticVision V6.0**: Top SD1.5 realistic model
- Photographic quality, natural colors
- Great for portraits, people, scenes
- Lower VRAM than SDXL alternatives

### Dreamlike Models
- **Dreamlike Photoreal 2.0**: Artistic photorealism
- **Dreamlike Diffusion**: General artistic

### Anything V5 (Anime Classic)
- Classic anime model
- Still used as base for many anime merges
- Lightweight, fast generation

### ChilloutMix (Asian Aesthetic)
- Specialized for Asian faces/aesthetics
- Popular for portrait work
- Many variants available

### GhostMix
- **GhostMix V2.0**: Spooky, atmospheric, horror
- Great for dark fantasy, gothic themes

### MeinaMix (Anime)
- **MeinaMix V11**: High quality anime
- Clean lines, vibrant colors
- Good LoRA compatibility

### Counterfeit
- **Counterfeit V3.0**: Anime/illustration
- Detailed backgrounds
- Good character consistency

## NSFW / ADULT MODELS

**Note**: These models are for adult content creation. Ensure compliance with local laws and platform terms.

### Top NSFW Checkpoints

**SDXL NSFW:**
- **Pony Diffusion V6 XL**: Excellent NSFW capabilities
  - Use tags: `explicit, nsfw, nude` etc.
  - Quality tags: `score_9, score_8_up`

- **AutismMix SDXL**: NSFW-capable anime
- **LEOSAM HelloWorld XL**: Photorealistic NSFW
- **XXMix_9realistic**: Realistic adult content
- **NightVision XL**: Dark/moody NSFW
- **Juggernaut XL** (some versions): Realistic NSFW capable

**SD 1.5 NSFW:**
- **AOM3 (AbyssOrangeMix3)**: Popular anime NSFW
  - A1, A2, A3 variants for different styles
- **BasilMix**: Anime NSFW specialist
- **MeinaHentai**: Explicit anime content
- **Hassaku**: Hentai-focused model
- **7th_anime**: Anime adult content
- **Grapefruit**: Hentai model
- **Perfect World**: Realistic NSFW

**FLUX NSFW:**
- **FLUX-NSFW**: Community fine-tune
- Use appropriate prompts, FLUX is more restrictive by default

### NSFW LoRAs (Work with base models)
- **Detail Tweaker**: Enhance anatomical details
- **Better Bodies**: Improved body proportions
- Various character-specific LoRAs on CivitAI

### NSFW Prompt Tips
1. Be explicit with content tags: `nude, naked, nsfw, explicit`
2. Use negative prompts: `censored, watermark, text, censor_bar`
3. For Pony: Include quality scores `score_9, score_8_up`
4. Specify poses, camera angles for better results
5. Use appropriate artist styles or LoRAs

### Important Notes
- CivitAI has NSFW filter - make account and enable in settings
- Some models are "NSFW-capable" but not default
- Always verify model license for commercial use
- Respect platform ToS where sharing

## FLUX ECOSYSTEM

### Base Models
- **FLUX.1-dev**: Full development model
  - Best quality
  - 12GB VRAM (fp8), 24GB (fp16)
  - 20-30 steps recommended

- **FLUX.1-schnell**: Fast/distilled version
  - 4 steps only
  - Lower quality but very fast
  - Good for previews/drafts

### Quantized Versions (Lower VRAM)
- **flux1-dev-fp8**: 8-bit quantized
- **flux1-dev-Q4_K_S.gguf**: 4-bit GGUF format
- **flux1-dev-Q8_0.gguf**: 8-bit GGUF format

### FLUX Fine-tunes
- **FLUX-Realism-LoRA**: Photorealistic enhancement
- **FLUX-Anime**: Anime style
- **FLUX-Koda**: Alternative style
- **RealFlux**: Realistic fine-tune

### FLUX Requirements
- CLIP-L: `clip_l.safetensors`
- T5-XXL: `t5xxl_fp16.safetensors` or `t5xxl_fp8_e4m3fn.safetensors`
- VAE: `ae.safetensors` (FLUX-specific VAE)

### FLUX LoRAs
- Trained specifically for FLUX
- Different format than SD LoRAs
- Growing ecosystem on CivitAI

### FLUX Tips
- Guidance scale in text encoder, not sampler
- CFG=1.0 in KSampler
- Works well with longer, detailed prompts
- Better text rendering than SD models

## VIDEO GENERATION MODELS

### AnimateDiff (SD 1.5 Motion)
**Motion Modules:**
- `mm_sd_v15_v2.ckpt`: Standard motion, most compatible
- `mm_sd_v15_v3.ckpt`: Improved motion quality
- `mm_sdxl_v10_beta.ckpt`: SDXL version (experimental)
- `temporaldiff-v1-animatediff.ckpt`: Alternative motion

**Best Checkpoints for AnimateDiff:**
- RealisticVision (realistic)
- ToonYou (cartoon)
- RevAnimated (anime)
- Any SD1.5 checkpoint works

### Stable Video Diffusion (SVD)
- `svd_xt_1_1.safetensors`: Image-to-video, 25 frames
- `svd_xt.safetensors`: Original version
- Input: Single image
- Output: 14-25 frames video

### WAN / Hunyuan Video
**Models:**
- `hunyuan_video_720_cfgdistill_fp8_e4m3fn.safetensors`: Main model (fp8)
- `hunyuan_video_720_bf16.safetensors`: Full precision

**Requirements:**
- Video VAE: `hunyuan_video_vae_fp32.safetensors`
- Text encoders: LLaVA + CLIP
- VRAM: 12GB+ (fp8), 24GB+ (bf16)

**Resolutions:**
- 848x480 (16:9)
- 720x480 (3:2)
- 1280x720 (HD, needs more VRAM)

### Mochi
- High quality video generation
- Text-to-video
- Specific VAE and encoders needed

### CogVideoX
- Efficient video generation
- Growing community support

### LTX Video
- Lightweight video generation
- Lower VRAM requirements
- Fast generation

## POPULAR LoRAs

### Style LoRAs

**Art Styles:**
- **Anime Lineart**: Clean anime lines
- **Watercolor**: Watercolor painting effect
- **Oil Painting**: Classical oil painting
- **Pixel Art**: Retro pixel style
- **Comic Book**: Western comic style
- **Studio Ghibli**: Ghibli-inspired
- **Makoto Shinkai**: Your Name style backgrounds

**Photography Styles:**
- **Film Grain**: Analog film look
- **Cinematic**: Movie-like lighting
- **Polaroid**: Instant camera effect
- **DSLR**: Sharp photo quality

### Character/Concept LoRAs
- Thousands on CivitAI for specific characters
- Celebrities, fictional characters, OCs
- Quality varies - check downloads/ratings

### Detail LoRAs (Universal)
- **Detail Tweaker XL**: Adjust detail level
- **Add More Details**: Enhance textures
- **Skin Texture**: Realistic skin
- **Eyes LoRA**: Better eye detail

### Pony-Specific LoRAs
- Many made specifically for Pony Diffusion
- Check CivitAI "Pony" filter
- Often use Pony-specific tags

### FLUX LoRAs
- Newer, smaller ecosystem
- Different format than SD LoRAs
- Growing rapidly on CivitAI

### LoRA Usage Tips
1. Start with strength 0.7-0.8
2. Stack max 2-3 LoRAs
3. Reduce strength when stacking
4. Some LoRAs need trigger words
5. Check compatibility (SD1.5 vs SDXL vs FLUX)

## WHERE TO DOWNLOAD MODELS

### CivitAI (civitai.com)
- **Largest collection** of SD models
- User ratings and reviews
- NSFW content (enable in settings)
- LoRAs, checkpoints, embeddings
- Free, account recommended
- Filter by base model (SD1.5, SDXL, Pony, FLUX)

### Hugging Face (huggingface.co)
- Official model releases
- FLUX, SD3, research models
- Higher quality/verified models
- API access available
- Search: "diffusers" or model name

### Stability AI
- Official SD models
- SD3.5, SDXL official
- stability.ai/membership

### Pony Diffusion Official
- Direct from creator
- Latest versions first

### Model Aggregators
- **Tensor.Art**: Alternative to CivitAI
- **AIBooru**: Model database
- **OpenModelDB**: Upscalers, misc models

### Download Tips
1. Check model hash for authenticity
2. Read model card for usage tips
3. Note trigger words if any
4. Check base model compatibility
5. Verify file size matches listed

## VAE KNOWLEDGE

### What is VAE?
- Variational Auto-Encoder
- Encodes images to/from latent space
- Affects color, detail, sharpness
- Most checkpoints include VAE, but external can be better

### Popular VAEs

**For SD 1.5:**
- `vae-ft-mse-840000-ema-pruned.safetensors`: Best general VAE
- `kl-f8-anime2.ckpt`: Anime colors
- `blessed2.vae.pt`: Community favorite

**For SDXL:**
- `sdxl_vae.safetensors`: Official SDXL VAE
- `sdxl-vae-fp16-fix`: Fixed version for fp16
- Most SDXL checkpoints include good VAE

**For FLUX:**
- `ae.safetensors`: Required FLUX VAE
- Different architecture, not compatible with SD VAEs

### VAE Tips
1. SD1.5 benefits most from external VAE
2. SDXL usually fine with built-in
3. FLUX requires its specific VAE
4. Baked VAE in checkpoint = no separate VAE needed
5. Bad VAE = washed out colors, artifacts

## QUICK RECOMMENDATIONS

### By Use Case

**Photorealistic Portraits:**
1. FLUX.1-dev (best quality, high VRAM)
2. Juggernaut XL V9 (SDXL, balanced)
3. CyberRealistic (SD1.5, low VRAM)

**Anime/Illustration:**
1. Pony Diffusion V6 XL (best anime SDXL)
2. MeinaMix V11 (SD1.5 anime)
3. NovelAI-based merges

**NSFW/Adult:**
1. Pony V6 XL (anime/general)
2. LEOSAM HelloWorld XL (realistic)
3. AOM3 (SD1.5 anime)

**Fantasy/Artistic:**
1. DreamShaper XL
2. Zavychroma XL
3. GhostMix (dark themes)

**Video Generation:**
1. WAN/Hunyuan (best quality)
2. AnimateDiff + RealisticVision (realistic)
3. AnimateDiff + ToonYou (cartoon)

### By VRAM

**4-6GB VRAM:**
- SD1.5 models only
- RealisticVision, DreamShaper 8
- Use --lowvram flag

**8GB VRAM:**
- SDXL with optimizations
- Juggernaut XL, RealVisXL
- AnimateDiff (16 frames)

**12GB VRAM:**
- FLUX fp8 comfortable
- SDXL full speed
- Hunyuan Video fp8

**16GB+ VRAM:**
- Everything runs well
- FLUX fp16
- Long video generation

### Starter Pack (Download These First)
1. **Checkpoint**: Juggernaut XL V9 or FLUX.1-dev-fp8
2. **VAE**: sdxl_vae.safetensors (if SDXL)
3. **Upscaler**: RealESRGAN_x4plus.pth
4. **Negative Embedding**: EasyNegative or badhandv4
