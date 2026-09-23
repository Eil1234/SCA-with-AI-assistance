# 🔐 SCA-with-AI-Assistance

**AES-128 / AES-256 旁路攻擊分析平台 + AI 助手**

一個綜合旁路攻擊（Side-Channel Attack, SCA）分析和教學平台。集傳統密碼學攻擊、深度學習模型評估、AI 對話助手及自動報告生成於一身。使用者可實時分析加密算法的安全性，並通過 AI 獲得即時解釋、學習支持和安全評估報告。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)

---

## ✨ 核心特性

### 🎯 傳統密碼學攻擊方法

支援 6 種經典旁路攻擊算法，適用於 AES-128 和 AES-256：

- **CPA**（Correlation Power Analysis）- 相關性功率分析
- **DPA-DoM**（Difference of Means）- 平均差分功率分析
- **DPA-PCC**（Pearson Correlation）- 皮爾遜相關功率分析
- **MIA**（Mutual Information Analysis）- 互信息分析
- **Template Attack** - 模板攻擊（需預建模板）
- **SNR** - 信噪比洩漏點分析

### 🤖 AI 驅動的深度學習評估

利用預訓練深度學習模型進行 AES-128 密鑰恢復：

- **CNN**（卷積神經網路）
- **MLP**（多層感知器）
- 支援 **12 種模型組合**：
  - 洩漏模型：Identity (ID) / Hamming Weight (HW)
  - 資料集：ASCAD Fixed / ASCAD Random / CHES CTF

### 🧠 AI 驅動的分析和助手

### 智能對話助手
使用 Gemini AI 提供實時互動支持，幫助使用者理解平台和攻擊方法：

- 💬 自然語言問答 - 向平台提出任何關於旁路攻擊的問題
- 🎓 教學輔助 - 解釋攻擊原理、幫助理解結果
- ❓ 實時幫助 - 在分析過程中獲得建議

### 自動安全報告生成
分析完成後，Gemini AI 自動生成專業的安全評估報告：

- 📊 針對性分析 - 基於量測結果的深度評估
- 🔒 改進建議 - 針對發現的漏洞提出具體建議
- 📥 PDF 下載 - 完整報告導出

### ⚡ 高級功能

- **實時進度顯示** - 動態進度條追蹤分析進度
- **動態圖表生成** - 每個 byte 單獨生成結果圖表（Eileen 優化）
- **執行取消** - 可隨時停止正在進行的分析
- **PDF 報告下載** - 完整分析結果導出
- **完整 API 文檔** - 支援程式化調用

---

## 🏗️ 系統架構

```
SCA-with-AI-Assistance
│
├── 前端層 (Frontend)
│   └── platform.html         # 單頁應用（SPA）
│       ├── 攻擊配置界面
│       ├── 動態圖表展示
│       └── AI 助手聊天面板
│
├── API 層 (FastAPI Backend)
│   ├── /attack/*             # 攻擊執行端點
│   ├── /ai/*                 # AI 評估和助手端點
│   ├── /report/*             # 報告生成端點
│   └── /docs                 # 互動式 Swagger UI
│
└── 業務邏輯層
    ├── 6 個傳統攻擊模組
    ├── 2 個 AI 深度學習模型
    ├── Gemini AI 助手集成
    └── 報告生成服務
```

---

## 🚀 快速開始

### 系統要求

- **Windows 10/11** （建議）或 macOS/Linux
- **Python 3.9+**
- **Gemini API Key**（可選，無 key 時仍可使用攻擊功能）

### 安裝步驟（Windows）

#### 方法 1：自動啟動腳本（推薦 ⭐）

```powershell
# 1. Clone 專案
git clone https://github.com/Eil1234/SCA-with-AI-assistance.git
cd SCA-with-AI-assistance

# 2. 雙擊 start_platform.bat
# 腳本會自動：
# - 安裝依賴
# - 啟動 FastAPI (port 8000)
# - 開啟瀏覽器
```

#### 方法 2：手動啟動

```powershell
cd api

# 安裝基礎依賴
python -m pip install -r requirements.txt

# 安裝 AI 依賴
python -m pip install -r requirements-ai.txt

# 啟動 API
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 方法 3：macOS/Linux

```bash
cd api
python -m pip install -r requirements.txt
python -m pip install -r requirements-ai.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 訪問應用

啟動後，在瀏覽器打開：

```
http://localhost:8000/platform
```

**常用網址**：
- 🎨 主操作介面：http://localhost:8000/platform
- 📡 API 文檔：http://localhost:8000/docs
- ❤️ 健康檢查：http://localhost:8000/health
- 🤖 AI 模型狀態：http://localhost:8000/ai/status

---

## 🔑 配置 Gemini AI 助手（可選但推薦）

### 1. 獲取 API Key

前往 [Google AI Studio](https://aistudio.google.com/app/apikeys) 免費創建 API Key。

### 2. 在程式中配置

編輯 `api/main.py`，找到：

```python
# 設置 GEMINI_API_KEY
os.environ["GEMINI_API_KEY"] = "自己的GEMINI_API_KEY"
```

替換為妳的真實 Key：

```python
os.environ["GEMINI_API_KEY"] = "你的_Gemini_API_Key"
```

### 3. 重啟 FastAPI

```powershell
# 按 Ctrl+C 停止
# 或重新執行啟動腳本
```

✅ 現在就可以使用 AI 助手功能了！

---

## 📊 使用指南

### 執行攻擊分析

1. **選擇攻擊方法** - 從 6 種傳統攻擊或 2 種 AI 模型中選擇
2. **上傳資料** - 拖拽上傳 Traces 和 Plaintexts/Keys
3. **配置參數** - 選擇 AES 版本、洩漏模型、目標 byte
4. **開始分析** - 點擊「開始分析」按鈕
5. **查看結果** - 動態圖表逐個顯示，實時更新
6. **下載報告** - 點擊「下載 PDF 報告」導出結果

### 使用對話助手和報告生成

### 與 AI 對話
1. 點擊右下角對話按鈕打開聊天面板
2. 提問關於平台使用、攻擊方法、結果解釋等任何問題
3. AI 實時生成有幫助的回答
4. 繼續對話以獲得更深入的理解

### 生成分析報告
1. 完成攻擊分析後，點擊「生成報告」
2. AI 自動分析測量結果和攻擊成功率
3. 生成專業的安全評估報告（包括風險評級和改進建議）
4. 點擊「下載 PDF」保存報告

### 生成安全報告

分析完成後，點擊「生成報告」：
- Gemini AI 自動分析結果
- 生成專業的安全評估報告
- 提出針對性改進建議
- 支援 PDF 下載

---

## 📋 支援的資料格式

| 格式 | 說明 |
|------|------|
| `.npy` | NumPy array |
| `.csv` | 逗號分隔值（每列一筆資料） |
| `.h5` / `.hdf5` | HDF5 datasets |
| `.trs` | Riscure Inspector traces |

### 資料要求

- **Traces**：shape `(N, trace_length)`，浮點數
- **Plaintexts**：shape `(N, 16)`，uint8
- **Keys**（SNR 分析用）：shape `(N, 16)` for AES-128 或 `(N, 32)` for AES-256

---

## 🤖 AI 模型配置

### 支援的 AI 模型組合

```
模型類型 × 洩漏模型 × 資料集

CNN 和 MLP，各有：
- ID（Identity） / HW（Hamming Weight）
- ASCAD Fixed / ASCAD Random / CHES CTF

共 12 種組合
```

### 設置步驟

1. **創建資料集目錄**：
   ```
   api/ai_assets/
   ├── data/
   │   ├── ascad_fixed/
   │   ├── ascad_random/
   │   └── ches_ctf/
   └── models/
       ├── fixed_cnn_bo_id_model.h5
       ├── fixed_cnn_bo_hw_model.h5
       └── ...（共 12 個 .h5 文件）
   ```

2. **放置資料集和模型**：
   - 將 `.h5` 檔案放在 `api/ai_assets/models/`
   - 將資料集放在 `api/ai_assets/data/`

3. **驗證模型**：
   ```
   http://localhost:8000/ai/status
   ```

---

## 🛠️ Template Attack 預建模板

Template Attack 需要用已知密鑰的 profiling 資料預先建立模板。

### 建立模板（管理員操作）

```powershell
cd api

# AES-128
python build_template.py --aes 128 \
  --traces PROFILE_TRACES.npy \
  --plaintexts PROFILE_TEXTIN.npy \
  --keys PROFILE_KEYS.npy

# AES-256
python build_template.py --aes 256 \
  --traces PROFILE_TRACES.npy \
  --plaintexts PROFILE_TEXTIN.npy \
  --keys PROFILE_KEYS.npy
```

### 模板說明

- 需要來自**同一晶片、相同環境**的 profiling 資料
- 生成的 `.npz` 文件應放在 `api/templates/`
- 生成後重啟 FastAPI 即可在前端選擇

詳見 [`api/templates/README.md`](api/templates/README.md)

---

## 📡 API 端點速查表

### 基礎端點

| 方法 | 端點 | 功能 |
|------|------|------|
| GET | `/health` | 健康檢查 |
| GET | `/algorithms` | 可用算法列表 |
| GET | `/ai/status` | AI 模型狀態 |

### 攻擊端點

| 方法 | 端點（AES-128） | 端點（AES-256） |
|------|-----------------|-----------------|
| POST | `/attack/cpa` | `/attack/cpa256` |
| POST | `/attack/dpa_dom` | `/attack/dpa_dom256` |
| POST | `/attack/dpa_pcc` | `/attack/dpa_pcc256` |
| POST | `/attack/mia` | `/attack/mia256` |
| POST | `/attack/template` | `/attack/template256` |
| POST | `/attack/snr` | `/attack/snr256` |

### AI 端點

| 方法 | 端點 | 功能 |
|------|------|------|
| POST | `/ai/evaluate` | 執行 CNN/MLP 評估 |
| POST | `/ai/chat` | AI 助手聊天 |

### 報告端點

| 方法 | 端點 | 功能 |
|------|------|------|
| POST | `/report/generate` | 生成 AI 分析報告 |
| POST | `/report/pdf` | 生成 PDF |

完整 API 文檔：http://localhost:8000/docs

---

## 🗂️ 專案結構

```
SCA-with-AI-assistance/
│
├── 📄 README.md              # 本文件
├── 📄 SETUP.md               # 詳細設置指南
├── 📄 QUICKSTART.md          # 30 秒快速開始
├── 📄 API_SPEC.md            # API 詳細規範
├── 📄 LICENSE                # MIT 許可證
├── 📄 .gitignore
│
├── 🌐 platform.html          # 主前端頁面（含 AI 助手）
├── 🔧 start_platform.bat     # Windows 自動啟動腳本
│
├── 📁 api/                   # FastAPI 後端
│   ├── main.py               # ⭐ FastAPI 主程式
│   ├── requirements.txt       # 基礎依賴
│   ├── requirements-ai.txt    # AI 依賴
│   ├── .env.example          # 環境變量示例
│   │
│   ├── 🎯 攻擊模組
│   ├── aes256_utils.py
│   ├── attack_base.py
│   │
│   ├── attacks/
│   │   ├── cpa.py            # CPA 攻擊
│   │   ├── dpa_dom.py
│   │   ├── dpa_pcc.py
│   │   ├── mia.py
│   │   ├── snr.py
│   │   ├── snr256.py
│   │   └── template.py
│   │
│   ├── 🤖 AI 模組
│   ├── ai_attack_service.py  # AI 評估服務
│   ├── report_service.py     # Gemini 報告生成
│   │
│   ├── 📊 工具
│   ├── build_template.py     # Template 建模工具
│   ├── template_store.py
│   ├── trace_loader.py
│   │
│   ├── ai_assets/
│   │   ├── README.md
│   │   ├── data/             # ⚠️ 不含在 Git 中
│   │   └── models/           # ⚠️ 不含在 Git 中
│   │
│   └── templates/
│       └── README.md         # Template 說明
│
└── static/
    └── ai-tutor.js           # AI 助手前端邏輯
```

---

## ⚡ 平台改進和優化

### 優化的用戶界面

相比傳統的一次性生成 16 張圖表，現在改為動態流式展示：

- 動態逐張加載圖表 - 更快看到初步結果
- 每個 byte 結果單獨展示 - 清晰對比各字節的攻擊成功率
- 流暢的使用體驗 - 實時進度反饋
- 互動式結果檢視 - 點擊高亮特定字節

### AI 驅動的分析和對話

集成 Gemini AI 提供兩層支持：

- **實時對話助手** - 使用者可隨時提問，獲得平台和攻擊相關的解釋
- **自動報告生成** - 分析完成後自動生成安全評估報告
- **靈活配置** - 可選配置 API Key；無 Key 時仍可使用所有攻擊功能

### 簡化的部署和安裝

原本需要多個複雜的手動步驟，現在只需：

```powershell
# 方式 1：自動啟動
.\start_platform.bat

# 方式 2：手動啟動
cd api
pip install -r requirements.txt
pip install -r requirements-ai.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## ❓ 常見問題

### 「API 離線」錯誤

```bash
# 檢查健康狀態
curl http://localhost:8000/health

# 確認 FastAPI 正在運行（查看終端窗口）
# 重新啟動：按 Ctrl+C 後重新運行啟動命令
```

### AI 模型未加載（status 顯示 ready: false）

```bash
# 檢查模型目錄
ls -la api/ai_assets/models/

# 確認所有 12 個 .h5 文件都存在
# 檢查文件名是否完全匹配（區分大小寫）
```

### Port 8000 被占用

```powershell
# 查詢占用 port 8000 的程序
netstat -ano | findstr :8000

# 終止程序（替換 PID）
taskkill /PID <PID> /F
```

### Gemini API Key 錯誤

- ✅ 確認在 `api/main.py` 中正確設定
- ✅ 檢查 key 是否有多餘空格
- ✅ 確認 API key 未過期
- ✅ 重啟 FastAPI

更多問題詳見 [`SETUP.md`](SETUP.md)

---

## 📖 進階文檔

- **[SETUP.md](SETUP.md)** - Windows/macOS/Linux 完整設置指南
- **[QUICKSTART.md](QUICKSTART.md)** - 30 秒快速上手
- **[API_SPEC.md](API_SPEC.md)** - 完整 API 規範

---

## 📜 許可證

本專案採用 [MIT 許可證](LICENSE)。

---

**版本**：1.0.0  
**最後更新**：2026 年 9 月  
**Status**：主動維護中 ✅
