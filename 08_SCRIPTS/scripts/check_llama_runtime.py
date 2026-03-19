try:
    import torch
    import transformers
    print("System: 🤖 Using Hugging Face transformers with PyTorch.")
except ImportError:
    print("System: ⚠️ transformers not installed.")

try:
    from llama_cpp import Llama
    print("System: 🧠 llama.cpp (GGUF-based) detected.")
except ImportError:
    print("System: ❌ llama.cpp not detected.")

try:
    import requests
    r = requests.get("http://localhost:11434")
    if r.ok:
        print("System: 🧱 Ollama detected on localhost.")
except:
    print("System: ❌ Ollama not active.")

try:
    import gradio
    print("System: 🌐 WebUI system (Gradio/text-gen-webui) likely in use.")
except ImportError:
    pass
