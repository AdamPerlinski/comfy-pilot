/**
 * comfy-pilot - Main panel UI
 *
 * Creates a chat panel in ComfyUI's menu for interacting with AI agents.
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

class ComfyPilotPanel {
  constructor() {
    this.messages = [];
    this.isStreaming = false;
    this.currentAgent = "ollama";
    this.availableAgents = {};
    this.systemInfo = null;
    this.includeWorkflow = false;

    this.container = null;
    this.messagesContainer = null;
    this.inputField = null;
    this.sendButton = null;
    this.agentSelect = null;
    this.workflowToggle = null;
  }

  async init() {
    // Fetch available agents
    await this.refreshAgents();

    // Create the panel UI
    this.createPanel();

    // Register with ComfyUI menu
    this.registerMenuButton();
  }

  async refreshAgents() {
    try {
      const response = await api.fetchApi("/comfy-pilot/agents");
      if (response.ok) {
        this.availableAgents = await response.json();
      }
    } catch (e) {
      console.error("Failed to fetch agents:", e);
    }
  }

  async refreshSystemInfo() {
    try {
      const response = await api.fetchApi("/comfy-pilot/system");
      if (response.ok) {
        this.systemInfo = await response.json();
        this.updateSystemDisplay();
      }
    } catch (e) {
      console.error("Failed to fetch system info:", e);
    }
  }

  createPanel() {
    this.container = document.createElement("div");
    this.container.id = "comfy-pilot-panel";
    this.container.innerHTML = `
      <div class="comfy-pilot-header">
        <h3>🤖 Comfy Pilot</h3>
        <select class="comfy-pilot-agent-select"></select>
        <button class="comfy-pilot-reset" title="Reset chat">🗑️</button>
        <button class="comfy-pilot-close" title="Close">&times;</button>
      </div>
      <div class="comfy-pilot-system-info">
        <span class="gpu-info">Loading system info...</span>
      </div>
      <div class="comfy-pilot-messages"></div>
      <div class="comfy-pilot-workflow-context">
        <label class="comfy-pilot-toggle">
          <input type="checkbox" class="comfy-pilot-workflow-toggle">
          <span class="toggle-label">Include current workflow</span>
        </label>
        <span class="workflow-status"></span>
      </div>
      <div class="comfy-pilot-input-area">
        <textarea
          class="comfy-pilot-input"
          placeholder="Ask me to create or modify a workflow..."
          rows="2"
        ></textarea>
        <button class="comfy-pilot-send">Send</button>
      </div>
      <div class="comfy-pilot-footer">
        Created by <a href="https://github.com/AdamPerlinski" target="_blank">Adam Perliński</a>
      </div>
    `;

    // Apply styles
    this.applyStyles();

    // Get references
    this.messagesContainer = this.container.querySelector(".comfy-pilot-messages");
    this.inputField = this.container.querySelector(".comfy-pilot-input");
    this.sendButton = this.container.querySelector(".comfy-pilot-send");
    this.agentSelect = this.container.querySelector(".comfy-pilot-agent-select");
    this.workflowToggle = this.container.querySelector(".comfy-pilot-workflow-toggle");
    this.workflowStatus = this.container.querySelector(".workflow-status");

    // Populate agent select
    this.updateAgentSelect();

    // Event listeners
    this.sendButton.addEventListener("click", () => this.sendMessage());
    this.inputField.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    this.agentSelect.addEventListener("change", (e) => {
      this.currentAgent = e.target.value;
    });

    this.workflowToggle.addEventListener("change", (e) => {
      this.includeWorkflow = e.target.checked;
      this.updateWorkflowStatus();
    });

    this.container.querySelector(".comfy-pilot-close").addEventListener("click", () => {
      this.hide();
    });

    this.container.querySelector(".comfy-pilot-reset").addEventListener("click", () => {
      this.resetChat();
    });

    // Add to document but keep hidden
    document.body.appendChild(this.container);
    this.hide();
  }

  applyStyles() {
    if (document.getElementById("comfy-pilot-styles")) return;

    const styles = document.createElement("style");
    styles.id = "comfy-pilot-styles";
    styles.textContent = `
      #comfy-pilot-panel {
        position: fixed;
        top: 50px;
        right: 20px;
        width: 400px;
        height: 600px;
        background: var(--comfy-menu-bg, #1a1a2e);
        border: 1px solid var(--border-color, #333);
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        z-index: 10000;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        font-family: system-ui, -apple-system, sans-serif;
      }

      .comfy-pilot-header {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color, #333);
        gap: 12px;
      }

      .comfy-pilot-header h3 {
        margin: 0;
        flex-grow: 1;
        font-size: 16px;
        color: var(--fg-color, #fff);
      }

      .comfy-pilot-agent-select {
        background: var(--comfy-input-bg, #2a2a3e);
        color: var(--fg-color, #fff);
        border: 1px solid var(--border-color, #444);
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 13px;
      }

      .comfy-pilot-reset,
      .comfy-pilot-close {
        background: none;
        border: none;
        color: var(--fg-color, #888);
        font-size: 18px;
        cursor: pointer;
        padding: 4px 8px;
        line-height: 1;
        border-radius: 4px;
      }

      .comfy-pilot-reset:hover,
      .comfy-pilot-close:hover {
        color: var(--fg-color, #fff);
        background: rgba(255,255,255,0.1);
      }

      .comfy-pilot-close {
        font-size: 24px;
      }

      .comfy-pilot-system-info {
        padding: 8px 16px;
        font-size: 12px;
        color: var(--fg-color, #888);
        background: var(--comfy-input-bg, #2a2a3e);
        border-bottom: 1px solid var(--border-color, #333);
      }

      .comfy-pilot-messages {
        flex-grow: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .comfy-pilot-message {
        padding: 10px 14px;
        border-radius: 8px;
        max-width: 90%;
        word-wrap: break-word;
        line-height: 1.5;
        font-size: 14px;
      }

      .comfy-pilot-message.user {
        background: var(--comfy-input-bg, #3a3a5e);
        color: var(--fg-color, #fff);
        align-self: flex-end;
        border-bottom-right-radius: 2px;
      }

      .comfy-pilot-message.assistant {
        background: var(--p-surface-700, #252538);
        color: var(--fg-color, #ddd);
        align-self: flex-start;
        border-bottom-left-radius: 2px;
      }

      .comfy-pilot-message pre {
        background: #1a1a2a;
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 12px;
        margin: 8px 0;
      }

      .comfy-pilot-message code {
        font-family: monospace;
      }

      .comfy-pilot-workflow-actions {
        display: flex;
        gap: 8px;
        margin-top: 8px;
      }

      .comfy-pilot-workflow-actions button {
        background: var(--p-button-text-primary-color, #4a9eff);
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
      }

      .comfy-pilot-workflow-actions button:hover {
        opacity: 0.9;
      }

      .comfy-pilot-workflow-context {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        gap: 8px;
        border-top: 1px solid var(--border-color, #333);
        background: var(--comfy-input-bg, #2a2a3e);
      }

      .comfy-pilot-toggle {
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        font-size: 12px;
        color: var(--fg-color, #aaa);
      }

      .comfy-pilot-toggle input {
        cursor: pointer;
      }

      .comfy-pilot-toggle:hover {
        color: var(--fg-color, #fff);
      }

      .workflow-status {
        font-size: 11px;
        color: var(--fg-color, #666);
      }

      .comfy-pilot-input-area {
        display: flex;
        padding: 12px;
        gap: 8px;
      }

      .comfy-pilot-input {
        flex-grow: 1;
        background: var(--comfy-input-bg, #2a2a3e);
        color: var(--fg-color, #fff);
        border: 1px solid var(--border-color, #444);
        border-radius: 6px;
        padding: 10px;
        font-size: 14px;
        resize: none;
        font-family: inherit;
      }

      .comfy-pilot-input:focus {
        outline: none;
        border-color: var(--p-button-text-primary-color, #4a9eff);
      }

      .comfy-pilot-send {
        background: var(--p-button-text-primary-color, #4a9eff);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
      }

      .comfy-pilot-send:hover {
        opacity: 0.9;
      }

      .comfy-pilot-send:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      #comfy-pilot-menu-button {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: transparent;
        border: none;
        color: var(--fg-color, #fff);
        cursor: pointer;
        font-size: 14px;
      }

      #comfy-pilot-menu-button:hover {
        background: var(--comfy-input-bg, rgba(255,255,255,0.1));
        border-radius: 4px;
      }

      .comfy-pilot-hidden {
        display: none !important;
      }

      .comfy-pilot-footer {
        padding: 8px 12px;
        font-size: 10px;
        color: var(--fg-color, #555);
        text-align: center;
        border-top: 1px solid var(--border-color, #2a2a2a);
        opacity: 0.5;
      }

      .comfy-pilot-footer a {
        color: var(--fg-color, #777);
        text-decoration: none;
      }

      .comfy-pilot-footer a:hover {
        color: var(--fg-color, #aaa);
        text-decoration: underline;
      }

      .comfy-pilot-thinking {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        color: var(--fg-color, #888);
        font-size: 13px;
      }

      .thinking-dots {
        display: flex;
        gap: 4px;
      }

      .thinking-dots span {
        animation: thinking-pulse 1.4s infinite ease-in-out both;
        font-size: 8px;
      }

      .thinking-dots span:nth-child(1) { animation-delay: 0s; }
      .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
      .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }

      @keyframes thinking-pulse {
        0%, 80%, 100% { opacity: 0.3; }
        40% { opacity: 1; }
      }

      .thinking-text {
        font-style: italic;
        opacity: 0.7;
      }
    `;
    document.head.appendChild(styles);
  }

  updateAgentSelect() {
    this.agentSelect.innerHTML = "";

    for (const [name, info] of Object.entries(this.availableAgents)) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = info.display_name;
      option.disabled = !info.available;

      if (!info.available) {
        option.textContent += " (unavailable)";
      }

      this.agentSelect.appendChild(option);
    }

    // Select first available agent
    for (const [name, info] of Object.entries(this.availableAgents)) {
      if (info.available) {
        this.currentAgent = name;
        this.agentSelect.value = name;
        break;
      }
    }
  }

  updateSystemDisplay() {
    const gpuInfo = this.container.querySelector(".gpu-info");
    if (this.systemInfo?.gpus?.length > 0) {
      const gpu = this.systemInfo.gpus[0];
      gpuInfo.textContent = `${gpu.name} | ${gpu.vram_free_mb}MB free`;
    } else {
      gpuInfo.textContent = "GPU info unavailable";
    }
  }

  getCurrentWorkflow() {
    try {
      // Get the current graph from ComfyUI
      if (app.graph) {
        // Serialize to API format
        const workflow = app.graph.serialize();
        return workflow;
      }
      return null;
    } catch (e) {
      console.error("Failed to get current workflow:", e);
      return null;
    }
  }

  getWorkflowSummary(workflow) {
    if (!workflow || !workflow.nodes) return null;

    const summary = {
      nodeCount: workflow.nodes.length,
      nodeTypes: {},
      connections: workflow.links?.length || 0
    };

    // Count node types
    for (const node of workflow.nodes) {
      const type = node.type || "Unknown";
      summary.nodeTypes[type] = (summary.nodeTypes[type] || 0) + 1;
    }

    return summary;
  }

  updateWorkflowStatus() {
    if (!this.includeWorkflow) {
      this.workflowStatus.textContent = "";
      return;
    }

    const workflow = this.getCurrentWorkflow();
    if (workflow) {
      const summary = this.getWorkflowSummary(workflow);
      if (summary) {
        this.workflowStatus.textContent = `(${summary.nodeCount} nodes)`;
      } else {
        this.workflowStatus.textContent = "(empty)";
      }
    } else {
      this.workflowStatus.textContent = "(no workflow)";
    }
  }

  registerMenuButton() {
    console.log("[comfy-pilot] Registering menu button...");

    // Wait for ComfyUI menu to be ready
    const checkMenu = setInterval(() => {
      // Try multiple selectors for different ComfyUI versions
      const selectors = [
        ".comfyui-menu .comfyui-menu-right",  // New ComfyUI frontend
        ".comfyui-menu-right",
        ".comfy-menu-btns",
        "header nav",
        ".comfyui-menu",  // Fallback to main menu
        "#comfyui-body-top",  // Another fallback
      ];

      let menuContainer = null;
      for (const selector of selectors) {
        menuContainer = document.querySelector(selector);
        if (menuContainer) {
          console.log(`[comfy-pilot] Found menu container: ${selector}`);
          break;
        }
      }

      if (menuContainer) {
        clearInterval(checkMenu);

        const button = document.createElement("button");
        button.id = "comfy-pilot-menu-button";
        button.className = "comfyui-button comfyui-menu-mobile-collapse primary";
        button.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span class="comfyui-button-text">Pilot</span>
        `;
        button.addEventListener("click", () => this.toggle());

        menuContainer.appendChild(button);
        console.log("[comfy-pilot] Menu button added successfully");
      }
    }, 500);

    // Timeout after 3 seconds - create floating button as primary UI
    setTimeout(() => {
      clearInterval(checkMenu);
      console.log("[comfy-pilot] Creating floating button");
      this.createFloatingButton();
    }, 2000);
  }

  createFloatingButton() {
    this.isButtonMinimized = localStorage.getItem("comfy-pilot-minimized") === "true";

    const container = document.createElement("div");
    container.id = "comfy-pilot-floating-container";
    container.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
    `;

    const button = document.createElement("button");
    button.id = "comfy-pilot-floating-button";
    button.title = "Open Comfy Pilot - AI Assistant";

    const minimizeBtn = document.createElement("button");
    minimizeBtn.id = "comfy-pilot-minimize-btn";
    minimizeBtn.title = "Minimize";
    minimizeBtn.innerHTML = "−";
    minimizeBtn.style.cssText = `
      position: absolute;
      top: -8px;
      right: -8px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #444;
      border: 2px solid #222;
      color: white;
      font-size: 14px;
      line-height: 1;
      cursor: pointer;
      display: none;
      align-items: center;
      justify-content: center;
    `;

    const wrapper = document.createElement("div");
    wrapper.style.cssText = "position: relative;";
    wrapper.appendChild(button);
    wrapper.appendChild(minimizeBtn);
    container.appendChild(wrapper);

    const updateButtonStyle = () => {
      if (this.isButtonMinimized) {
        button.innerHTML = `
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        `;
        button.style.cssText = `
          padding: 10px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
          color: white;
          transition: transform 0.2s, box-shadow 0.2s;
          opacity: 0.7;
        `;
        minimizeBtn.innerHTML = "+";
        minimizeBtn.title = "Expand";
      } else {
        button.innerHTML = `
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span>comfy-pilot</span>
        `;
        button.style.cssText = `
          padding: 12px 16px;
          border-radius: 12px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 4px;
          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
          color: white;
          font-size: 11px;
          font-weight: 500;
          font-family: system-ui, -apple-system, sans-serif;
          transition: transform 0.2s, box-shadow 0.2s;
        `;
        minimizeBtn.innerHTML = "−";
        minimizeBtn.title = "Minimize";
      }
    };

    updateButtonStyle();

    wrapper.addEventListener("mouseenter", () => {
      minimizeBtn.style.display = "flex";
      if (!this.isButtonMinimized) {
        button.style.transform = "scale(1.05)";
        button.style.boxShadow = "0 6px 20px rgba(102, 126, 234, 0.5)";
      } else {
        button.style.opacity = "1";
      }
    });
    wrapper.addEventListener("mouseleave", () => {
      minimizeBtn.style.display = "none";
      if (!this.isButtonMinimized) {
        button.style.transform = "scale(1)";
        button.style.boxShadow = "0 4px 15px rgba(102, 126, 234, 0.4)";
      } else {
        button.style.opacity = "0.7";
      }
    });

    button.addEventListener("click", () => this.toggle());

    minimizeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.isButtonMinimized = !this.isButtonMinimized;
      localStorage.setItem("comfy-pilot-minimized", this.isButtonMinimized);
      updateButtonStyle();
    });

    document.body.appendChild(container);
    this.floatingButton = button;
    console.log("[comfy-pilot] Floating button created");
  }

  show() {
    this.container.classList.remove("comfy-pilot-hidden");
    this.refreshAgents();
    this.refreshSystemInfo();
    this.updateWorkflowStatus();
    this.inputField.focus();
  }

  hide() {
    this.container.classList.add("comfy-pilot-hidden");
  }

  resetChat() {
    this.messages = [];
    this.messagesContainer.innerHTML = "";
    this.addMessage("assistant", "Chat reset! How can I help you with ComfyUI today?");
  }

  toggle() {
    if (this.container.classList.contains("comfy-pilot-hidden")) {
      this.show();
    } else {
      this.hide();
    }
  }

  async sendMessage() {
    const text = this.inputField.value.trim();
    if (!text || this.isStreaming) return;

    // Add user message
    this.addMessage("user", text);
    this.inputField.value = "";

    // Start streaming response
    this.isStreaming = true;
    this.sendButton.disabled = true;
    this.sendButton.textContent = "...";

    // Show thinking indicator
    const thinkingEl = this.addThinkingIndicator();

    try {
      // Build request payload
      const payload = {
        agent: this.currentAgent,
        message: text,
        history: this.messages.slice(-20) // Last 20 messages for context
      };

      // Include current workflow if toggled on
      if (this.includeWorkflow) {
        const workflow = this.getCurrentWorkflow();
        if (workflow) {
          payload.current_workflow = workflow;
        }
      }

      const response = await api.fetchApi("/comfy-pilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Stream the response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = "";
      let messageEl = null;
      let firstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        assistantMessage += chunk;

        if (firstChunk) {
          this.removeThinkingIndicator();
          firstChunk = false;
        }

        if (!messageEl) {
          messageEl = this.addMessage("assistant", assistantMessage);
        } else {
          this.updateMessage(messageEl, assistantMessage);
        }
      }

      // Check for workflow in response
      this.checkForWorkflow(messageEl, assistantMessage);

    } catch (error) {
      this.addMessage("assistant", `Error: ${error.message}`);
    } finally {
      this.isStreaming = false;
      this.sendButton.disabled = false;
      this.sendButton.textContent = "Send";
      this.removeThinkingIndicator();
    }
  }

  addThinkingIndicator() {
    const thinkingEl = document.createElement("div");
    thinkingEl.className = "comfy-pilot-thinking";
    thinkingEl.innerHTML = `
      <span class="thinking-dots">
        <span>●</span><span>●</span><span>●</span>
      </span>
      <span class="thinking-text">Thinking...</span>
    `;
    this.messagesContainer.appendChild(thinkingEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    // Cycle through funny ComfyUI community messages
    const messages = [
      "Untangling the noodles...",
      "Asking the VAE nicely...",
      "Sacrificing VRAM to the GPU gods...",
      "Reticulating splines...",
      "Have you tried more steps?",
      "CFG goes brrrrr...",
      "Consulting the LoRA council...",
      "Praying to the checkpoint...",
      "Converting creativity to latent space...",
      "Denoising my thoughts...",
      "It's not a bug, it's a feature...",
      "Training on your patience...",
      "50% done (for the last 5 minutes)...",
      "Downloading more VRAM...",
      "Blaming CLIP for everything...",
      "Just one more LoRA, I promise...",
      "Workflow.json has mass...",
      "Fighting with ComfyUI-Manager...",
      "NaN% complete...",
      "Generating excuses...",
    ];
    let idx = Math.floor(Math.random() * messages.length);
    const textEl = thinkingEl.querySelector(".thinking-text");
    if (textEl) textEl.textContent = messages[idx];

    this.thinkingInterval = setInterval(() => {
      idx = Math.floor(Math.random() * messages.length);
      if (textEl) textEl.textContent = messages[idx];
    }, 2500);

    return thinkingEl;
  }

  removeThinkingIndicator() {
    if (this.thinkingInterval) {
      clearInterval(this.thinkingInterval);
      this.thinkingInterval = null;
    }
    const thinking = this.messagesContainer.querySelector(".comfy-pilot-thinking");
    if (thinking) {
      thinking.remove();
    }
  }

  addMessage(role, content) {
    this.messages.push({ role, content });

    const messageEl = document.createElement("div");
    messageEl.className = `comfy-pilot-message ${role}`;
    messageEl.innerHTML = this.formatContent(content);

    this.messagesContainer.appendChild(messageEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    return messageEl;
  }

  updateMessage(messageEl, content) {
    messageEl.innerHTML = this.formatContent(content);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    // Update stored message
    const lastMsg = this.messages[this.messages.length - 1];
    if (lastMsg) {
      lastMsg.content = content;
    }
  }

  formatContent(content) {
    // Basic markdown-like formatting
    return content
      // Code blocks
      .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Bold
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // Newlines
      .replace(/\n/g, '<br>');
  }

  checkForWorkflow(messageEl, content) {
    // Look for JSON workflow in the message
    const jsonMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (!jsonMatch) return;

    try {
      const workflow = JSON.parse(jsonMatch[1]);

      // Check if it looks like a ComfyUI workflow
      const hasNodes = Object.values(workflow).some(
        v => typeof v === 'object' && v.class_type
      );

      if (hasNodes) {
        // Add apply button
        const actionsDiv = document.createElement("div");
        actionsDiv.className = "comfy-pilot-workflow-actions";
        actionsDiv.innerHTML = `
          <button class="apply-workflow">🚀 Apply Workflow</button>
          <button class="log-workflow">📋 Log to Console</button>
        `;

        actionsDiv.querySelector(".apply-workflow").addEventListener("click", async () => {
          const btn = actionsDiv.querySelector(".apply-workflow");
          btn.textContent = "⏳ Applying...";
          btn.disabled = true;
          try {
            await this.applyWorkflow(workflow);
            btn.textContent = "✅ Applied!";
            btn.style.background = "#28a745";
          } catch (e) {
            btn.textContent = "❌ Failed";
            btn.style.background = "#dc3545";
          }
          setTimeout(() => {
            btn.textContent = "🚀 Apply Workflow";
            btn.style.background = "";
            btn.disabled = false;
          }, 2000);
        });

        actionsDiv.querySelector(".log-workflow").addEventListener("click", () => {
          console.log("[comfy-pilot] Workflow JSON:", workflow);
          console.log("[comfy-pilot] Workflow (formatted):", JSON.stringify(workflow, null, 2));
          const btn = actionsDiv.querySelector(".log-workflow");
          btn.textContent = "✅ Logged!";
          setTimeout(() => {
            btn.textContent = "📋 Log to Console";
          }, 1500);
        });

        messageEl.appendChild(actionsDiv);
      }
    } catch (e) {
      // Not valid JSON, ignore
    }
  }

  async applyWorkflow(workflow) {
    try {
      console.log("[comfy-pilot] Applying workflow...", workflow);
      console.log("[comfy-pilot] Workflow type:", this.detectWorkflowFormat(workflow));

      const format = this.detectWorkflowFormat(workflow);

      if (format === "api") {
        // API format - convert to graph format first
        await this.loadApiWorkflow(workflow);
      } else if (format === "graph") {
        // Graph format - load directly
        await this.loadGraphWorkflow(workflow);
      } else {
        throw new Error("Unknown workflow format");
      }

      console.log("[comfy-pilot] Workflow applied successfully");
    } catch (error) {
      console.error("[comfy-pilot] Failed to apply workflow:", error);
      console.log("[comfy-pilot] Workflow JSON to copy:", JSON.stringify(workflow, null, 2));
      throw error; // Re-throw so button can show error state
    }
  }

  detectWorkflowFormat(workflow) {
    // Graph format has "nodes" array and "links" array
    if (workflow.nodes && Array.isArray(workflow.nodes)) {
      return "graph";
    }
    // API format has numbered keys with class_type
    const keys = Object.keys(workflow);
    if (keys.length > 0 && workflow[keys[0]]?.class_type) {
      return "api";
    }
    // Check if it's wrapped
    if (workflow.output && typeof workflow.output === "object") {
      return this.detectWorkflowFormat(workflow.output);
    }
    return "unknown";
  }

  async loadApiWorkflow(apiWorkflow) {
    // Method 1: Use ComfyUI's native API loading via fetch
    try {
      // ComfyUI can import API format via the /prompt endpoint structure
      // But for loading into graph, we need to convert or use app.loadApiJson if available

      if (app.loadApiJson) {
        // Newer ComfyUI has this method
        await app.loadApiJson(apiWorkflow);
        console.log("[comfy-pilot] Loaded via app.loadApiJson");
        return;
      }

      // Try to load via graph's native import
      if (app.graph) {
        // Clear and rebuild from API format
        app.graph.clear();

        // Create nodes from API format
        const nodeIdMap = {};

        for (const [id, nodeData] of Object.entries(apiWorkflow)) {
          const nodeType = nodeData.class_type;
          const node = window.LiteGraph.createNode(nodeType);

          if (node) {
            node.id = parseInt(id);
            nodeIdMap[id] = node;

            // Set widget values
            if (nodeData.inputs) {
              for (const [inputName, inputValue] of Object.entries(nodeData.inputs)) {
                // Skip connections (arrays like [nodeId, slotIndex])
                if (!Array.isArray(inputValue)) {
                  const widget = node.widgets?.find(w => w.name === inputName);
                  if (widget) {
                    widget.value = inputValue;
                  }
                }
              }
            }

            // Position nodes in a grid
            const idx = parseInt(id);
            node.pos = [150 + (idx % 5) * 300, 100 + Math.floor(idx / 5) * 200];

            app.graph.add(node);
          } else {
            console.warn(`[comfy-pilot] Unknown node type: ${nodeType}`);
          }
        }

        // Create connections
        for (const [id, nodeData] of Object.entries(apiWorkflow)) {
          if (nodeData.inputs) {
            const targetNode = nodeIdMap[id];
            if (!targetNode) continue;

            for (const [inputName, inputValue] of Object.entries(nodeData.inputs)) {
              // Connections are arrays: [sourceNodeId, sourceSlotIndex]
              if (Array.isArray(inputValue) && inputValue.length === 2) {
                const [sourceId, sourceSlot] = inputValue;
                const sourceNode = nodeIdMap[sourceId];

                if (sourceNode && targetNode) {
                  const targetSlot = targetNode.findInputSlot(inputName);
                  if (targetSlot !== -1) {
                    sourceNode.connect(sourceSlot, targetNode, targetSlot);
                  }
                }
              }
            }
          }
        }

        app.graph.setDirtyCanvas(true, true);
        console.log("[comfy-pilot] Loaded via manual node creation");
        return;
      }

      throw new Error("No suitable method to load API workflow");
    } catch (error) {
      console.error("[comfy-pilot] loadApiWorkflow error:", error);
      throw error;
    }
  }

  async loadGraphWorkflow(graphWorkflow) {
    try {
      if (app.loadGraphData) {
        await app.loadGraphData(graphWorkflow);
        console.log("[comfy-pilot] Loaded via app.loadGraphData");
        return;
      }

      if (app.graph && app.graph.configure) {
        app.graph.configure(graphWorkflow);
        app.graph.setDirtyCanvas(true, true);
        console.log("[comfy-pilot] Loaded via graph.configure");
        return;
      }

      throw new Error("No suitable method to load graph workflow");
    } catch (error) {
      console.error("[comfy-pilot] loadGraphWorkflow error:", error);
      throw error;
    }
  }
}

// Initialize when ComfyUI is ready
console.log("[comfy-pilot] Extension loading...");

app.registerExtension({
  name: "comfy-pilot",
  async setup() {
    console.log("[comfy-pilot] Setup starting...");
    try {
      const panel = new ComfyPilotPanel();
      await panel.init();

      // Expose for debugging
      window.comfyPilot = panel;
      console.log("[comfy-pilot] Setup complete! Panel available at window.comfyPilot");
    } catch (error) {
      console.error("[comfy-pilot] Setup failed:", error);
    }
  }
});
