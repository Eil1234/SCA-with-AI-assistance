"""
main.py
AES-128 Side-Channel Attack API
啟動方式：uvicorn main:app --reload --host 0.0.0.0 --port 8000
API 文件：http://localhost:8000/docs

架構說明：
  - 所有攻擊演算法放在 attacks/ 資料夾
  - 新增演算法只需在 attacks/ 新增 .py 並繼承 BaseAttack，API 自動支援
  - 前端只需呼叫 POST /attack/{algorithm_id}，不需要因為加新演算法而改程式碼
"""

import importlib
import pkgutil
import os
import google.generativeai as genai
import sys
import io
import asyncio
import multiprocessing as mp
import queue as queue_module
import threading
import time
import uuid

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, Body, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 確保 attacks/ 資料夾可以被 import
sys.path.insert(0, os.path.dirname(__file__))

from attack_base import registry, AttackInput
from trace_loader import load_traces, load_plaintexts
from report_service import generate_security_report, render_report_pdf, report_config
from template_store import template_status
from ai_attack_service import ai_service_status, run_ai_evaluation, validate_ai_request

# ── 自動載入 attacks/ 資料夾下所有演算法模組 ──────────────────────────
import attacks
for _, module_name, _ in pkgutil.iter_modules(attacks.__path__):
    importlib.import_module(f"attacks.{module_name}")
# ─────────────────────────────────────────────────────────────────────

# 設置 GEMINI_API_KEY
os.environ["GEMINI_API_KEY"] = "自己的GEMINI_API_KEY"


app = FastAPI(
    title="SCA Attack API",
    description="""
## AES-128 / AES-256 旁通道攻擊 API

**使用流程：**
1. `GET /algorithms` — 查詢目前支援的攻擊演算法清單
2. `POST /attack/{algorithm_id}` — 上傳 traces 與 plaintexts，執行攻擊

**支援上傳格式：** `.npy` / `.csv` / `.h5` / `.hdf5` / `.trs`

**AES-128 AI 攻擊：**
- 內建伺服器端 CNN / MLP 模型評估，支援 ASCAD Fixed、ASCAD Random、CHES CTF。
- AI 模型只評估資料集指定的單一 key byte，不宣稱還原完整 16-byte 金鑰。
- `GET /ai/status` 可檢查 TensorFlow、資料集與模型是否已就緒。

**新增演算法：**
- 在 `attacks/` 資料夾新增 .py 檔，繼承 `BaseAttack`，API 自動支援
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 正式環境請填前端網址
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 共用工具 ──────────────────────────────────────────────────────────

async def read_upload(file: UploadFile, field_name: str, is_plaintext: bool = False) -> np.ndarray:
    """讀取上傳檔案，自動依副檔名解析格式（npy/csv/h5/trs）"""
    try:
        content = await file.read()
        if is_plaintext:
            return load_plaintexts(content, file.filename or "file.npy")
        else:
            return load_traces(content, file.filename or "file.npy")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{field_name} 解析失敗：{e}")


# ── Endpoints ─────────────────────────────────────────────────────────

# ── 可取消的攻擊工作 ───────────────────────────────────────────────────
_attack_jobs: dict[str, dict] = {}
_cancelled_job_ids: dict[str, float] = {}
_attack_jobs_lock = threading.Lock()


class AttackCancelledError(Exception):
    """使用者主動取消攻擊。"""


def _attack_process_worker(algorithm_id: str, data: AttackInput, output_queue):
    """在獨立程序執行 CPU 密集攻擊，讓主程序可以真正終止工作。"""
    try:
        attack = registry.get(algorithm_id)
        if attack is None:
            output_queue.put({"status": "error", "message": f"找不到演算法 '{algorithm_id}'"})
            return
        result = attack.run(data)
        output_queue.put({"status": "ok", "result": {
            "algorithm": result.algorithm,
            "key_hex": result.key_hex,
            "key_bytes": result.key_bytes,
            "num_traces": result.num_traces,
            "trace_length": result.trace_length,
            "plot_base64": result.plot_base64,
            "extra": result.extra,
        }})
    except ValueError as exc:
        output_queue.put({"status": "value_error", "message": str(exc)})
    except Exception as exc:
        output_queue.put({"status": "error", "message": str(exc)})


async def _run_attack_process(job_id: str, algorithm_id: str, data: AttackInput) -> dict:
    """啟動攻擊子程序並非阻塞等待；取消端點可 terminate 該程序。"""
    context = mp.get_context("spawn")
    output_queue = context.Queue(maxsize=1)
    process = context.Process(
        target=_attack_process_worker,
        args=(algorithm_id, data, output_queue),
        name=f"sca-{algorithm_id}-{job_id[:8]}",
        daemon=True,
    )

    with _attack_jobs_lock:
        cutoff = time.monotonic() - 600
        for cancelled_id, created_at in list(_cancelled_job_ids.items()):
            if created_at < cutoff:
                _cancelled_job_ids.pop(cancelled_id, None)
        if job_id in _cancelled_job_ids:
            _cancelled_job_ids.pop(job_id, None)
            output_queue.close()
            raise AttackCancelledError()
        if job_id in _attack_jobs:
            output_queue.close()
            raise HTTPException(status_code=409, detail="相同 job_id 的攻擊正在執行")
        _attack_jobs[job_id] = {"process": process, "cancelled": False}
        try:
            process.start()
        except Exception:
            _attack_jobs.pop(job_id, None)
            output_queue.close()
            raise

    try:
        message = None
        while process.is_alive() and message is None:
            await asyncio.sleep(0.2)
            try:
                message = output_queue.get_nowait()
            except queue_module.Empty:
                pass
            with _attack_jobs_lock:
                job = _attack_jobs.get(job_id)
                if job and job["cancelled"]:
                    raise AttackCancelledError()

        await asyncio.to_thread(process.join, 0.5)
        with _attack_jobs_lock:
            job = _attack_jobs.get(job_id)
            if job and job["cancelled"]:
                raise AttackCancelledError()

        if message is None:
            try:
                message = await asyncio.to_thread(output_queue.get, True, 2.0)
            except queue_module.Empty as exc:
                raise RuntimeError(f"攻擊子程序未回傳結果（exit code: {process.exitcode}）") from exc

        if message.get("status") == "ok":
            return message["result"]
        if message.get("status") == "value_error":
            raise ValueError(message.get("message") or "攻擊輸入不正確")
        raise RuntimeError(message.get("message") or "攻擊子程序執行失敗")
    finally:
        if process.is_alive():
            process.terminate()
            await asyncio.to_thread(process.join, 2.0)
            if process.is_alive() and hasattr(process, "kill"):
                process.kill()
                await asyncio.to_thread(process.join, 1.0)
        with _attack_jobs_lock:
            _attack_jobs.pop(job_id, None)
        output_queue.close()
        output_queue.join_thread()

def _ai_process_worker(model_type: str, leakage_model: str, dataset_type: str, output_queue):
    """在獨立程序載入 TensorFlow 並執行 AES-128 AI 評估。"""
    try:
        result = run_ai_evaluation(model_type, leakage_model, dataset_type)
        output_queue.put({"status": "ok", "result": result})
    except ValueError as exc:
        output_queue.put({"status": "value_error", "message": str(exc)})
    except Exception as exc:
        output_queue.put({"status": "error", "message": str(exc)})


async def _run_ai_process(job_id: str, model_type: str, leakage_model: str, dataset_type: str) -> dict:
    """以可取消子程序執行 AI 評估，避免 TensorFlow 阻塞 FastAPI。"""
    context = mp.get_context("spawn")
    output_queue = context.Queue(maxsize=1)
    process = context.Process(
        target=_ai_process_worker,
        args=(model_type, leakage_model, dataset_type, output_queue),
        name=f"sca-ai-{model_type}-{job_id[:8]}",
        daemon=True,
    )

    with _attack_jobs_lock:
        cutoff = time.monotonic() - 600
        for cancelled_id, created_at in list(_cancelled_job_ids.items()):
            if created_at < cutoff:
                _cancelled_job_ids.pop(cancelled_id, None)
        if job_id in _cancelled_job_ids:
            _cancelled_job_ids.pop(job_id, None)
            output_queue.close()
            raise AttackCancelledError()
        if job_id in _attack_jobs:
            output_queue.close()
            raise HTTPException(status_code=409, detail="相同 job_id 的分析正在執行")
        _attack_jobs[job_id] = {"process": process, "cancelled": False, "kind": "ai"}
        try:
            process.start()
        except Exception:
            _attack_jobs.pop(job_id, None)
            output_queue.close()
            raise

    try:
        message = None
        while process.is_alive() and message is None:
            await asyncio.sleep(0.2)
            try:
                message = output_queue.get_nowait()
            except queue_module.Empty:
                pass
            with _attack_jobs_lock:
                job = _attack_jobs.get(job_id)
                if job and job["cancelled"]:
                    raise AttackCancelledError()

        await asyncio.to_thread(process.join, 0.5)
        with _attack_jobs_lock:
            job = _attack_jobs.get(job_id)
            if job and job["cancelled"]:
                raise AttackCancelledError()
        if message is None:
            try:
                message = await asyncio.to_thread(output_queue.get, True, 2.0)
            except queue_module.Empty as exc:
                raise RuntimeError(f"AI 子程序未回傳結果（exit code: {process.exitcode}）") from exc
        if message.get("status") == "ok":
            return message["result"]
        if message.get("status") == "value_error":
            raise ValueError(message.get("message") or "AI 評估輸入不正確")
        raise RuntimeError(message.get("message") or "AI 評估子程序執行失敗")
    finally:
        if process.is_alive():
            process.terminate()
            await asyncio.to_thread(process.join, 2.0)
            if process.is_alive() and hasattr(process, "kill"):
                process.kill()
                await asyncio.to_thread(process.join, 1.0)
        with _attack_jobs_lock:
            _attack_jobs.pop(job_id, None)
        output_queue.close()
        output_queue.join_thread()


class AIEvaluationRequest(BaseModel):
    model_type: str
    leakage_model: str
    dataset_type: str
    job_id: str | None = None

@app.get("/", summary="狀態確認")
def root():
    return {
        "status": "ok",
        "message": "AES-128 / AES-256 SCA Attack API 運行中",
        "platform": "/platform",
    }


@app.get("/platform", include_in_schema=False)
@app.get("/platform.html", include_in_schema=False)
def platform_page():
    """由同一支 FastAPI 提供操作網頁，避免另外開啟本機 HTML。"""
    platform_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "platform.html")
    return FileResponse(platform_path, media_type="text/html; charset=utf-8")


@app.get(
    "/algorithms",
    summary="取得支援的攻擊演算法清單",
    description="前端用來動態產生演算法選單，不需要寫死演算法名稱。",
)
def list_algorithms():
    return {"algorithms": registry.list_all()}


@app.get("/template/status", summary="伺服器預建 Template Attack 狀態")
def get_template_status():
    """回傳 AES-128/AES-256 統計模板是否已由管理者建立。"""
    return {"templates": {"128": template_status(128), "256": template_status(256)}}

@app.get("/ai/status", summary="AES-128 CNN / MLP 服務狀態")
def get_ai_status():
    """檢查 TensorFlow、伺服器資料集與預訓練模型組合。"""
    return ai_service_status()


@app.post("/ai/evaluate", summary="執行 AES-128 CNN / MLP 側信道評估")
async def evaluate_ai(request: AIEvaluationRequest):
    """使用伺服器端資料集與模型評估單一 AES-128 key byte。"""
    try:
        model_type, leakage_model, dataset_type = validate_ai_request(
            request.model_type, request.leakage_model, request.dataset_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    active_job_id = (request.job_id or uuid.uuid4().hex).strip()
    if not active_job_id or len(active_job_id) > 100 or not all(ch.isalnum() or ch in "-_" for ch in active_job_id):
        raise HTTPException(status_code=400, detail="job_id 只能包含英數字、-、_，且不可超過 100 字元")
    try:
        return await _run_ai_process(active_job_id, model_type, leakage_model, dataset_type)
    except AttackCancelledError:
        raise HTTPException(status_code=409, detail="AI 攻擊已由使用者取消")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 攻擊執行失敗：{exc}") from exc

@app.post(
    "/attack/{algorithm_id}",
    summary="執行攻擊",
    description="""
執行指定演算法的旁通道攻擊。

**必填欄位：**
- `traces_file`：功耗波形 `.npy`，shape `(N, trace_length)`，dtype `float32/float64`
- `plaintexts_file`：明文 `.npy`，shape `(N, 16)`，dtype `uint8`

**選填欄位：**
- `preprocessed_traces_file`：如果之後有另外做前處理過的 traces，格式同 traces_file
  - 若提供，攻擊將使用此 traces 而非原始 traces
  - 不提供則直接用原始 traces（目前用不到這個欄位）

**回傳：**
```json
{
  "algorithm":    "cpa",
  "key_hex":      "2b7e151628aed2a6abf7158809cf4f3c",
  "key_bytes":    [43, 126, 21, 22, 40, 174, 210, 166, 171, 247, 21, 136, 9, 207, 79, 60],
  "num_traces":   2000,
  "trace_length": 24400,
  "plot_base64":  "<base64 PNG>"
}
```

前端顯示圖表：`<img src="data:image/png;base64,{plot_base64}" />`
""",
)
async def run_attack(
    algorithm_id: str,
    traces_file: UploadFile = File(..., description="功耗波形 .npy"),
    plaintexts_file: UploadFile = File(..., description="明文 .npy，shape (N, 16)"),
    preprocessed_traces_file: UploadFile = File(None, description="[選填，目前用不到] 前處理過的 traces .npy"),
    template_traces_file: UploadFile = File(None, description="[管理者／相容模式選填] 臨時 profiling traces .npy"),
    template_plaintexts_file: UploadFile = File(None, description="[管理者／相容模式選填] 臨時 profiling plaintexts .npy"),
    template_keys_file: UploadFile = File(None, description="[管理者／相容模式選填] 臨時 profiling keys .npy（AES-128: 16 bytes；AES-256: 32 bytes）"),
    known_key_hex: str = Form(None, description="[選填] 已知金鑰：AES-128 為 32 hex，AES-256 為 64 hex；SNR256 必填"),
    job_id: str = Form(None, description="[選填] 前端產生的工作 ID，供取消攻擊使用"),
):
    # 查詢演算法
    attack = registry.get(algorithm_id)
    if attack is None:
        available = [a["id"] for a in registry.list_all()]
        raise HTTPException(
            status_code=404,
            detail=f"找不到演算法 '{algorithm_id}'，目前支援：{available}"
        )

    # 讀取必填檔案（支援 npy / csv / h5 / trs）
    traces     = await read_upload(traces_file, "traces_file")
    plaintexts = await read_upload(plaintexts_file, "plaintexts_file", is_plaintext=True)

    # 選填：AI 前處理
    preprocessed = None
    if preprocessed_traces_file is not None:
        preprocessed = await read_upload(preprocessed_traces_file, "preprocessed_traces_file")

    # 管理者／相容模式選填：臨時 profiling 資料；一般使用者走伺服器預建模板
    tmpl_traces     = None
    tmpl_plaintexts = None
    tmpl_keys       = None
    if template_traces_file is not None:
        tmpl_traces     = await read_upload(template_traces_file, "template_traces_file")
    if template_plaintexts_file is not None:
        tmpl_plaintexts = await read_upload(template_plaintexts_file, "template_plaintexts_file", is_plaintext=True)
    if template_keys_file is not None:
        tmpl_keys       = await read_upload(template_keys_file, "template_keys_file", is_plaintext=True)

    known_key = None
    if known_key_hex:
        normalized_key = "".join(known_key_hex.split())
        if len(normalized_key) not in (32, 64):
            raise HTTPException(status_code=400, detail="known_key_hex 必須是 32 或 64 個十六進位字元")
        try:
            known_key = np.frombuffer(bytes.fromhex(normalized_key), dtype=np.uint8).copy()
        except ValueError:
            raise HTTPException(status_code=400, detail="known_key_hex 只能包含 0-9、a-f")

    # 組裝輸入並執行攻擊
    data = AttackInput(
        traces=traces,
        plaintexts=plaintexts,
        preprocessed_traces=preprocessed,
        template_traces=tmpl_traces,
        template_plaintexts=tmpl_plaintexts,
        template_keys=tmpl_keys,
        known_key=known_key,
    )

    active_job_id = (job_id or uuid.uuid4().hex).strip()
    if not active_job_id or len(active_job_id) > 100 or not all(ch.isalnum() or ch in "-_" for ch in active_job_id):
        raise HTTPException(status_code=400, detail="job_id 只能包含英數字、-、_，且不可超過 100 字元")

    try:
        result_payload = await _run_attack_process(active_job_id, algorithm_id, data)
    except AttackCancelledError:
        raise HTTPException(status_code=409, detail="攻擊已由使用者取消")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"攻擊執行失敗：{e}")

    return JSONResponse(result_payload)


@app.post("/attack/cancel/{job_id}", summary="取消正在執行的傳統或 AI 攻擊")
async def cancel_attack(job_id: str):
    """終止指定傳統或 AI 攻擊子程序，釋放 CPU/GPU 與記憶體。"""
    with _attack_jobs_lock:
        job = _attack_jobs.get(job_id)
        if job is None:
            cutoff = time.monotonic() - 600
            for cancelled_id, created_at in list(_cancelled_job_ids.items()):
                if created_at < cutoff:
                    _cancelled_job_ids.pop(cancelled_id, None)
            _cancelled_job_ids[job_id] = time.monotonic()
            return {"cancelled": True, "terminated": False, "status": "cancellation_registered", "job_id": job_id}
        job["cancelled"] = True
        process = job.get("process")

    terminated = False
    if process is not None and process.is_alive():
        process.terminate()
        await asyncio.to_thread(process.join, 2.0)
        if process.is_alive() and hasattr(process, "kill"):
            process.kill()
            await asyncio.to_thread(process.join, 1.0)
        terminated = not process.is_alive()

    return {"cancelled": True, "terminated": terminated, "status": "cancelled", "job_id": job_id}

@app.get("/report/config", summary="AI 報告服務狀態")
def get_report_config():
    """只回傳是否已設定金鑰，不會回傳或記錄 API key。"""
    return report_config()


@app.post("/report/generate", summary="產生 AI 輔助晶片旁通道安全分析報告")
def generate_report(payload: dict = Body(...)):
    """
    依分析結果產生可稽核的結構化報告。

    - 有 `GEMINI_API_KEY`：使用 Google Gemini API 產生敘述。
    - 無金鑰或 AI 暫時失敗：安全退回固定模板。
    - 量測事實、風險狀態及標準條文對照不交由 AI 改寫。
    """
    try:
        return JSONResponse(generate_security_report(payload))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"報告資料格式錯誤：{exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"報告產生失敗：{exc}") from exc


@app.post("/report/pdf", summary="下載晶片旁通道安全分析 PDF")
def download_report_pdf(payload: dict = Body(...)):
    report = payload.get("report")
    if not isinstance(report, dict):
        raise HTTPException(status_code=400, detail="payload.report 必須是已產生的報告物件")
    try:
        pdf_bytes = render_report_pdf(report, payload.get("plot_base64"))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF 產生失敗：{exc}") from exc

    document_id = str(report.get("document_id") or "SCA-Security-Report")
    safe_id = "".join(ch for ch in document_id if ch.isalnum() or ch in "-_") or "SCA-Security-Report"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_id}.pdf"'},
    )

@app.get("/health", summary="Health check")
def health():
    ai_status = ai_service_status()
    return {"status": "ok", "ai_attacks": {"aes_bits": 128, "ready_any": ai_status["ready_any"]}}

@app.get("/ai/status", summary="查詢 AI 服務狀態")
def get_ai_status():
    """查詢 AI 模型服務的狀態"""
    ai_status = ai_service_status()
    
    if isinstance(ai_status, dict) and "combinations" in ai_status:
        return ai_status
    
    return {
        "ready_any": ai_status.get("ready_any", False) if isinstance(ai_status, dict) else False,
        "combinations": ai_status.get("combinations", []) if isinstance(ai_status, dict) else [],
        "error": ai_status.get("error") if isinstance(ai_status, dict) else "AI 服務狀態讀取失敗"
    }

# ======================== 新增區域：Gemini 教導小助手 ========================
# 使用現有的 Gemini 客戶端，複用同一個 API

import google.generativeai as genai
from pydantic import BaseModel
from typing import Optional, List, Dict

# 假設你已經有 Gemini 初始化代碼：
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = genai.GenerativeModel("gemini-3.6-flash")

class MessageItem(BaseModel):
    role: str  # "user" 或 "model"
    content: str

class ChatRequest(BaseModel):
    messages: List[MessageItem]
    report_context: Optional[Dict] = None

class ChatResponse(BaseModel):
    content: str

def get_gemini_model():
    """獲取 Gemini 模型"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"DEBUG get_gemini_model: API Key 存在 = {bool(api_key)}")
        
        if not api_key:
            print("ERROR: GEMINI_API_KEY 為空")
            raise ValueError("GEMINI_API_KEY 環境變數未設置")
        
        print(f"DEBUG: 配置 Gemini...")
        genai.configure(api_key=api_key)
        
        print(f"DEBUG: 初始化模型...")
        model = genai.GenerativeModel("gemini-3.6-flash")
        
        print(f"DEBUG: 模型初始化成功")
        return model
    
    except Exception as e:
        print(f"ERROR in get_gemini_model: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

def get_tutor_system_prompt(report_context: dict = None) -> str:
    """教導小助手的系統提示詞"""
    base_prompt = """你是一個友善的 AI 小助手，專門幫助使用者理解旁通道攻擊分析平臺。

**你的職責：**
1. 用簡明易懂的語言解釋複雜的安全概念
2. 提供分步驟的使用指南
3. 回答關於平臺功能的問題
4. 在適當時提供程式碼範例

**平臺功能：**
- 第一步：選擇分析資料來源（上傳 Trace 與 Plaintext 或使用內建資料集）
- 第二步：配置 AES 版本和加密金鑰
- 第三步：選擇攻擊方法和評估方式
- 第四步：執行分析並查看結果

**回應規則：**
- 始終用繁體中文回應
- **極度簡練**：每次回答請控制在 2 至 3 個短句以內，直接切入重點，絕對不要長篇大論。
- **禁止冗言贅字**：不要出現「好的，我很樂意為您解答...」、「這是一個很好的問題...」等開場白或客套話。
- 如果不確定，說明並建議查看官方文件
- 盡量提供實用的例子"""
    
    # 如果有報告上下文，加入相關背景
    if report_context:
        context_info = f"""

**用戶當前的分析背景：**
- 攻擊類型：{report_context.get('attack_type', 'N/A')}
- 資料集：{report_context.get('dataset', 'N/A')}
- AES 版本：{report_context.get('aes_version', 'N/A')}
- 金鑰恢復狀態：{report_context.get('key_recovered', 'N/A')}
- SNR 值：{report_context.get('snr', 'N/A')}

請結合上述背景，用最精簡的語句回答使用者的問題，幫助其理解分析結果和安全含義。"""
        return base_prompt + context_info
    
    return base_prompt

@app.post("/api/ai/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest):
    """Gemini 教導小助手端點"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 環境變數未設置")
        
        genai.configure(api_key=api_key)
        
        # 1. 取得系統提示詞
        system_instruction = get_tutor_system_prompt(request.report_context)
        
        # 2. 初始化模型時帶入 system_instruction（這能確保 AI 嚴格遵守規則且不囉嗦）
        model = genai.GenerativeModel(
            model_name="gemini-3.6-flash",
            system_instruction=system_instruction
        )
        
        # 3. 轉換歷史對話格式（確保只有正確的 role 輪替與過濾髒資料）
        messages = []
        for msg in request.messages:
            content = msg.content.strip()
            
            # 【新增防護】如果內容包含提示詞殘留或亂碼，直接跳過不送給 AI
            if "sentences max" in content or "Sentence" in content or "max_output_tokens" in content:
                continue
                
            # 確保 role 符合 Gemini 的預期 ("user" 或 "model")
            role = "user" if msg.role == "user" else "model"
            messages.append({
                "role": role,
                "parts": [{"text": content}]
            })
        
        # 安全防護：如果前端沒有傳入歷史訊息，給一個預設的招呼或提示
        if not messages:
            messages = [{"role": "user", "parts": [{"text": "你好，請簡短介紹我能怎麼使用這個平台。"}]}]

        # 4. 調用 Gemini（不再把 system_instruction 當作 user message 塞進去）
        response = model.generate_content(
            messages,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=512,  # 限制最大輸出長度，防止它長篇大論
                temperature=0.3         # 降低溫度，讓回答更精準、嚴謹、不發散
            )
        )
        
        return ChatResponse(content=response.text)
    
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"\n❌ ERROR in ai_chat: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/ai/chat-with-context", response_model=ChatResponse)


@app.get("/api/ai/health")
async def ai_health():
    """
    檢查 Gemini AI 服務健康狀態
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    return {
        "status": "healthy" if api_key else "unconfigured",
        "api_configured": bool(api_key),
        "service": "gemini",
        "model": "gemini-3.6-flash"
    }

# ============================================================================
# 靜態文件和平臺頁面配置
# ============================================================================

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# 配置靜態文件路由
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 提供 platform.html
@app.get("/platform")
async def get_platform():
    """返回 platform.html 頁面"""
    try:
        platform_path = os.path.join(os.path.dirname(__file__), "..", "platform.html")
        with open(platform_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="platform.html 檔案未找到")

# ============================================================================
# 啟動伺服器
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)