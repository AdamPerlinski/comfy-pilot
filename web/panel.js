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
    this.currentModel = "";
    this.availableAgents = {};
    this.systemInfo = null;
    this.includeWorkflow = false;
    this.contextMode = localStorage.getItem("comfy-pilot-context-mode") || "standard";
    this.knowledgeCategories = null; // null = all enabled
    this.contextOptionsOpen = false;

    this.lastDetectedWorkflow = null;

    this.container = null;
    this.messagesContainer = null;
    this.inputField = null;
    this.sendButton = null;
    this.agentSelect = null;
    this.modelSelect = null;
    this.workflowToggle = null;
  }

  async init() {
    await this.refreshAgents();
    this.createPanel();
    this.registerMenuButton();
    this.loadSavedCategories();
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

  async fetchKnowledgeCategories() {
    try {
      const response = await api.fetchApi("/comfy-pilot/knowledge-categories");
      if (response.ok) {
        const categories = await response.json();
        this.updateCategoryCheckboxes(categories);
      }
    } catch (e) {
      console.error("Failed to fetch knowledge categories:", e);
    }
  }

  loadSavedCategories() {
    const saved = localStorage.getItem("comfy-pilot-categories");
    if (saved) {
      try {
        this.knowledgeCategories = JSON.parse(saved);
      } catch (e) {
        this.knowledgeCategories = null;
      }
    }
  }

  createPanel() {
    this.container = document.createElement("div");
    this.container.id = "comfy-pilot-panel";
    this.container.innerHTML = `
      <div class="cp-header">
        <h3>Comfy Pilot</h3>
        <select class="cp-agent-select"></select>
        <select class="cp-model-select" style="display:none"></select>
        <button class="cp-new-chat" title="New Chat">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" y1="18" x2="12" y2="12"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
          </svg>
        </button>
        <button class="cp-close" title="Close">&times;</button>
      </div>
      <div class="cp-system-info">
        <span class="gpu-info">Loading system info...</span>
      </div>
      <div class="cp-context-panel">
        <button class="cp-context-toggle">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M3 12h18"/></svg>
          Context Options
          <span class="cp-context-mode-badge">${this.contextMode}</span>
        </button>
        <div class="cp-context-body" style="display:none">
          <div class="cp-context-row">
            <label>Context mode:</label>
            <select class="cp-context-mode">
              <option value="minimal"${this.contextMode === "minimal" ? " selected" : ""}>Minimal (5K)</option>
              <option value="standard"${this.contextMode === "standard" ? " selected" : ""}>Standard (15K)</option>
              <option value="verbose"${this.contextMode === "verbose" ? " selected" : ""}>Verbose (30K)</option>
            </select>
          </div>
          <div class="cp-categories">
            <label>Knowledge:</label>
            <div class="cp-category-list">Loading...</div>
          </div>
        </div>
      </div>
      <div class="cp-messages"></div>
      <div class="cp-workflow-context">
        <label class="cp-toggle">
          <input type="checkbox" class="cp-workflow-toggle">
          <span class="toggle-label">Include current workflow</span>
        </label>
        <span class="workflow-status"></span>
      </div>
      <div class="cp-persistent-actions" style="display:none">
        <span class="cp-detected-label">Workflow detected</span>
        <button class="cp-btn-validate">Validate</button>
        <button class="cp-btn-apply">Apply</button>
        <button class="cp-btn-log">Log</button>
      </div>
      <div class="cp-input-area">
        <textarea
          class="cp-input"
          placeholder="Ask me to create or modify a workflow..."
          rows="2"
        ></textarea>
        <button class="cp-send">Send</button>
      </div>
      <div class="cp-footer">
        Created by <a href="https://github.com/AdamPerlinski" target="_blank">Adam Perli\u0144ski</a>
      </div>
    `;

    this.applyStyles();

    // Get references
    this.messagesContainer = this.container.querySelector(".cp-messages");
    this.inputField = this.container.querySelector(".cp-input");
    this.sendButton = this.container.querySelector(".cp-send");
    this.agentSelect = this.container.querySelector(".cp-agent-select");
    this.modelSelect = this.container.querySelector(".cp-model-select");
    this.workflowToggle = this.container.querySelector(".cp-workflow-toggle");
    this.workflowStatus = this.container.querySelector(".workflow-status");

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
      this.updateModelSelect();
    });

    this.modelSelect.addEventListener("change", (e) => {
      this.currentModel = e.target.value;
    });

    this.workflowToggle.addEventListener("change", (e) => {
      this.includeWorkflow = e.target.checked;
      this.updateWorkflowStatus();
    });

    this.container.querySelector(".cp-close").addEventListener("click", () => {
      this.hide();
    });

    this.container.querySelector(".cp-new-chat").addEventListener("click", () => {
      this.resetChat();
    });

    // Context options toggle
    const ctxToggle = this.container.querySelector(".cp-context-toggle");
    const ctxBody = this.container.querySelector(".cp-context-body");
    ctxToggle.addEventListener("click", () => {
      this.contextOptionsOpen = !this.contextOptionsOpen;
      ctxBody.style.display = this.contextOptionsOpen ? "block" : "none";
      if (this.contextOptionsOpen) {
        this.fetchKnowledgeCategories();
      }
    });

    // Context mode change
    this.container.querySelector(".cp-context-mode").addEventListener("change", (e) => {
      this.contextMode = e.target.value;
      localStorage.setItem("comfy-pilot-context-mode", this.contextMode);
      this.container.querySelector(".cp-context-mode-badge").textContent = this.contextMode;
    });

    // Persistent actions bar
    const persistentBar = this.container.querySelector(".cp-persistent-actions");
    persistentBar.querySelector(".cp-btn-validate").addEventListener("click", async () => {
      if (!this.lastDetectedWorkflow) return;
      await this.validateWorkflowUI(this.lastDetectedWorkflow, persistentBar);
    });
    persistentBar.querySelector(".cp-btn-apply").addEventListener("click", async () => {
      if (!this.lastDetectedWorkflow) return;
      const btn = persistentBar.querySelector(".cp-btn-apply");
      btn.textContent = "Validating...";
      btn.disabled = true;
      try {
        // Validate first
        const valResponse = await api.fetchApi("/comfy-pilot/validate-workflow", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ workflow: this.lastDetectedWorkflow }),
        });
        const valResult = await valResponse.json();
        if (!valResult.valid) {
          btn.textContent = "Invalid!";
          btn.style.background = "var(--cp-danger)";
          await this.validateWorkflowUI(this.lastDetectedWorkflow, persistentBar);
          setTimeout(() => { btn.textContent = "Apply"; btn.style.background = ""; btn.disabled = false; }, 2000);
          return;
        }
        // Apply
        btn.textContent = "Applying...";
        await this.applyWorkflow(this.lastDetectedWorkflow);
        btn.textContent = "Applied!";
        btn.style.background = "var(--cp-success)";
      } catch (e) {
        btn.textContent = "Failed";
        btn.style.background = "var(--cp-danger)";
      }
      setTimeout(() => {
        btn.textContent = "Apply";
        btn.style.background = "";
        btn.disabled = false;
      }, 2000);
    });
    persistentBar.querySelector(".cp-btn-log").addEventListener("click", () => {
      if (!this.lastDetectedWorkflow) return;
      console.log("[comfy-pilot] Workflow JSON:", this.lastDetectedWorkflow);
      console.log("[comfy-pilot] Workflow (formatted):", JSON.stringify(this.lastDetectedWorkflow, null, 2));
      const btn = persistentBar.querySelector(".cp-btn-log");
      btn.textContent = "Logged!";
      setTimeout(() => { btn.textContent = "Log"; }, 1500);
    });

    document.body.appendChild(this.container);
    this.hide();
  }

  applyStyles() {
    if (document.getElementById("comfy-pilot-styles")) return;

    const styles = document.createElement("style");
    styles.id = "comfy-pilot-styles";
    styles.textContent = `
      :root {
        --cp-bg: var(--comfy-menu-bg, #1a1a2e);
        --cp-bg-secondary: var(--comfy-input-bg, #2a2a3e);
        --cp-border: var(--border-color, #333);
        --cp-text: var(--fg-color, #fff);
        --cp-text-dim: var(--fg-color, #888);
        --cp-accent: var(--p-button-text-primary-color, #4a9eff);
        --cp-success: #28a745;
        --cp-danger: #dc3545;
        --cp-warning: #ffc107;
        --cp-radius: 8px;
      }

      #comfy-pilot-panel {
        position: fixed;
        top: 50px;
        right: 20px;
        width: 420px;
        height: 620px;
        background: var(--cp-bg);
        border: 1px solid var(--cp-border);
        border-radius: var(--cp-radius);
        display: flex;
        flex-direction: column;
        z-index: 10000;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5);
        font-family: system-ui, -apple-system, sans-serif;
        font-size: 14px;
        color: var(--cp-text);
      }

      /* Header */
      .cp-header {
        display: flex;
        align-items: center;
        padding: 10px 12px;
        border-bottom: 1px solid var(--cp-border);
        gap: 8px;
      }
      .cp-header h3 {
        margin: 0;
        flex-grow: 1;
        font-size: 15px;
        font-weight: 600;
      }
      .cp-agent-select, .cp-model-select {
        background: var(--cp-bg-secondary);
        color: var(--cp-text);
        border: 1px solid var(--cp-border);
        border-radius: 4px;
        padding: 4px 6px;
        font-size: 12px;
        max-width: 120px;
      }
      .cp-new-chat, .cp-close {
        background: none;
        border: none;
        color: var(--cp-text-dim);
        cursor: pointer;
        padding: 4px 6px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .cp-new-chat:hover, .cp-close:hover {
        color: var(--cp-text);
        background: rgba(255,255,255,0.1);
      }
      .cp-close { font-size: 22px; line-height: 1; }

      /* System info */
      .cp-system-info {
        padding: 6px 12px;
        font-size: 11px;
        color: var(--cp-text-dim);
        background: var(--cp-bg-secondary);
        border-bottom: 1px solid var(--cp-border);
      }

      /* Context panel */
      .cp-context-panel {
        border-bottom: 1px solid var(--cp-border);
      }
      .cp-context-toggle {
        display: flex;
        align-items: center;
        gap: 6px;
        width: 100%;
        padding: 6px 12px;
        background: none;
        border: none;
        color: var(--cp-text-dim);
        cursor: pointer;
        font-size: 12px;
        text-align: left;
      }
      .cp-context-toggle:hover { color: var(--cp-text); background: rgba(255,255,255,0.03); }
      .cp-context-mode-badge {
        margin-left: auto;
        background: var(--cp-bg-secondary);
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .cp-context-body {
        padding: 8px 12px;
        background: var(--cp-bg-secondary);
        border-top: 1px solid var(--cp-border);
      }
      .cp-context-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .cp-context-row label { font-size: 12px; color: var(--cp-text-dim); white-space: nowrap; }
      .cp-context-mode {
        background: var(--cp-bg);
        color: var(--cp-text);
        border: 1px solid var(--cp-border);
        border-radius: 4px;
        padding: 3px 6px;
        font-size: 12px;
        flex: 1;
      }
      .cp-categories label { font-size: 12px; color: var(--cp-text-dim); display: block; margin-bottom: 4px; }
      .cp-category-list {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        font-size: 11px;
      }
      .cp-category-chip {
        display: flex;
        align-items: center;
        gap: 3px;
        padding: 2px 8px;
        background: var(--cp-bg);
        border: 1px solid var(--cp-border);
        border-radius: 12px;
        cursor: pointer;
        user-select: none;
      }
      .cp-category-chip.active { border-color: var(--cp-accent); background: rgba(74,158,255,0.1); }
      .cp-category-chip input { display: none; }

      /* Messages */
      .cp-messages {
        flex-grow: 1;
        overflow-y: auto;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .cp-message {
        padding: 8px 12px;
        border-radius: var(--cp-radius);
        max-width: 90%;
        word-wrap: break-word;
        line-height: 1.5;
        font-size: 13px;
      }
      .cp-message.user {
        background: var(--cp-bg-secondary);
        align-self: flex-end;
        border-bottom-right-radius: 2px;
      }
      .cp-message.assistant {
        background: var(--p-surface-700, #252538);
        color: var(--fg-color, #ddd);
        align-self: flex-start;
        border-bottom-left-radius: 2px;
      }
      .cp-message pre {
        background: #1a1a2a;
        padding: 8px;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 11px;
        margin: 6px 0;
      }
      .cp-message code { font-family: monospace; }

      /* Workflow actions */
      .cp-workflow-actions {
        display: flex;
        gap: 6px;
        margin-top: 8px;
        flex-wrap: wrap;
      }
      .cp-workflow-actions button {
        border: none;
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 11px;
        font-weight: 500;
        color: white;
      }
      .cp-workflow-actions button:hover { opacity: 0.9; }
      .cp-btn-apply { background: var(--cp-accent); }
      .cp-btn-validate { background: #6c757d; }
      .cp-btn-log { background: #6c757d; }
      .cp-btn-fix { background: var(--cp-warning); color: #000; }

      /* Validation result */
      .cp-validation-result {
        margin-top: 6px;
        padding: 6px 8px;
        border-radius: 4px;
        font-size: 11px;
      }
      .cp-validation-result.valid { background: rgba(40,167,69,0.15); color: #28a745; }
      .cp-validation-result.invalid { background: rgba(220,53,69,0.15); color: #dc3545; }
      .cp-validation-result ul { margin: 4px 0 0 16px; padding: 0; }

      /* Collapsible messages */
      .cp-message.collapsed .cp-msg-content {
        max-height: 120px;
        overflow: hidden;
        mask-image: linear-gradient(to bottom, #000 60%, transparent 100%);
        -webkit-mask-image: linear-gradient(to bottom, #000 60%, transparent 100%);
      }
      .cp-msg-toggle {
        display: block;
        background: none;
        border: none;
        color: var(--cp-accent);
        cursor: pointer;
        font-size: 11px;
        padding: 2px 0;
        margin-top: 2px;
      }
      .cp-msg-toggle:hover { text-decoration: underline; }
      .cp-validation-result.collapsed .cp-val-details { display: none; }
      .cp-val-toggle {
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
        font-size: 11px;
        opacity: 0.8;
        padding: 0;
        margin-left: 6px;
      }
      .cp-val-toggle:hover { opacity: 1; }

      /* Workflow context */
      .cp-workflow-context {
        display: flex;
        align-items: center;
        padding: 6px 12px;
        gap: 8px;
        border-top: 1px solid var(--cp-border);
        background: var(--cp-bg-secondary);
      }
      .cp-toggle {
        display: flex;
        align-items: center;
        gap: 5px;
        cursor: pointer;
        font-size: 12px;
        color: var(--cp-text-dim);
      }
      .cp-toggle input { cursor: pointer; }
      .cp-toggle:hover { color: var(--cp-text); }
      .workflow-status { font-size: 11px; color: var(--cp-text-dim); }

      /* Persistent actions bar */
      .cp-persistent-actions {
        display: flex;
        align-items: center;
        padding: 6px 12px;
        gap: 6px;
        border-top: 1px solid var(--cp-border);
        background: var(--cp-bg-secondary);
      }
      .cp-persistent-actions .cp-detected-label {
        font-size: 11px;
        color: var(--cp-text-dim);
        flex: 1;
      }
      .cp-persistent-actions button {
        border: none;
        padding: 4px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 11px;
        font-weight: 500;
        color: white;
      }
      .cp-persistent-actions button:hover { opacity: 0.9; }
      .cp-persistent-actions .cp-btn-validate { background: #6c757d; }
      .cp-persistent-actions .cp-btn-apply { background: var(--cp-accent); }
      .cp-persistent-actions .cp-btn-log { background: #6c757d; }

      /* Input */
      .cp-input-area {
        display: flex;
        padding: 10px;
        gap: 6px;
      }
      .cp-input {
        flex-grow: 1;
        background: var(--cp-bg-secondary);
        color: var(--cp-text);
        border: 1px solid var(--cp-border);
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 13px;
        resize: none;
        font-family: inherit;
      }
      .cp-input:focus {
        outline: none;
        border-color: var(--cp-accent);
      }
      .cp-send {
        background: var(--cp-accent);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
      }
      .cp-send:hover { opacity: 0.9; }
      .cp-send:disabled { opacity: 0.5; cursor: not-allowed; }

      /* Footer */
      .cp-footer {
        padding: 6px 12px;
        font-size: 10px;
        color: var(--cp-text-dim);
        text-align: center;
        border-top: 1px solid var(--cp-border);
        opacity: 0.4;
      }
      .cp-footer a { color: inherit; text-decoration: none; }
      .cp-footer a:hover { text-decoration: underline; }

      /* Menu button */
      #comfy-pilot-menu-button {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: transparent;
        border: none;
        color: var(--cp-text);
        cursor: pointer;
        font-size: 14px;
      }
      #comfy-pilot-menu-button:hover {
        background: var(--cp-bg-secondary);
        border-radius: 4px;
      }

      .comfy-pilot-hidden { display: none !important; }

      /* Thinking */
      .cp-thinking {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        color: var(--cp-text-dim);
        font-size: 12px;
      }
      .thinking-dots {
        display: flex;
        gap: 3px;
      }
      .thinking-dots span {
        animation: cp-pulse 1.4s infinite ease-in-out both;
        font-size: 8px;
      }
      .thinking-dots span:nth-child(1) { animation-delay: 0s; }
      .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
      .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes cp-pulse {
        0%, 80%, 100% { opacity: 0.3; }
        40% { opacity: 1; }
      }
      .thinking-text { font-style: italic; opacity: 0.7; }
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

    this.updateModelSelect();
  }

  updateModelSelect() {
    const info = this.availableAgents[this.currentAgent];
    if (!info || !info.models || info.models.length === 0) {
      this.modelSelect.style.display = "none";
      this.currentModel = "";
      return;
    }

    this.modelSelect.style.display = "";
    this.modelSelect.innerHTML = "";

    for (const model of info.models) {
      const option = document.createElement("option");
      option.value = model;
      option.textContent = model;
      this.modelSelect.appendChild(option);
    }

    this.currentModel = info.models[0];
    this.modelSelect.value = this.currentModel;
  }

  updateCategoryCheckboxes(categories) {
    const listEl = this.container.querySelector(".cp-category-list");
    if (!listEl) return;
    listEl.innerHTML = "";

    const savedCategories = this.knowledgeCategories;

    for (const [category, titles] of Object.entries(categories)) {
      const chip = document.createElement("label");
      chip.className = "cp-category-chip";
      const isActive = !savedCategories || savedCategories.includes(category);
      if (isActive) chip.classList.add("active");

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = isActive;
      cb.value = category;

      cb.addEventListener("change", () => {
        chip.classList.toggle("active", cb.checked);
        this.saveCategories();
      });

      chip.appendChild(cb);
      chip.appendChild(document.createTextNode(category));
      listEl.appendChild(chip);
    }
  }

  saveCategories() {
    const checkboxes = this.container.querySelectorAll(".cp-category-list input[type=checkbox]");
    const active = [];
    let allChecked = true;
    for (const cb of checkboxes) {
      if (cb.checked) active.push(cb.value);
      else allChecked = false;
    }

    if (allChecked) {
      this.knowledgeCategories = null;
      localStorage.removeItem("comfy-pilot-categories");
    } else {
      this.knowledgeCategories = active;
      localStorage.setItem("comfy-pilot-categories", JSON.stringify(active));
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
      if (app.graph) {
        return app.graph.serialize();
      }
      return null;
    } catch (e) {
      console.error("Failed to get current workflow:", e);
      return null;
    }
  }

  getWorkflowSummary(workflow) {
    if (!workflow || !workflow.nodes) return null;
    return {
      nodeCount: workflow.nodes.length,
      nodeTypes: {},
      connections: workflow.links?.length || 0,
    };
  }

  updateWorkflowStatus() {
    if (!this.includeWorkflow) {
      this.workflowStatus.textContent = "";
      return;
    }
    const workflow = this.getCurrentWorkflow();
    if (workflow) {
      const summary = this.getWorkflowSummary(workflow);
      this.workflowStatus.textContent = summary ? `(${summary.nodeCount} nodes)` : "(empty)";
    } else {
      this.workflowStatus.textContent = "(no workflow)";
    }
  }

  registerMenuButton() {
    const checkMenu = setInterval(() => {
      const selectors = [
        ".comfyui-menu .comfyui-menu-right",
        ".comfyui-menu-right",
        ".comfy-menu-btns",
        "header nav",
        ".comfyui-menu",
        "#comfyui-body-top",
      ];

      let menuContainer = null;
      for (const selector of selectors) {
        menuContainer = document.querySelector(selector);
        if (menuContainer) break;
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
      }
    }, 500);

    setTimeout(() => {
      clearInterval(checkMenu);
      this.createFloatingButton();
    }, 2000);
  }

  createFloatingButton() {
    this.isButtonMinimized = localStorage.getItem("comfy-pilot-minimized") === "true";

    const container = document.createElement("div");
    container.id = "comfy-pilot-floating-container";
    container.style.cssText = `
      position: fixed; bottom: 20px; right: 20px; z-index: 9999;
      display: flex; flex-direction: column; align-items: flex-end; gap: 8px;
    `;

    const button = document.createElement("button");
    button.id = "comfy-pilot-floating-button";
    button.title = "Open Comfy Pilot - AI Assistant";

    const minimizeBtn = document.createElement("button");
    minimizeBtn.id = "comfy-pilot-minimize-btn";
    minimizeBtn.title = "Minimize";
    minimizeBtn.innerHTML = "\u2212";
    minimizeBtn.style.cssText = `
      position: absolute; top: -8px; right: -8px; width: 20px; height: 20px;
      border-radius: 50%; background: #444; border: 2px solid #222;
      color: white; font-size: 14px; line-height: 1; cursor: pointer;
      display: none; align-items: center; justify-content: center;
    `;

    const wrapper = document.createElement("div");
    wrapper.style.cssText = "position: relative;";
    wrapper.appendChild(button);
    wrapper.appendChild(minimizeBtn);
    container.appendChild(wrapper);

    const updateButtonStyle = () => {
      if (this.isButtonMinimized) {
        button.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;
        button.style.cssText = `
          padding: 10px; border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none; cursor: pointer; display: flex; align-items: center;
          justify-content: center; box-shadow: 0 2px 10px rgba(102,126,234,0.3);
          color: white; transition: transform 0.2s, box-shadow 0.2s; opacity: 0.7;
        `;
        minimizeBtn.innerHTML = "+";
        minimizeBtn.title = "Expand";
      } else {
        button.innerHTML = `
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span>comfy-pilot</span>
        `;
        button.style.cssText = `
          padding: 12px 16px; border-radius: 12px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none; cursor: pointer; display: flex; flex-direction: column;
          align-items: center; justify-content: center; gap: 4px;
          box-shadow: 0 4px 15px rgba(102,126,234,0.4); color: white;
          font-size: 11px; font-weight: 500; font-family: system-ui, -apple-system, sans-serif;
          transition: transform 0.2s, box-shadow 0.2s;
        `;
        minimizeBtn.innerHTML = "\u2212";
        minimizeBtn.title = "Minimize";
      }
    };

    updateButtonStyle();

    wrapper.addEventListener("mouseenter", () => {
      minimizeBtn.style.display = "flex";
      if (!this.isButtonMinimized) {
        button.style.transform = "scale(1.05)";
        button.style.boxShadow = "0 6px 20px rgba(102,126,234,0.5)";
      } else {
        button.style.opacity = "1";
      }
    });
    wrapper.addEventListener("mouseleave", () => {
      minimizeBtn.style.display = "none";
      if (!this.isButtonMinimized) {
        button.style.transform = "scale(1)";
        button.style.boxShadow = "0 4px 15px rgba(102,126,234,0.4)";
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
    this.includeWorkflow = false;
    this.workflowToggle.checked = false;
    this.updateWorkflowStatus();
    this.lastDetectedWorkflow = null;
    this.updatePersistentActions();
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

    this.addMessage("user", text);
    this.inputField.value = "";

    this.isStreaming = true;
    this.sendButton.disabled = true;
    this.sendButton.textContent = "...";

    this.addThinkingIndicator();

    try {
      const payload = {
        agent: this.currentAgent,
        message: text,
        history: this.messages.slice(-20),
        context_mode: this.contextMode,
      };

      if (this.currentModel) {
        payload.model = this.currentModel;
      }

      if (this.knowledgeCategories) {
        payload.knowledge_categories = this.knowledgeCategories;
      }

      if (this.includeWorkflow) {
        try {
          const workflow = this.getCurrentWorkflow();
          if (workflow) payload.current_workflow = workflow;
        } catch (e) {
          console.warn("[comfy-pilot] Failed to get workflow for context:", e);
        }
      }

      const response = await api.fetchApi("/comfy-pilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

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
    thinkingEl.className = "cp-thinking";
    thinkingEl.innerHTML = `
      <span class="thinking-dots"><span>\u25cf</span><span>\u25cf</span><span>\u25cf</span></span>
      <span class="thinking-text">Thinking...</span>
    `;
    this.messagesContainer.appendChild(thinkingEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

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
    const thinking = this.messagesContainer.querySelector(".cp-thinking");
    if (thinking) thinking.remove();
  }

  addMessage(role, content) {
    this.messages.push({ role, content });

    const messageEl = document.createElement("div");
    messageEl.className = `cp-message ${role}`;

    const contentEl = document.createElement("div");
    contentEl.className = "cp-msg-content";
    contentEl.innerHTML = this.formatContent(content);
    messageEl.appendChild(contentEl);

    // Collapse long messages (> 500 chars)
    if (content.length > 500) {
      messageEl.classList.add("collapsed");
      const toggle = document.createElement("button");
      toggle.className = "cp-msg-toggle";
      toggle.textContent = "\u25bc Show more";
      toggle.addEventListener("click", () => {
        const isCollapsed = messageEl.classList.toggle("collapsed");
        toggle.textContent = isCollapsed ? "\u25bc Show more" : "\u25b2 Show less";
      });
      messageEl.appendChild(toggle);
    }

    this.messagesContainer.appendChild(messageEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    return messageEl;
  }

  updateMessage(messageEl, content) {
    let contentEl = messageEl.querySelector(".cp-msg-content");
    if (contentEl) {
      contentEl.innerHTML = this.formatContent(content);
    } else {
      messageEl.innerHTML = this.formatContent(content);
    }
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    // Add/update collapse toggle for long messages
    if (content.length > 500 && !messageEl.querySelector(".cp-msg-toggle")) {
      if (!contentEl) {
        const wrapper = document.createElement("div");
        wrapper.className = "cp-msg-content";
        wrapper.innerHTML = messageEl.innerHTML;
        messageEl.innerHTML = "";
        messageEl.appendChild(wrapper);
        contentEl = wrapper;
      }
      messageEl.classList.add("collapsed");
      const toggle = document.createElement("button");
      toggle.className = "cp-msg-toggle";
      toggle.textContent = "\u25bc Show more";
      toggle.addEventListener("click", () => {
        const isCollapsed = messageEl.classList.toggle("collapsed");
        toggle.textContent = isCollapsed ? "\u25bc Show more" : "\u25b2 Show less";
      });
      messageEl.appendChild(toggle);
    }

    const lastMsg = this.messages[this.messages.length - 1];
    if (lastMsg) lastMsg.content = content;
  }

  formatContent(content) {
    return content
      .replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");
  }

  checkForWorkflow(messageEl, content) {
    const jsonMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (!jsonMatch) return;

    let workflow;
    try {
      workflow = JSON.parse(jsonMatch[1]);
    } catch (e) {
      return;
    }

    const hasNodes = Object.values(workflow).some(
      (v) => typeof v === "object" && v !== null && v.class_type
    );
    if (!hasNodes) return;

    // Track the last detected workflow for the persistent bar
    this.lastDetectedWorkflow = workflow;
    this.updatePersistentActions();

    // Inline marker on the message
    const marker = document.createElement("div");
    marker.className = "cp-workflow-actions";
    marker.innerHTML = `<span style="font-size:11px;color:var(--cp-text-dim)">Workflow detected (${Object.keys(workflow).length} nodes) - use buttons below to validate/apply</span>`;
    messageEl.appendChild(marker);
  }

  updatePersistentActions() {
    const bar = this.container.querySelector(".cp-persistent-actions");
    if (!bar) return;
    if (this.lastDetectedWorkflow) {
      const count = Object.keys(this.lastDetectedWorkflow).length;
      bar.style.display = "flex";
      bar.querySelector(".cp-detected-label").textContent = `Workflow detected (${count} nodes)`;
      // Remove old validation results
      const oldResult = bar.parentElement.querySelector(".cp-persistent-actions + .cp-validation-result");
      if (oldResult) oldResult.remove();
    } else {
      bar.style.display = "none";
    }
  }

  async validateWorkflowUI(workflow, container) {
    // Remove existing validation results near this container
    const parent = container.parentElement || container;
    parent.querySelectorAll(".cp-validation-result").forEach((el) => el.remove());

    try {
      const response = await api.fetchApi("/comfy-pilot/validate-workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflow }),
      });
      const result = await response.json();

      const resultDiv = document.createElement("div");
      resultDiv.className = `cp-validation-result ${result.valid ? "valid" : "invalid"}`;

      if (result.valid) {
        resultDiv.innerHTML = `<strong>\u2713 Valid</strong> (${result.node_count} nodes${result.validated_against_registry ? ", checked against registry" : ""})`;
      } else {
        let html = `<strong>\u2717 Invalid</strong> (${result.errors.length} error${result.errors.length !== 1 ? "s" : ""})`;
        html += `<button class="cp-val-toggle">\u25bc details</button>`;
        html += `<div class="cp-val-details"><ul>`;
        for (const err of result.errors) {
          html += `<li>${err.message}${err.suggestion ? ` <em>${err.suggestion}</em>` : ""}</li>`;
        }
        html += "</ul>";

        if (result.warnings?.length) {
          html += `<div style="margin-top:4px;color:#ffc107"><strong>Warnings:</strong></div><ul>`;
          for (const w of result.warnings) {
            html += `<li>${w.message}</li>`;
          }
          html += "</ul>";
        }
        html += "</div>";

        resultDiv.innerHTML = html;

        // Toggle validation details
        const valToggle = resultDiv.querySelector(".cp-val-toggle");
        valToggle.addEventListener("click", () => {
          resultDiv.classList.toggle("collapsed");
          valToggle.textContent = resultDiv.classList.contains("collapsed") ? "\u25bc details" : "\u25b2 hide";
        });

        // Add "Ask agent to fix" button
        const fixBtn = document.createElement("button");
        fixBtn.className = "cp-btn-fix";
        fixBtn.textContent = "Ask agent to fix";
        fixBtn.style.marginTop = "6px";
        fixBtn.addEventListener("click", () => {
          const errorText = result.errors.map((e) => e.message).join("\n");
          this.inputField.value = `The workflow has validation errors:\n${errorText}\n\nPlease fix these errors and provide a corrected workflow.`;
          this.sendMessage();
        });
        resultDiv.appendChild(fixBtn);
      }

      (parent || container).appendChild(resultDiv);
    } catch (e) {
      console.error("Validation failed:", e);
    }
  }

  async applyWorkflow(workflow) {
    try {
      const format = this.detectWorkflowFormat(workflow);

      if (format === "api") {
        await this.loadApiWorkflow(workflow);
      } else if (format === "graph") {
        await this.loadGraphWorkflow(workflow);
      } else {
        throw new Error("Unknown workflow format");
      }
    } catch (error) {
      console.error("[comfy-pilot] Failed to apply workflow:", error);
      console.log("[comfy-pilot] Workflow JSON to copy:", JSON.stringify(workflow, null, 2));
      throw error;
    }
  }

  detectWorkflowFormat(workflow) {
    if (workflow.nodes && Array.isArray(workflow.nodes)) return "graph";
    const keys = Object.keys(workflow);
    if (keys.length > 0 && workflow[keys[0]]?.class_type) return "api";
    if (workflow.output && typeof workflow.output === "object") {
      return this.detectWorkflowFormat(workflow.output);
    }
    return "unknown";
  }

  async loadApiWorkflow(apiWorkflow) {
    try {
      if (app.loadApiJson) {
        await app.loadApiJson(apiWorkflow);
        return;
      }

      if (app.graph) {
        app.graph.clear();
        const nodeIdMap = {};

        for (const [id, nodeData] of Object.entries(apiWorkflow)) {
          const node = window.LiteGraph.createNode(nodeData.class_type);
          if (node) {
            node.id = parseInt(id);
            nodeIdMap[id] = node;

            if (nodeData.inputs) {
              for (const [inputName, inputValue] of Object.entries(nodeData.inputs)) {
                if (!Array.isArray(inputValue)) {
                  const widget = node.widgets?.find((w) => w.name === inputName);
                  if (widget) widget.value = inputValue;
                }
              }
            }

            const idx = parseInt(id);
            node.pos = [150 + (idx % 5) * 300, 100 + Math.floor(idx / 5) * 200];
            app.graph.add(node);
          } else {
            console.warn(`[comfy-pilot] Unknown node type: ${nodeData.class_type}`);
          }
        }

        for (const [id, nodeData] of Object.entries(apiWorkflow)) {
          if (!nodeData.inputs) continue;
          const targetNode = nodeIdMap[id];
          if (!targetNode) continue;

          for (const [inputName, inputValue] of Object.entries(nodeData.inputs)) {
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

        app.graph.setDirtyCanvas(true, true);
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
        return;
      }
      if (app.graph && app.graph.configure) {
        app.graph.configure(graphWorkflow);
        app.graph.setDirtyCanvas(true, true);
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
app.registerExtension({
  name: "comfy-pilot",
  async setup() {
    try {
      const panel = new ComfyPilotPanel();
      await panel.init();
      window.comfyPilot = panel;
      console.log("[comfy-pilot] Setup complete!");
    } catch (error) {
      console.error("[comfy-pilot] Setup failed:", error);
    }
  },
});
