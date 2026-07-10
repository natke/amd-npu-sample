# AMD NPU Foundry Local sample

Minimal repros for an incompatibility between ONNX Runtime and the AMD NPU
(VitisAI) EP, hit when running a model on the NPU via
[Foundry Local](https://github.com/microsoft/Foundry-Local).

Three ways to reproduce it, from easiest to most involved. See
[Bisection results](#bisection-results) below for the summary of what causes
the bug and where it's fixed.

## Prerequisites

- Windows on an AMD Ryzen AI (XDNA NPU) machine
- AMD Vitis AI EP installed (bug reproduces on **1.8.62**; fixed in **1.8.68+**)
- Python 3.11+ (for repros 2 and 3)

---

## Repro 1: Foundry Local CLI (easiest)

No Python required. Download and install the latest Foundry Local CLI
(**0.10.1**) from
[the Foundry-Local releases page](https://github.com/microsoft/Foundry-Local/releases#release-cli-preview-0.10.1),
then run any model with an AMD NPU variant:

```powershell
foundry model run qwen2.5-0.5b
```

The CLI ships with Core.WinML 1.2.3 (ORT 1.26.0), which triggers the bug on
Vitis EP 1.8.62.

---

## Repro 2: Foundry Local Python SDK

Uses `foundry_amd_npu.py` to download and run an NPU model via the Foundry
Local Python SDK. Same underlying Core.WinML as the CLI, so hits the same
bug — but useful when you want to script model selection or step through
manager/catalog behaviour.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python foundry_amd_npu.py

# Or pick a different model alias (default: qwen2.5-0.5b):
python foundry_amd_npu.py --model phi-3.5-mini
```

Pass any model alias in the catalog that has an AMD NPU variant via `--model`
(check with `foundry model list --variants` — look for
`NPU / VitisAIExecutionProvider`).

---

## Repro 3: Direct ORT-GenAI (choose your own ONNX Runtime version)

`genai_amd_npu.py` bypasses Foundry Local and runs the model directly with
`onnxruntime-genai-winml`. This lets you swap the ONNX Runtime version
independently of the Foundry Local Core, so you can bisect ORT / ORT-GenAI
versions against the AMD NPU EP.

It accepts the same `--model` alias as `foundry_amd_npu.py` (default:
`qwen2.5-0.5b`) and looks up the cached model folder in the Foundry Local
model cache. Run repro 1 or 2 first so the AMD NPU variant is downloaded.

```powershell
python -m venv .venv-genai
.\.venv-genai\Scripts\Activate.ps1
pip install -r requirements-genai.txt

# Install the ONNX Runtime version you want to test against
# (windowsml does NOT install onnxruntime unless you use its [with-ort] extra,
# so we install it explicitly to control the version we're bisecting.)
pip install "onnxruntime==1.26.0"

python genai_amd_npu.py

# Or with a different model alias:
python genai_amd_npu.py --model phi-3.5-mini

# To bisect, uninstall and reinstall with a different version:
pip install --force-reinstall "onnxruntime==1.23.2"
pip install --force-reinstall "onnxruntime-genai-winml==0.13.2"
```

---

## Bisection results

**Root cause:** The AMD Vitis AI **EP 1.8.62** introduced the incompatibility
with ONNX Runtime versions 1.25.0 or later. Earlier Vitis EP versions work;
1.8.62 exhibits the bug. The bug is fixed in Vitis EP version **1.8.68**.

### By ORT version (direct GenAI test via `genai_amd_npu.py`)

| ORT       | Status              |
| --------- | ------------------- |
| 1.24.x    | ✅ works            |
| 1.25.0    | ❌ bug introduced   |
| 1.26.0    | ❌ bug              |

### By Foundry Local WinML SDK version

Native Core is ABI-locked to a specific ORT major.minor + GenAI major.minor,
so the SDK-level bug tracks whichever ORT it ships with:

| SDK (WinML) | ORT        | GenAI  | WinML / WinAppSDK           | Status                          |
| ----------- | ---------- | ------ | --------------------------- | ------------------------------- |
| 0.8.2.2     | 1.23.2     | —      | —                           | ✅ (pre-1.25)                   |
| 0.9.0       | 1.23.2.3   | —      | —                           | ✅ (pre-1.25)                   |
| 1.0.0       | 1.23.2.3   | 0.13.1 | WinAppSDK 1.8.250916003     | ✅ (pre-1.25)                   |
| 1.1.0       | 1.23.2.3   | 0.13.2 | WinAppSDK 1.8.250916003     | ✅ confirmed (with EP 1.8.62)   |
| 1.2.0       | **1.26.0** | 0.14.0 | WinML 2.1.1                 | ❌ confirmed                    |
| 1.2.1       | **1.26.0** | 0.14.1 | WinML 2.1.1                 | ❌                              |
| 1.2.2       | **1.26.0** | 0.14.1 | WinML 2.1.1                 | ❌                              |
| 1.2.3       | **1.26.0** | 0.14.1 | WinML 2.1.1                 | ❌ confirmed                    |

**Cliff:** The WinML SDK jumped from ORT 1.23.2.3 (1.1.0) straight to 1.26.0
(1.2.0) — no WinML SDK build was ever shipped against ORT 1.24 or 1.25, which
is why the regression only surfaced at SDK 1.2.0.

### Foundry Local CLI mapping

| Foundry Local CLI | SDK / Core.WinML | ORT         |
| ----------------- | ---------------- | ----------- |
| 0.10.0            | 1.2.0            | 1.26.0 ❌   |
| 0.10.1            | 1.2.3            | 1.26.0 ❌   |

