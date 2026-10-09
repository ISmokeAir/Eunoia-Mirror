import urllib.request
import json
import time
import psutil
import sys

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except:
        return 0.0

def benchmark_ollama(model_name):
    print(f"\n--- Benchmark CPU Ollama: {model_name} ---")
    
    # Check if model exists, if not pull it
    print(f"Verificare/Descărcare model {model_name} (te rog așteaptă)...")
    import subprocess
    subprocess.run(["ollama", "pull", model_name], stdout=subprocess.DEVNULL)
    
    print("Start generare...")
    
    data = {
        "model": model_name,
        "prompt": "Ești un asistent concis într-o oglindă. Rezumă pe scurt ziua de azi și urează-mi o dimineață productivă.",
        "stream": False
    }
    
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    temp_before = get_cpu_temp()
    start_time = time.time()
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Eroare API: {e}")
        return
        
    end_time = time.time()
    temp_after = get_cpu_temp()
    
    duration = result['eval_duration'] / 1e9 # convert nanoseconds to seconds
    eval_count = result['eval_count']
    tps = eval_count / duration if duration > 0 else 0
    total_time = end_time - start_time
    
    print(f"Timp Total: {total_time:.2f}s | Timp Evaluare: {duration:.2f}s")
    print(f"Viteza Generare: {tps:.2f} TPS")
    print(f"Temperatura CPU: {temp_before:.1f}°C -> {temp_after:.1f}°C")
    print(f"Răspuns: {result['response'][:100]}...\n")

if __name__ == "__main__":
    print("===========================================")
    print("🐌 RASPBERRY PI 5 CPU BENCHMARK (OLLAMA)")
    print("===========================================")
    benchmark_ollama("qwen2.5:1.5b")
    benchmark_ollama("llama3.2:1b")
    print("Benchmark complet!")

