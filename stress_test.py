import time
import sys
import json
import psutil
from pathlib import Path

# Setup Hailo environment paths
repo_root = Path("/home/atei/ProjectSM/hailo-apps")
sys.path.insert(0, str(repo_root))

from hailo_platform import VDevice
from hailo_platform.genai import LLM
from hailo_apps.python.core.common.defines import SHARED_VDEVICE_GROUP_ID

PROMPTS = [
    # 1. Simple queries
    "Salut, cum mă îmbrac azi dacă afară plouă?",
    "Cât fac 124 * 43?",
    "Spune-mi o scurtă poveste despre o oglindă magică.",
    
    # 2. Logic and Reasoning
    "Am 5 mere. Îi dau lui Ion 2. Apoi cumpăr încă 3. Câte mere am acum? Explică pas cu pas.",
    "Dacă mâine a fost joi, ce zi e azi?",
    
    # 3. Long generation (stress test)
    "Explică detaliat teoria relativității a lui Einstein, dar folosește un limbaj simplu de înțeles pentru un copil de 10 ani. Scrie minim 3 paragrafe.",
    "Scrie o rețetă completă pentru sarmale, incluzând ingrediente, pași de preparare și timp de gătire.",
    
    # 4. Multilingual / Translation
    "Tradu următoarea frază în engleză, franceză și spaniolă: 'Oglinda fermecată îmi arată viitorul în fiecare dimineață.'",
    
    # 5. Smart Mirror specific
    "Ești un asistent inteligent într-o oglindă. Creează un scurt rezumat al știrilor dimineții (inventează 3 știri pozitive) și urează-mi o zi bună."
]

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except:
        return 0.0

def main():
    model_path = "/home/atei/ProjectSM/Qwen3-1.7B-Instruct.hef"
    results = []
    
    print("Starting Stress Test...")
    start_load = time.time()
    params = VDevice.create_params()
    params.group_id = SHARED_VDEVICE_GROUP_ID
    
    try:
        vdevice = VDevice(params)
        llm = LLM(vdevice, model_path)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"Model loaded in {time.time() - start_load:.2f} seconds.")
    
    # We will run the prompts multiple times to generate heat and stress
    RUNS = 3
    total_prompts = len(PROMPTS) * RUNS
    current_prompt = 0
    
    for run in range(RUNS):
        for text in PROMPTS:
            current_prompt += 1
            print(f"--- Prompt {current_prompt}/{total_prompts} ---")
            
            prompt = [
                {"role": "system", "content": [{"type": "text", "text": "Ești un asistent inteligent, concis și util. Răspunzi doar în limba română."}]},
                {"role": "user", "content": [{"type": "text", "text": text}]}
            ]
            
            temp_before = get_cpu_temp()
            cpu_before = psutil.cpu_percent(interval=None)
            
            start_gen = time.time()
            response = llm.generate_all(prompt=prompt, temperature=0.7, max_generated_tokens=300)
            end_gen = time.time()
            
            clean_response = response.split(". [{'type'")[0].replace("<|im_end|>", "").strip()
            
            temp_after = get_cpu_temp()
            cpu_after = psutil.cpu_percent(interval=None)
            
            duration = end_gen - start_gen
            approx_tokens = len(clean_response) / 4
            tps = approx_tokens / duration if duration > 0 else 0
            
            result = {
                "run": run + 1,
                "prompt": text,
                "response": clean_response,
                "duration_sec": round(duration, 2),
                "approx_tps": round(tps, 2),
                "temp_before": temp_before,
                "temp_after": temp_after
            }
            results.append(result)
            
            print(f"Time: {duration:.2f}s | TPS: {tps:.2f} | Temp: {temp_after:.1f}°C")
            time.sleep(1) # Small pause

    if llm:
        llm.release()
    if vdevice:
        vdevice.release()
        
    with open("/home/atei/ProjectSM/stress_test_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("Stress test complete. Results saved.")

if __name__ == "__main__":
    main()

