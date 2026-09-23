# 🔧 詳細設置指南

完整的開發環境和部署設置步驟。

---

## 📋 系統要求

- **Python**: 3.9 或更高版本
- **操作系統**: Windows 10/11、macOS、或 Linux
- **記憶體**: 4GB 以上（AI 模型推理建議 8GB）
- **GPU**（可選）: CUDA 11.0+（加速推理）

### 驗證安裝

```powershell
python --version  # 應顯示 3.9+
pip --version
```

---

## 🪟 Windows 完整設置

### 1️⃣ Clone 或下載項目

```powershell
git clone https://github.com/Eil1234/SCA-with-AI-assistance.git
cd SCA-with-AI-assistance
```

### 2️⃣ 創建虛擬環境（推薦）

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ 升級 pip

```powershell
python -m pip install --upgrade pip
```

### 4️⃣ 安裝基礎依賴

```powershell
cd api
python -m pip install -r requirements.txt
```

### 5️⃣ 安裝 AI 依賴

#### 選項 A：Intel 優化版（推薦用於 Windows）

```powershell
python -m pip install -r requirements-ai.txt
python -m pip install tensorflow-intel
```

#### 選項 B：標準版

```powershell
python -m pip install -r requirements-ai.txt
python -m pip install tensorflow
```

#### 選項 C：GPU 支援（需要 CUDA）

```powershell
python -m pip install -r requirements-ai.txt
python -m pip install tensorflow[and-cuda]
```

### 6️⃣ 配置 Gemini API Key

編輯 `api/main.py`：

```python
# 找到這一行
os.environ["GEMINI_API_KEY"] = "自己的GEMINI_API_KEY"

# 替換為你的 key
os.environ["GEMINI_API_KEY"] = "你的_Gemini_API_Key"
```

### 7️⃣ 啟動 FastAPI

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

看到以下信息表示成功：

```
Uvicorn running on http://0.0.0.0:8000
```

---

## 🍎 macOS 設置

### 1️⃣ Clone 項目

```bash
git clone https://github.com/Eil1234/SCA-with-AI-assistance.git
cd SCA-with-AI-assistance
```

### 2️⃣ 使用 Homebrew 安裝 Python（如需要）

```bash
brew install python@3.10
```

### 3️⃣ 創建虛擬環境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4️⃣ 升級 pip 並安裝依賴

```bash
python -m pip install --upgrade pip

cd api
python -m pip install -r requirements.txt
python -m pip install -r requirements-ai.txt
```

### 5️⃣ 配置 API Key 並啟動

```bash
# 編輯 main.py（使用 nano、vim 或文本編輯器）
nano main.py

# 找到並替換 GEMINI_API_KEY 行

# 啟動
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🐧 Linux 設置（Ubuntu/Debian）

### 1️⃣ 更新系統

```bash
sudo apt-get update
sudo apt-get upgrade
```

### 2️⃣ 安裝 Python

```bash
sudo apt-get install python3.10 python3.10-venv python3-pip
```

### 3️⃣ Clone 項目

```bash
git clone https://github.com/Eil1234/SCA-with-AI-assistance.git
cd SCA-with-AI-assistance
```

### 4️⃣ 創建虛擬環境

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 5️⃣ 安裝依賴

```bash
cd api
pip install -r requirements.txt
pip install -r requirements-ai.txt
```

### 6️⃣ 配置和啟動

```bash
# 編輯 main.py
nano main.py
# 替換 GEMINI_API_KEY

# 啟動
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📁 AI 資源配置

### 創建必要目錄

```powershell
# Windows
mkdir api\ai_assets\data
mkdir api\ai_assets\models

# macOS / Linux
mkdir -p api/ai_assets/data
mkdir -p api/ai_assets/models
```

### 資料集和模型結構

```
api/ai_assets/
├── data/
│   ├── ascad_fixed/          # ASCAD Fixed 資料集
│   ├── ascad_random/         # ASCAD Random 資料集
│   └── ches_ctf/             # CHES CTF 資料集
│
└── models/
    ├── fixed_cnn_bo_id_model.h5      # CNN ID model for ASCAD Fixed
    ├── fixed_cnn_bo_hw_model.h5      # CNN HW model for ASCAD Fixed
    ├── fixed_mlp_bo_id_model.h5      # MLP ID model for ASCAD Fixed
    ├── fixed_mlp_bo_hw_model.h5      # MLP HW model for ASCAD Fixed
    ├── rand_cnn_bo_id_model.h5
    ├── rand_cnn_bo_hw_model.h5
    ├── rand_mlp_bo_id_model.h5
    ├── rand_mlp_bo_hw_model.h5
    ├── ches_cnn_bo_id_model.h5
    ├── ches_cnn_bo_hw_model.h5
    ├── ches_mlp_bo_id_model.h5
    └── ches_mlp_bo_hw_model.h5
```

### 驗證模型

```bash
# 啟動後訪問
curl http://localhost:8000/ai/status

# 或在瀏覽器打開
http://localhost:8000/ai/status
```

預期輸出：

```json
{
  "models": [
    {
      "model": "fixed_cnn_bo_id_model",
      "ready": true,
      "path": "api/ai_assets/models/fixed_cnn_bo_id_model.h5"
    },
    ...
  ]
}
```

---

## 🔑 Gemini API Key 設置（可選但推薦）

若要使用 AI 對話助手和自動報告生成功能，需配置 Gemini API Key。

### 1️⃣ 獲取免費 API Key

1. 打開 [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. 點擊「Get API Key」或「Create API Key」
3. 複製生成的 key

### 2️⃣ 配置方式

#### 方式 A：直接在 `main.py` 中設定（簡單）

編輯 `api/main.py`：

```python
import os

# 找到以下行
os.environ["GEMINI_API_KEY"] = "自己的GEMINI_API_KEY"

# 替換為
os.environ["GEMINI_API_KEY"] = "sk-1234567890abcdef..."
```

#### 方式 B：使用 `.env` 文件（推薦，更安全）

1. 複製 `api/.env.example` 為 `api/.env`：

```powershell
Copy-Item api\.env.example api\.env
```

2. 編輯 `api/.env`：

```dotenv
GEMINI_API_KEY=你的_Gemini_API_Key
GEMINI_MODEL=gemini-3-flash-preview
```

3. 在 `main.py` 中使用 python-dotenv 讀取：

```python
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
```

### 3️⃣ 驗證配置

```bash
# 啟動後訪問
curl http://localhost:8000/health

# 測試 AI 端點
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### ⚠️ 安全提示

❌ **不要**：
- 把真實 API key 提交到 Git
- 在公開代碼中暴露 key
- 分享 key 給他人

✅ **應該**：
- 使用 `.env` 文件管理敏感信息
- 確保 `.env` 在 `.gitignore` 中
- 定期更換 key（如泄露）

---

## 🧪 驗證安裝

### 檢查 Python 模塊

```bash
# FastAPI
python -c "from fastapi import FastAPI; print('FastAPI OK')"

# TensorFlow
python -c "import tensorflow as tf; print(f'TensorFlow {tf.__version__} OK')"

# Gemini AI
python -c "import google.generativeai; print('Gemini OK')"
```

### 測試 API

```bash
# 健康檢查
curl http://localhost:8000/health

# 算法列表
curl http://localhost:8000/algorithms

# AI 模型狀態
curl http://localhost:8000/ai/status
```

---

## 🐛 常見問題排查

### Python 版本錯誤

**錯誤**：`No module named 'venv'`

**解決**：確保使用 Python 3.9+

```bash
python --version

# 如果版本太舊，下載新版本或使用特定版本
python3.10 -m venv venv
```

### TensorFlow 導入失敗

**錯誤**：`ImportError: DLL load failed`（Windows）或版本衝突

**解決**：

```bash
# 卸載舊版本
pip uninstall tensorflow -y

# 重新安裝（Windows 推薦 intel 版）
pip install tensorflow-intel

# 或標準版本
pip install tensorflow
```

### Port 8000 被占用

**錯誤**：`Address already in use: ('0.0.0.0', 8000)`

**解決**：

```powershell
# Windows 查詢
netstat -ano | findstr :8000

# 終止程序（替換 PID）
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>

# 或使用不同 port
python -m uvicorn main:app --port 8001
```

### 虛擬環境激活失敗

**錯誤**：`venv\Scripts\activate 無法執行`

**解決**：

```powershell
# 確保虛擬環境存在
python -m venv venv

# 使用完整路徑
& .\venv\Scripts\Activate.ps1
```

### Gemini API Key 不工作

**錯誤**：報告功能失敗或返回 401

**解決**：

1. 確認在 `main.py` 中正確設定
2. 檢查 key 是否有額外空格
3. 驗證 key 有效期未過期
4. 重啟 FastAPI

```bash
# 測試 key
curl -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent \
  -H "Content-Type: application/json" \
  -d "{\"contents\": [{\"parts\": [{\"text\": \"Hi\"}]}]}" \
  -H "x-goog-api-key: YOUR_API_KEY"
```

### AI 模型未載入

**現象**：`http://localhost:8000/ai/status` 返回 `"ready": false`

**解決**：

1. 檢查目錄存在：
   ```bash
   ls -la api/ai_assets/models/
   ls -la api/ai_assets/data/
   ```

2. 確認所有 12 個 `.h5` 文件都存在

3. 驗證文件名完全匹配（區分大小寫）

4. 檢查文件沒有損壞：
   ```bash
   python -c "import h5py; h5py.File('api/ai_assets/models/fixed_cnn_bo_id_model.h5', 'r')"
   ```

---

## 📦 依賴管理

### 查看已安裝的包

```bash
pip list
```

### 更新所有依賴

```bash
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-ai.txt
```

### 生成當前環境的 requirements

```bash
pip freeze > requirements_current.txt
```

### 卸載所有依賴

```bash
pip freeze | xargs pip uninstall -y
```

---

## 🐳 Docker 部署（可選）

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY api/requirements.txt .
COPY api/requirements-ai.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-ai.txt
RUN pip install tensorflow-intel

COPY api/ ./
COPY platform.html ./
COPY static/ ./static/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 構建和運行

```bash
# 構建
docker build -t sca-with-ai-assistance .

# 運行
docker run -p 8000:8000 sca-with-ai-assistance
```

---

## ✅ 完成檢查清單

部署前確認：

- [ ] Python 3.9+ 已安裝
- [ ] 虛擬環境已創建和激活
- [ ] `requirements.txt` 已安裝
- [ ] `requirements-ai.txt` 已安裝
- [ ] TensorFlow 可成功導入
- [ ] FastAPI 可成功導入
- [ ] Gemini API Key 已配置（可選）
- [ ] AI 資源目錄已創建
- [ ] 應用可在 `http://localhost:8000` 運行
- [ ] 前端可加載
- [ ] API 端點可訪問

---

**需要幫助？** 在 [GitHub Issues](https://github.com/Eil1234/SCA-with-AI-assistance/issues) 提問！
