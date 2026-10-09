import time
import sys
import os
import glob
import psutil
from pathlib import Path

# Setup Hailo environment paths
repo_root = Path("/home/atei/ProjectSM/hailo-apps")
sys.path.insert(0, str(repo_root))

from hailo_platform import VDevice
from hailo_platform.genai import LLM
from hailo_apps.python.core.common.defines import SHARED_VDEVICE_GROUP_ID

PROMPTS = [
    "Ești un asistent inteligent într-o oglindă. Rezumă pe scurt ziua de azi și urează-mi o dimineață productivă."
]

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except:
        return 0.0

def benchmark_model(model_path, vdevice):
    print(f"\n[{model_path.name}] Încărcare model...")
    try:
        start_load = time.time()
        llm = LLM(vdevice, str(model_path))
        load_time = time.time() - start_load
        print(f"✓ Încărcat în {load_time:.2f}s")
        
        results = []
        for i, text in enumerate(PROMPTS):
            print(f"Rulare prompt {i+1}...")
            prompt = [
                {"role": "system", "content": [{"type": "text", "text": "Ești un asistent concis. Răspunzi doar în limba română."}]},
                {"role": "user", "content": [{"type": "text", "text": text}]}
            ]
            
            temp_before = get_cpu_temp()
            start_gen = time.time()
            # Generate
            response = llm.generate_all(prompt=prompt, temperature=0.7, max_generated_tokens=200)
            end_gen = time.time()
            
            # Context clear to avoid full cache error
            llm.clear_context()
            
            temp_after = get_cpu_temp()
            duration = end_gen - start_gen
            clean_response = response.split(". [{'type'")[0].replace("<|im_end|>", "").strip()
            
            approx_tokens = len(clean_response) / 4
            tps = approx_tokens / duration if duration > 0 else 0
            
            print(f"Timp: {duration:.2f}s | TPS estimat: {tps:.2f} | Temp: {temp_after:.1f}°C")
            print(f"Răspuns: {clean_response[:100]}...\n")
            
            results.append({
                "duration": duration,
                "tps": tps,
                "temp_after": temp_after,
                "response_sample": clean_response
            })
            
        llm.release()
        return load_time, results
    except Exception as e:
        print(f"Eroare la testarea {model_path.name}: {e}")
        return None, None

def main():
    print("===========================================")
    print("🏆 Hailo-10H Model Benchmark (LLM Only)")
    print("===========================================")
    
    # Get all LLM .hef files (excluding Whisper and VL)
    all_hefs = glob.glob("/home/atei/ProjectSM/*.hef")
    llm_hefs = [Path(p) for p in all_hefs if "Whisper" not in p and "VL" not in p]
    
    print(f"Modele găsite spre testare: {len(llm_hefs)}")
    
    params = VDevice.create_params()
    params.group_id = SHARED_VDEVICE_GROUP_ID
    try:
        vdevice = VDevice(params)
    except Exception as e:
        print(f"Nu s-a putut inițializa VDevice: {e}")
        return

    summary = {}
    
    for model_path in llm_hefs:
        load_time, res = benchmark_model(model_path, vdevice)
        if res:
            summary[model_path.name] = {
                "load_time": load_time,
                "avg_tps": sum(r["tps"] for r in res) / len(res),
                "avg_duration": sum(r["duration"] for r in res) / len(res),
                "sample_response": res[0]["response_sample"]
            }
            
    vdevice.release()
    
    print("\n\n===========================================")
    print("📊 REZULTATE FINALE BENCHMARK")
    print("===========================================")
    # Sort by highest TPS
    sorted_summary = sorted(summary.items(), key=lambda x: x[1]["avg_tps"], reverse=True)
    
    with open("/home/atei/ProjectSM/benchmark_summary.md", "w") as f:
        f.write("# Rezultate Benchmark LLM-uri (Hailo-10H)\n\n")
        f.write("| Model | Load Time (s) | Generare Medie (s) | Viteza (TPS) | Exemplu Răspuns |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        
        for name, data in sorted_summary:
            safe_resp = data["sample_response"].replace('\n', ' ')
            if len(safe_resp) > 80:
                safe_resp = safe_resp[:77] + "..."
            
            line = f"| **{name}** | {data['load_time']:.2f}s | {data['avg_duration']:.2f}s | **{data['avg_tps']:.1f}** | {safe_resp} |\n"
            print(f"- {name}: {data['avg_tps']:.1f} TPS")
            f.write(line)
            
    print("\nRaportul detaliat a fost salvat în benchmark_summary.md")

if __name__ == "__main__":
    main()

