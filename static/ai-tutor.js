/**
 * AI 小助手 - 增強版本（可拖動 + 預設打開）
 * 用於旁通道攻擊分析平臺
 */

(function(window) {
  'use strict';

  const DEFAULTS = {
    apiEndpoint: '/api/ai/chat',
    platformName: '旁通道攻擊分析平臺',
    language: 'zh-TW',
    maxHistoryLength: 10,
    autoOpen: false,  
    draggable: true  // 可拖動
  };

  class AITutorWidget {
    constructor(config = {}) {
      this.config = { ...DEFAULTS, ...config };
      this.isOpen = false;
      this.isLoading = false;
      this.conversationHistory = [];
      this.isDragging = false;
      this.dragStartX = 0;
      this.dragStartY = 0;
      this.offsetX = 0;
      this.offsetY = 0;
      
      this.init();
    }

    init() {
      this.setupDOM();
      this.attachEventListeners();
      this.setupStyles();
      this.loadHistory();
      
      // 預設打開
      //if (this.config.autoOpen) {
      //  setTimeout(() => this.open(), 300);
      //}
    }

    setupDOM() {
      if (document.getElementById('ai-tutor-bubble')) {
        this.bubble = document.getElementById('ai-tutor-bubble');
      } else {
        this.bubble = this.createBubbleDOM();
        document.body.appendChild(this.bubble);
      }

      this.toggleBtn = this.bubble.querySelector('.ai-tutor-btn');
      this.panel = this.bubble.querySelector('.ai-tutor-panel');
      this.header = this.bubble.querySelector('.ai-tutor-header');
      this.content = this.bubble.querySelector('.ai-tutor-content');
      this.input = this.bubble.querySelector('.ai-tutor-input');
      this.sendBtn = this.bubble.querySelector('.ai-tutor-send');
      this.closeBtn = this.bubble.querySelector('.ai-tutor-close');
    }

    createBubbleDOM() {
      const bubble = document.createElement('div');
      bubble.id = 'ai-tutor-bubble';
      bubble.innerHTML = `
        <style>
          .ai-tutor-bubble {
            position: fixed;
            bottom: 28px;
            right: 28px;
            z-index: 999999;
            font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
          }
          
          .ai-tutor-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #7755d9, #6b4fc1);
            border: none;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(119, 85, 217, 0.3);
            transition: all 0.3s ease;
          }
          
          .ai-tutor-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(119, 85, 217, 0.4);
          }
          
          .ai-tutor-btn.open {
            display: none;
          }
          
          .ai-tutor-panel {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 380px;
            max-height: 600px;
            background: #fff;
            border: 1px solid #d8c9ff;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
            display: none;
            flex-direction: column;
            overflow: hidden;
            animation: slideUp 0.3s ease;
          }
          
          .ai-tutor-panel.open {
            display: flex;
          }
          
          @keyframes slideUp {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          .ai-tutor-header {
            padding: 16px;
            background: linear-gradient(135deg, #f4f0ff, #f0e8ff);
            border-bottom: 1px solid #d8c9ff;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: grab;
            user-select: none;
          }
          
          .ai-tutor-header:active {
            cursor: grabbing;
          }
          
          .ai-tutor-header-title {
            font-size: 14px;
            font-weight: 700;
            color: #51349e;
            margin: 0;
          }
          
          .ai-tutor-close {
            background: none;
            border: none;
            font-size: 18px;
            color: #51349e;
            cursor: pointer;
            padding: 0;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          
          .ai-tutor-close:hover {
            opacity: 0.7;
          }
          
          .ai-tutor-content {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
          }
          
          .ai-message {
            display: flex;
            gap: 10px;
            align-items: flex-start;
            animation: fadeIn 0.3s ease;
          }
          
          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateY(10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          .ai-message.bot {
            justify-content: flex-start;
          }
          
          .ai-message.user {
            justify-content: flex-end;
          }
          
          .ai-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #7755d9;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
            flex-shrink: 0;
          }
          
          .ai-message.user .ai-avatar {
            background: #3b6ff0;
          }
          
          .ai-bubble {
            max-width: 85%;
            padding: 10px 12px;
            border-radius: 12px;
            font-size: 12px;
            line-height: 1.6;
            word-wrap: break-word;
          }
          
          .ai-message.bot .ai-bubble {
            background: #f4f0ff;
            color: #51349e;
            border: 1px solid #d8c9ff;
          }
          
          .ai-message.user .ai-bubble {
            background: #eff3ff;
            color: #1e3fa8;
            border: 1px solid #c5d3fa;
          }
          
          .ai-loading {
            display: flex;
            gap: 4px;
            align-items: center;
            height: 24px;
          }
          
          .ai-loading span {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #7755d9;
            animation: pulse 1.4s ease-in-out infinite;
          }
          
          .ai-loading span:nth-child(1) { animation-delay: -0.32s; }
          .ai-loading span:nth-child(2) { animation-delay: -0.16s; }
          
          @keyframes pulse {
            0%, 60%, 100% { opacity: 0.3; }
            30% { opacity: 1; }
          }
          
          .ai-tutor-footer {
            padding: 12px 16px;
            border-top: 1px solid #d8c9ff;
            display: flex;
            gap: 8px;
          }
          
          .ai-input-wrap {
            flex: 1;
            display: flex;
          }
          
          .ai-tutor-input {
            flex: 1;
            border: 1px solid #e0e2ea;
            border-radius: 8px;
            padding: 8px 12px;
            font-family: 'Noto Sans TC', sans-serif;
            font-size: 12px;
            color: #1a1d2e;
            background: #f0f1f4;
            resize: none;
            max-height: 80px;
          }
          
          .ai-tutor-input:focus {
            outline: none;
            border-color: #7755d9;
            background: #fff;
          }
          
          .ai-tutor-input::placeholder {
            color: #7a7f9a;
          }
          
          .ai-tutor-send {
            background: #7755d9;
            border: none;
            color: #fff;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: all 0.2s ease;
            flex-shrink: 0;
            margin-left: 8px;
          }
          
          .ai-tutor-send:hover:not(:disabled) {
            background: #6b4fc1;
          }
          
          .ai-tutor-send:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          @media (max-width: 480px) {
            .ai-tutor-panel {
              width: 320px;
              max-height: 500px;
            }
          }
        </style>
        
        <button class="ai-tutor-btn" title="打開 AI 小助手">✨</button>
        <div class="ai-tutor-panel">
          <div class="ai-tutor-header">
            <h3 class="ai-tutor-header-title">AI 小助手</h3>
            <button class="ai-tutor-close">×</button>
          </div>
          
          <div class="ai-tutor-content">
            <div class="ai-message bot">
              <div class="ai-avatar">AI</div>
              <div class="ai-bubble">
                👋 你好！我是 AI 小助手。有什麼問題嗎？
              </div>
            </div>
          </div>
          
          <div class="ai-tutor-footer">
            <div class="ai-input-wrap">
              <textarea 
                class="ai-tutor-input" 
                placeholder="輸入你的問題..." 
                rows="1"
              ></textarea>
              <button class="ai-tutor-send" title="發送">📤</button>
            </div>
          </div>
        </div>
      `;
      
      return bubble;
    }

    attachEventListeners() {
      this.toggleBtn.addEventListener('click', () => this.toggle());
      this.closeBtn.addEventListener('click', () => this.close());
      this.sendBtn.addEventListener('click', () => this.sendMessage());

      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });

      this.input.addEventListener('input', () => {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 80) + 'px';
      });

      // 拖動功能
      if (this.config.draggable) {
        this.header.addEventListener('mousedown', (e) => this.startDrag(e));
        document.addEventListener('mousemove', (e) => this.drag(e));
        document.addEventListener('mouseup', () => this.endDrag());
      }
    }

    startDrag(e) {
      this.isDragging = true;
      this.dragStartX = e.clientX;
      this.dragStartY = e.clientY;
      
      const rect = this.panel.getBoundingClientRect();
      this.offsetX = rect.left;
      this.offsetY = rect.top;
    }

    drag(e) {
      if (!this.isDragging) return;
      
      const deltaX = e.clientX - this.dragStartX;
      const deltaY = e.clientY - this.dragStartY;
      
      const newX = this.offsetX + deltaX;
      const newY = this.offsetY + deltaY;
      
      // 限制在視窗內
      const maxX = window.innerWidth - this.panel.offsetWidth;
      const maxY = window.innerHeight - this.panel.offsetHeight;
      
      const clampedX = Math.max(0, Math.min(newX, maxX));
      const clampedY = Math.max(0, Math.min(newY, maxY));
      
      this.panel.style.position = 'fixed';
      this.panel.style.left = clampedX + 'px';
      this.panel.style.top = clampedY + 'px';
      this.panel.style.right = 'auto';
      this.panel.style.bottom = 'auto';
    }

    endDrag() {
      this.isDragging = false;
    }

    toggle() {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    }

    open() {
      this.isOpen = true;
      this.panel.classList.add('open');
      this.toggleBtn.classList.add('open');
      this.input.focus();
    }

    close() {
      this.isOpen = false;
      this.panel.classList.remove('open');
      this.toggleBtn.classList.remove('open');
    }

    async sendMessage() {
      const message = this.input.value.trim();
      if (!message || this.isLoading) return;

      this.input.value = '';
      this.input.style.height = 'auto';
      this.sendBtn.disabled = true;
      this.isLoading = true;

      this.addMessage(message, 'user');
      const loadingId = this.showLoading();

      try {
        const response = await this.callAPI(message);
        this.removeLoading(loadingId);
        this.addMessage(response, 'bot');
      } catch (error) {
        this.removeLoading(loadingId);
        this.addMessage(
          `❌ 發生錯誤：${error.message || '無法連線到服務'}`,
          'bot'
        );
        console.error('AI Tutor Error:', error);
      } finally {
        this.isLoading = false;
        this.sendBtn.disabled = false;
      }
    }

    async callAPI(userMessage) {
      this.conversationHistory.push({
        role: 'user',
        content: userMessage
      });

      try {
        const response = await fetch(this.config.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            messages: this.conversationHistory
          }),
          timeout: 30000
        });

        if (!response.ok) {
          throw new Error(`API 錯誤: ${response.statusText}`);
        }

        const data = await response.json();
        const assistantMessage = data.content;

        this.conversationHistory.push({
          role: 'model',
          content: assistantMessage
        });

        if (this.conversationHistory.length > this.config.maxHistoryLength) {
          this.conversationHistory = this.conversationHistory.slice(-this.config.maxHistoryLength);
        }

        this.saveHistory();
        return assistantMessage;
      } catch (error) {
        throw new Error(error.message || '無法連線到 AI 服務');
      }
    }

    addMessage(text, role) {
      const message = document.createElement('div');
      message.className = `ai-message ${role}`;

      const avatar = document.createElement('div');
      avatar.className = 'ai-avatar';
      avatar.textContent = role === 'bot' ? 'AI' : 'You';

      const bubble = document.createElement('div');
      bubble.className = 'ai-bubble';
      bubble.textContent = text;

      if (role === 'bot') {
        message.appendChild(avatar);
        message.appendChild(bubble);
      } else {
        message.appendChild(bubble);
        message.appendChild(avatar);
      }

      this.content.appendChild(message);
      this.scrollToBottom();
    }

    showLoading() {
      const id = Math.random().toString(36);
      const message = document.createElement('div');
      message.className = 'ai-message bot';
      message.id = `loading-${id}`;

      const avatar = document.createElement('div');
      avatar.className = 'ai-avatar';
      avatar.textContent = 'AI';

      const bubble = document.createElement('div');
      bubble.className = 'ai-loading';
      bubble.innerHTML = '<span></span><span></span><span></span>';

      message.appendChild(avatar);
      message.appendChild(bubble);
      this.content.appendChild(message);
      this.scrollToBottom();

      return id;
    }

    removeLoading(id) {
      const element = document.getElementById(`loading-${id}`);
      if (element) {
        element.remove();
      }
    }

    scrollToBottom() {
      this.content.scrollTop = this.content.scrollHeight;
    }

    saveHistory() {
      try {
        const historyToSave = this.conversationHistory.slice(-5);
        localStorage.setItem(
          'ai-tutor-history',
          JSON.stringify(historyToSave)
        );
      } catch (error) {
        console.warn('無法保存對話歷史:', error);
      }
    }

    loadHistory() {
      try {
        const saved = localStorage.getItem('ai-tutor-history');
        if (saved) {
          this.conversationHistory = JSON.parse(saved);
        }
      } catch (error) {
        console.warn('無法載入對話歷史:', error);
      }
    }
  }

  // 全域 API
  window.AITutor = {
    instance: null,

    init: function(config = {}) {
      this.instance = new AITutorWidget(config);
      return this.instance;
    },

    open: function() {
      if (this.instance) this.instance.open();
    },

    close: function() {
      if (this.instance) this.instance.close();
    },

    toggle: function() {
      if (this.instance) this.instance.toggle();
    },

    sendMessage: function(message) {
      if (this.instance) {
        this.instance.input.value = message;
        this.instance.sendMessage();
      }
    }
  };

})(window);
