# ⚡ 快速開始指南（30 秒）

想立即開始使用？這裡是最快的方式。

---

## 🪟 Windows 用戶（最簡單 ⭐）

### 方法 1：自動啟動（推薦）

```powershell
# 1️⃣ 打開命令行，進入項目目錄
cd C:\Users\YourName\SCA-with-AI-assistance

# 2️⃣ 雙擊 start_platform.bat
# 或在命令行執行
.\start_platform.bat

# ✅ 等待 30 秒，瀏覽器自動打開 http://localhost:8000/platform
```

**就這樣！** 🎉

### 方法 2：手動啟動

```powershell
cd api

# 安裝依賴（首次需要，之後不必重複）
python -m pip install -r requirements.txt
python -m pip install -r requirements-ai.txt

# 啟動 API
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 在瀏覽器打開
# http://localhost:8000/platform
```

---

## 🍎 macOS / 🐧 Linux 用戶

```bash
# 進入項目目錄
cd ~/SCA-with-AI-assistance/api

# 安裝依賴
python -m pip install -r requirements.txt
python -m pip install -r requirements-ai.txt

# 啟動
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 打開瀏覽器
# http://localhost:8000/platform
```

---

## 📍 常用網址

| 網址 | 功能 |
|------|------|
| http://localhost:8000/platform | 📱 主操作界面 |
| http://localhost:8000/docs | 📡 API 文檔 |
| http://localhost:8000/health | ❤️ 健康檢查 |
| http://localhost:8000/ai/status | 🤖 AI 模型狀態 |

---

## 🎯 基本使用流程

### 1️⃣ 選擇攻擊方法

在頁面左側選擇：
- **傳統攻擊**：CPA、DPA、MIA、Template、SNR
- **AI 模型**：CNN、MLP

### 2️⃣ 上傳資料

拖拽或點擊上傳：
- **Traces**：`.npy`、`.csv`、`.h5` 或 `.trs` 格式
- **Plaintexts**：同上格式
- **Keys**（SNR 用）：同上格式

### 3️⃣ 配置參數

- **AES 版本**：128 或 256
- **目標 Byte**：0-15（或 0-31 for AES-256）
- **洩漏模型**：ID 或 HW（AI 模型用）

### 4️⃣ 開始分析

點擊「開始分析」，等待進度條完成。

### 5️⃣ 查看結果

- 📊 **動態圖表**：每個 byte 結果一張圖
- 💾 **下載報告**：點擊「下載 PDF」

### 6️⃣ 使用 AI 對話和報告

- 💬 點擊右下角按鈕開啟對話，提問任何關於平台或結果的問題
- 📋 完成分析後點擊「生成報告」，AI 自動分析並生成安全評估
- 💾 下載 PDF 保存完整報告

---

## 🔑 配置 AI 助手（可選）

要使用 Gemini AI 功能，需要一個免費的 API Key。

### 1️⃣ 獲取 Key

前往 [Google AI Studio](https://aistudio.google.com/app/apikeys)，點擊 **「Get API Key」**，複製生成的 key。

### 2️⃣ 在程式中設定

編輯 `api/main.py`，找到這一行：

```python
os.environ["GEMINI_API_KEY"] = "自己的GEMINI_API_KEY"
```

替換為：

```python
os.environ["GEMINI_API_KEY"] = "你複製的key"
```

### 3️⃣ 重啟 API

```powershell
# 按 Ctrl+C 停止
# 然後重新運行啟動命令
```

✅ 完成！現在可以使用 AI 助手。

---

## 📊 上傳資料格式

### 必要資料

| 資料 | 格式 | 範例 |
|------|------|------|
| Traces | `.npy`, `.csv`, `.h5`, `.trs` | (1000, 5000) shape 的陣列 |
| Plaintexts | 同上 | (1000, 16) shape 的 uint8 |
| Keys | 同上 | (1000, 16) for AES-128 |

### Python 準備資料

```python
import numpy as np

# 讀取或生成資料
traces = np.random.randn(1000, 5000)        # 1000 筆 traces
plaintexts = np.random.randint(0, 256, (1000, 16), dtype=np.uint8)
keys = np.random.randint(0, 256, (1000, 16), dtype=np.uint8)

# 保存為 .npy
np.save("traces.npy", traces)
np.save("plaintexts.npy", plaintexts)
np.save("keys.npy", keys)

# 或保存為 CSV
np.savetxt("traces.csv", traces, delimiter=",")
```

---

## ❓ 我遇到了問題

### 「API 離線」

```bash
# 1. 檢查 FastAPI 是否正在運行
# 查看終端窗口，應看到：
# Uvicorn running on http://0.0.0.0:8000

# 2. 手動檢查
curl http://localhost:8000/health
# 應返回：{"status":"ok"}

# 3. 重啟 API
# 按 Ctrl+C，再重新運行啟動命令
```

### Port 8000 被占用

```powershell
# 查詢占用 port 8000 的程序
netstat -ano | findstr :8000

# 終止程序（替換 PID）
taskkill /PID <PID> /F
```

### AI 模型未就緒

```bash
# 檢查模型狀態
curl http://localhost:8000/ai/status

# 若模型不存在，確認：
# 1. 目錄 api/ai_assets/models/ 是否存在
# 2. 所有 12 個 .h5 文件都存在
# 3. 文件名是否完全匹配
```

### 更多問題

詳見 [SETUP.md](SETUP.md#常見問題排查) 的完整排查指南。

---

## 📖 下一步

- 📖 **詳細使用**：閱讀 [README.md](README.md)
- 🔧 **詳細設置**：閱讀 [SETUP.md](SETUP.md)
- 📡 **API 文檔**：訪問 http://localhost:8000/docs
- 🤝 **貢獻代碼**：閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)

---

**祝你使用愉快！** 🚀

有問題？在 [GitHub Issues](https://github.com/Eil1234/SCA-with-AI-assistance/issues) 中提問。
