# 🚀 comfy-pilot

**AI assistant for ComfyUI** — Create and modify workflows through natural language conversation.

Talk to Claude, Ollama, Gemini, or other AI agents directly in ComfyUI. Describe what you want, get a working workflow.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![ComfyUI](https://img.shields.io/badge/ComfyUI-compatible-green.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)
[![GitHub stars](https://img.shields.io/github/stars/AdamPerlinski/comfy-pilot?style=social)](https://github.com/AdamPerlinski/comfy-pilot/stargazers)

> 💡 **Like this project?** Give it a ⭐ star and 👁️ watch to stay updated with new features!

> ⚠️ **ALPHA VERSION** — This project is in early development. Use at your own risk. The author is not responsible for any API costs, token usage, or other expenses incurred while using this software.

---

## 🎬 Demo

![comfy-pilot demo](demo.gif)

*Chat with AI to create workflows instantly*

---

## ✨ Features

- **💬 Chat Panel** — AI assistant directly in ComfyUI menu
- **🤖 10 AI Agents** — Ollama, llama.cpp, Claude, Gemini, OpenAI, Kilo, Aider, Open Interpreter
- **🎨 Workflow Generation** — Describe what you want, get complete workflow
- **🧠 Smart Recommendations** — Knows top models, VRAM requirements, best practices
- **📊 System Aware** — Checks your GPU/VRAM, suggests optimizations
- **🎬 Video Support** — AnimateDiff, WAN/Hunyuan, Mochi workflows
- **🔧 ComfyUI Nodes** — Use AI directly in your workflows

---

## 📦 Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/AdamPerlinski/comfy-pilot.git
cd comfy-pilot
pip install -r requirements.txt
```

Restart ComfyUI. Done! 🎉

Now setup an AI agent below.

### 🤖 Setup an AI Agent

You need at least one agent. Choose based on your needs:

<details>
<summary><b>🦙 Ollama (Recommended — Free, Local, Private)</b></summary>

Best for: Local use, privacy, no API costs

1. **Install Ollama:**
   ```bash
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Or visit: https://ollama.com/download
   ```

2. **Download a model:**
   ```bash
   ollama pull qwen2.5-coder:7b   # Recommended - best for workflow generation (4.7GB)
   ollama pull qwen2.5-coder:32b  # Best quality if you have 24GB+ VRAM (19GB)
   ollama pull llama3.2:3b         # Lightweight alternative (2GB)
   ```
   > **Recommended:** `qwen2.5-coder:7b` — best balance of quality and speed for generating ComfyUI workflows.

3. **Start Ollama:**
   ```bash
   ollama serve
   ```
   Keep this running in background.

</details>

<details>
<summary><b>🦙 llama.cpp (Free, Local, Private)</b></summary>

Best for: Local use with maximum control — always-warm model, latest llama.cpp features

1. **Build llama.cpp** ([instructions](https://github.com/ggml-org/llama.cpp)) and download a GGUF model from Hugging Face.

2. **Start llama-server:**
   ```bash
   llama-server -m your-model.gguf -ngl 99 --host 0.0.0.0 --port 11434
   ```

comfy-pilot auto-detects it on `http://localhost:11434`. To use a different host or port, set the `LLAMACPP_BASE_URL` environment variable before starting ComfyUI.

</details>

<details>
<summary><b>🟣 Claude Code (Best Quality)</b></summary>

Best for: Highest quality responses, complex workflows

> **💡 No extra API costs!** Claude Code uses your existing Claude Max ($20/mo) or Pro ($100/mo) subscription. No separate API billing.

1. **Install Claude Code:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Login with your Claude account:**
   ```bash
   claude
   ```
   Follow the prompts to authenticate with your Claude Max or Pro account.

3. **Verify:**
   ```bash
   claude --version
   ```

</details>

<details>
<summary><b>🔵 Gemini (Google)</b></summary>

**Option A: Gemini CLI**
```bash
npm install -g @anthropic-ai/gemini-cli
gemini auth  # Follow prompts
```

**Option B: Gemini API (no CLI)**
```bash
export GOOGLE_API_KEY=xxxxx
```
Get key at: https://makersuite.google.com/app/apikey

</details>

<details>
<summary><b>🟢 OpenAI / Codex</b></summary>

**Option A: Codex CLI**
```bash
npm install -g @openai/codex
export OPENAI_API_KEY=sk-xxxxx
```

**Option B: OpenAI API (no CLI)**
```bash
export OPENAI_API_KEY=sk-xxxxx
```
Get key at: https://platform.openai.com/api-keys

</details>

<details>
<summary><b>🔶 Kilo Code (Open Source Claude Alternative)</b></summary>

```bash
npm install -g kilo-code
# Configure with your preferred provider
```

</details>

<details>
<summary><b>🟡 Aider (Popular Coding Assistant)</b></summary>

```bash
pip install aider-chat

# Use with OpenAI:
export OPENAI_API_KEY=sk-xxxxx

# Or with Anthropic:
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Or with Ollama (free):
# Just have ollama running
```

</details>

<details>
<summary><b>⚫ Open Interpreter (Local Code Execution)</b></summary>

```bash
pip install open-interpreter

# Use with any provider or local models
export OPENAI_API_KEY=sk-xxxxx  # Optional
```

</details>

### Step 4: Restart ComfyUI

```bash
cd /path/to/ComfyUI
python main.py
```

### Step 5: Use It!

1. Look for **"Pilot"** button in the top menu bar
2. Click to open the chat panel
3. Select your agent from dropdown
4. Start chatting!

---

## 🎯 Quick Start Examples

### Basic Image Generation
```
You: Create a txt2img workflow with SDXL

Agent: I'll create a workflow using SDXL. Here's what you'll need:
       - Checkpoint: Juggernaut XL V9 (download from CivitAI)
       [Outputs complete workflow JSON]
       [Apply Workflow] button appears
```

### Video Generation
```
You: I want to make a video with AnimateDiff, 24 frames

Agent: For AnimateDiff you'll need:
       - SD 1.5 checkpoint (e.g., RealisticVision)
       - Motion module: mm_sd_v15_v2.ckpt
       - Custom node: ComfyUI-AnimateDiff-Evolved
       [Outputs AnimateDiff workflow]
```

### Model Recommendations
```
You: What's the best model for anime?

Agent: For anime, I recommend:
       1. Pony Diffusion V6 XL (SDXL) - Best quality
          - Use tags: score_9, score_8_up
          - Download: CivitAI
       2. MeinaMix V11 (SD1.5) - Lower VRAM
       3. NovelAI-based merges
```

### NSFW Content
```
You: I need a model for adult content

Agent: For NSFW content, here are the best options:

       Anime/Hentai:
       - Pony V6 XL with explicit tags
       - AOM3 (AbyssOrangeMix3)

       Realistic:
       - LEOSAM HelloWorld XL

       Tips: Enable NSFW filter in CivitAI settings
       [Provides workflow with appropriate settings]
```

### Low VRAM Solutions
```
You: I only have 6GB VRAM, can I do upscaling?

Agent: Yes! Use tiled VAE for low VRAM:
       - VAEEncodeTiled + VAEDecodeTiled
       - tile_size: 256-512
       - Use SD 1.5 models (CyberRealistic)
       [Outputs tiled upscale workflow]
```

### WAN 2.2 Video Generation
```
You: Create a video of an eagle flying through clouds

Agent: I'll create a WAN 2.2 workflow for this:
       - Model: hunyuan_video_720_fp8
       - Resolution: 848x480
       - Frames: 49 (about 2 seconds)
       - flow_shift: 9 for dynamic motion

       You'll need:
       - ComfyUI-WAN custom node
       - hunyuan_video model files
       [Outputs complete workflow]
```

### Video Troubleshooting
```
You: [with workflow attached] The video is flickering

Agent: I see your workflow uses:
       - CFG: 8 (too high for video)
       - No temporal smoothing

       Fixes:
       1. Lower CFG: 8 → 5-6
       2. Add SVI_TemporalSmooth node (strength 0.3)
       3. Increase context_overlap in AnimateDiff
       [Shows exact parameter changes]
```

### Custom Node Detection
```
You: Can I make a face swap video?

Agent: Checking your installed nodes...
       ✓ ComfyUI-VideoHelperSuite (video I/O)
       ✗ comfyui-reactor-node (face swap)
       ✗ ComfyUI-Impact-Pack (face detection)

       You need to install:
       1. ComfyUI-Impact-Pack
       2. comfyui-reactor-node

       Via ComfyUI Manager: Manager → Install → search "reactor"
```

---

## 🤖 Supported Agents

> **Note:** Tested with Claude Code, Ollama, and Aider. Other agents are implemented but may need additional testing. Contributions welcome!

| Agent | Status | Type | Best For | Setup |
|-------|--------|------|----------|-------|
| **Ollama** | ✅ tested | Local | Free, private, offline | `ollama serve` |
| **Claude Code** | ✅ tested | CLI | Best quality | Claude Max/Pro subscription |
| **Aider** | ✅ tested | CLI | Coding focus | `pip install aider-chat` |
| **Gemini CLI** | untested | CLI | Google ecosystem | `gemini auth` |
| **Gemini API** | untested | HTTP | No CLI needed | `GOOGLE_API_KEY` |
| **OpenAI Codex** | untested | CLI | OpenAI ecosystem | `codex` CLI |
| **OpenAI API** | untested | HTTP | No CLI needed | `OPENAI_API_KEY` |
| **Kilo Code** | untested | CLI | Open source | `kilo` CLI |
| **Open Interpreter** | untested | CLI | Code execution | `pip install open-interpreter` |

---

## 📚 Knowledge Base

comfy-pilot knows about:

### Models
- **Top 2025**: FLUX, Juggernaut XL, RealVisXL, DreamShaper XL
- **Classics**: Pony Diffusion, Deliberate, RealisticVision, MeinaMix
- **NSFW**: Pony V6, AOM3, LEOSAM HelloWorld
- **Video**: AnimateDiff, WAN 2.2/Hunyuan, SVD, Mochi, CogVideoX, LTX

### Workflows
- txt2img, img2img, inpainting
- FLUX, SDXL, SD1.5, SD3
- Two-pass / hires fix
- Tiled generation (low VRAM)
- ControlNet, LoRA, IP-Adapter
- AnimateDiff, WAN 2.2 video

### Video Generation (NEW!)
- **WAN 2.2**: Text-to-video, image-to-video, camera control
- **SVI Pro**: Frame interpolation (RIFE, FILM, AMT), temporal smoothing
- **Hunyuan Video**: Native ComfyUI support, parameter tuning
- Advanced tricks: loops, slow-motion, style transfer, upscaling

### Custom Nodes
- **Auto-detection**: Sees what's installed
- **Installation guides**: Step-by-step for each pack
- **Dependency chains**: What you need for each task
- **Usage examples**: How to wire nodes together

### Optimization
- VRAM requirements per model
- Tiling for large images
- fp8 quantization
- Memory-saving techniques

### Workflow Troubleshooting
- "Image too similar" → adjust denoise
- "Video flickering" → temporal smooth, CFG
- "Motion too subtle" → flow_shift, keywords
- And 50+ more common issues with fixes

---

## 🔧 ComfyUI Nodes

### AgenticPromptGenerator

Use AI to enhance your prompts directly in workflows.

**Inputs:**
- `description`: What you want (e.g., "a cat in space")
- `agent`: Which AI to use
- `style`: Art style (photorealistic, anime, etc.)

**Outputs:**
- `positive_prompt`: Enhanced detailed prompt
- `negative_prompt`: Quality negative prompt

---

## 🏗️ Project Structure

```
comfy-pilot/
├── __init__.py           # ComfyUI registration
├── controller.py         # HTTP API endpoints
├── agents/               # AI backends (9 agents)
│   ├── ollama.py
│   ├── claude_code.py
│   ├── gemini.py
│   ├── codex.py
│   ├── kilo.py
│   ├── aider.py
│   └── open_interpreter.py
├── knowledge/            # AI knowledge base
│   ├── comfyui_knowledge.py   # Nodes, workflows, techniques
│   ├── models_knowledge.py    # Models, LoRAs, sources
│   └── workflow_patterns.py   # Ready patterns
├── workflow/             # Templates
│   ├── templates.py      # FLUX, SDXL, video, tiling...
│   └── manipulator.py    # JSON manipulation
├── nodes/                # ComfyUI nodes
│   └── prompt_generator.py
├── system/               # Monitoring
│   └── monitor.py        # GPU/VRAM info
└── web/                  # Frontend
    └── panel.js          # Chat UI
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/comfy-pilot/agents` | GET | List available agents |
| `/comfy-pilot/system` | GET | GPU/VRAM info |
| `/comfy-pilot/chat` | POST | Chat (streaming) |
| `/comfy-pilot/models` | GET | Available ComfyUI models |

---

## 🛠️ Troubleshooting

### "Pilot" button not showing
- Restart ComfyUI completely
- Check browser console for errors
- Ensure `web/panel.js` exists

### Agent shows "unavailable"
- **Ollama**: Is `ollama serve` running?
- **Claude/Gemini/OpenAI**: Is API key set?
- **CLI agents**: Is the CLI installed? (`claude --version`)

### Workflow won't apply
- Check browser console for errors
- Verify workflow JSON is valid
- Some nodes may require custom node installation

### Out of memory
- Use tiled VAE nodes
- Reduce resolution
- Use fp8 models (FLUX)
- Try SD1.5 instead of SDXL

---

## 🤝 Contributing

Contributions welcome!

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Open Pull Request

### Adding New Agents

Create `agents/my_agent.py`:

```python
from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry

class MyAgentBackend(AgentBackend):
    @property
    def name(self) -> str:
        return "my_agent"

    @property
    def display_name(self) -> str:
        return "My Agent"

    @property
    def supported_models(self) -> list[str]:
        return ["model-1", "model-2"]

    async def is_available(self) -> bool:
        return True  # Check if agent is installed

    async def query(self, messages, config):
        # Implement streaming response
        yield "Hello from my agent!"

# Auto-register
AgentRegistry.register(MyAgentBackend)
```

Then add to `agents/__init__.py`:
```python
from . import my_agent  # noqa: F401
```

---

## ⚠️ Disclaimer

**USE AT YOUR OWN RISK.** This software is provided "as is", without warranty of any kind.

- **API Costs**: The author is NOT responsible for any API costs, token usage, or billing charges incurred while using this software with AI services (Claude, OpenAI, Gemini, etc.)
- **No Liability**: The author assumes no liability for any damages, data loss, or other issues arising from the use of this software
- **Alpha Software**: This is experimental software in early development — bugs and breaking changes are expected
- **Third-Party Services**: This software interacts with third-party AI APIs — you are responsible for complying with their terms of service

By using this software, you acknowledge that you understand and accept these terms.

---

## 📄 License

**GPL-3.0 License** — see [LICENSE](LICENSE)

This project is licensed under the GNU General Public License v3.0 to maintain compatibility with ComfyUI. This means:
- ✅ Free to use, modify, and distribute
- ✅ Commercial use allowed
- ⚠️ Derivative works must also be open source under GPL-3.0
- ⚠️ Changes must be documented

---

## 🙏 Credits

Built with:
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Ollama](https://ollama.com)
- [Claude Code](https://claude.ai)
- [Aider](https://aider.chat)

