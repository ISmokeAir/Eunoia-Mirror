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
    model_path = "/home/atei/ProjectSM/Qwen3-1.7B-Instruct.hef"
    
    print("===========================================")
    print("🤖 Smart Mirror AI Assistant - Chat Test")
    print("===========================================")
    print(f"Loading model: {model_path} ...")
    
    start_load = time.time()
    
    params = VDevice.create_params()
    params.group_id = SHARED_VDEVICE_GROUP_ID
    
    try:
        vdevice = VDevice(params)
        llm = LLM(vdevice, model_path)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"✓ Model loaded in {time.time() - start_load:.2f} seconds.")
    print("Type 'exit' or 'quit' to close.")
    print("-" * 50)

    # REPL loop
    while True:
        try:
            user_input = input("\n👤 Tu: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue

            prompt = [
                {"role": "system", "content": [{"type": "text", "text": 'You are a helpful, smart, and concise AI assistant for a smart mirror. Speak in Romanian.'}]},
                {"role": "user", "content": [{"type": "text", "text": user_input}]}
            ]

            print("🧠 Asistent: ", end="", flush=True)
            
            start_gen = time.time()
            # We don't have streaming in the simple API out of the box, so we measure total time
            # For streaming, we would use generate() iterator if available. Let's just use generate_all
            response = llm.generate_all(prompt=prompt, temperature=0.7, max_generated_tokens=256)
            end_gen = time.time()

            clean_response = response.split(". [{'type'")[0].replace("<|im_end|>", "").strip()
            print(clean_response)
            
            duration = end_gen - start_gen
            # Rough token estimate (chars / 4)
            approx_tokens = len(clean_response) / 4
            tps = approx_tokens / duration if duration > 0 else 0
            
            print(f"\n[⏱️ Generat in {duration:.2f}s (~{tps:.1f} tokens/sec)]")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError generating response: {e}")
            break

    # Cleanup
    if llm:
        llm.release()
    if vdevice:
        vdevice.release()
    print("\nGoodbye!")

if __name__ == "__main__":
    main()

