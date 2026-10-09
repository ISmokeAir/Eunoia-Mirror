import time
import sys
from pathlib import Path

# Setup Hailo environment paths
repo_root = Path("/home/atei/ProjectSM/hailo-apps")
sys.path.insert(0, str(repo_root))

from hailo_platform import VDevice
from hailo_platform.genai import LLM
from hailo_apps.python.core.common.defines import SHARED_VDEVICE_GROUP_ID

def main():
    model_path = sys.argv[1]
    text = "Rezumă pe scurt ziua de azi și urează-mi o dimineață productivă."
    
    print(f"\n[{Path(model_path).name}] Încărcare model...")
    start_load = time.time()
    
    params = VDevice.create_params()
    params.group_id = SHARED_VDEVICE_GROUP_ID
    vdevice = VDevice(params)
    llm = LLM(vdevice, model_path)
    
    load_time = time.time() - start_load
    print(f"✓ Încărcat în {load_time:.2f}s")
    
    prompt = [
        {"role": "system", "content": "Ești un asistent concis. Răspunzi doar în limba română."},
        {"role": "user", "content": text}
    ]
    
    start_gen = time.time()
    response = llm.generate_all(prompt=prompt, temperature=0.7, max_generated_tokens=200)
    end_gen = time.time()
    
    duration = end_gen - start_gen
    clean_response = response.split(". [{'type'")[0].replace("<|im_end|>", "").strip()
    approx_tokens = len(clean_response) / 4
    tps = approx_tokens / duration if duration > 0 else 0
    
    print(f"Timp: {duration:.2f}s | TPS estimat: {tps:.2f}")
    print(f"Răspuns: {clean_response[:100]}...\n")

if __name__ == "__main__":
    main()
