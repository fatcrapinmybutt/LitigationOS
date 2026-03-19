import os
import subprocess
import sys

# ========== STAGE 1: ENVIRONMENT SETUP ==========
def pip_install(pkg):
    subprocess.call([sys.executable, "-m", "pip", "install", pkg])

print("🛠️ Installing required packages...")
required = ["transformers", "torch", "accelerate"]
for pkg in required:
    pip_install(pkg)

# ========== STAGE 2: MODEL SETUP ==========
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

print("📦 Loading model and tokenizer...")

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

# ========== STAGE 3: PROMPT THE MODEL ==========
print("💬 Running inference...\n")

prompt = """You are a Michigan family law assistant. Explain how MCL 722.27 allows a parent to file for custody modification when the other parent is obstructing parenting time. Use IRAC format."""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=400)
result = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("📜 RESPONSE:\n")
print(result)
