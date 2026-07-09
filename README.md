# amd-npu-sample

Minimal Python sample that downloads and runs an AMD NPU (VitisAI) model
using the [Foundry Local](https://github.com/microsoft/Foundry-Local) Python SDK.

## Prerequisites

- Windows on an AMD Ryzen AI (XDNA NPU) machine
- Foundry Local installed (CLI or SDK runtime)
- Python 3.11+

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python foundry_amd_npu.py
```

Edit `ALIAS` in `foundry_amd_npu.py` to any model alias in the catalog that
has an AMD NPU variant (check with `foundry model list --variants` — look for
`NPU / VitisAIExecutionProvider`).

