import os
import time
import subprocess
import sys
import json
import uuid

def verify_qwen_integration():
    print("=== Qwen3 Integration Verification ===")
    
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service_script = os.path.join(repo_root, "src", "providers", "qwen3", "qwen3_service.py")
    output_wav = os.path.join(repo_root, "tests", "qwen_init_test.wav")
    task_dir = "/tmp/sonora/tasks"
    os.makedirs(task_dir, exist_ok=True)

    print("Starting Qwen3 Service...")
    process = subprocess.Popen(
        [sys.executable, service_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(3) 
    
    try:
        task_id = str(uuid.uuid4())
        task_payload = {
            "id": task_id,
            "type": "design",
            "text": "Hello world, this is a swarm test.",
            "timestamp": time.time()
        }
        
        task_file = os.path.join(task_dir, f"{task_id}.json")
        expected_output = os.path.join(repo_root, "shared_data", "outputs", f"{task_id}.wav")
        
        print(f"Dropping task: {task_file}")
        with open(task_file, "w") as f:
            json.dump(task_payload, f)
            
        print("Waiting for Qwen3 output...")
        for _ in range(10):
            if os.path.exists(expected_output):
                print(f"✅ Success: Output found at {expected_output}")
                # Move to final test path
                if os.path.exists(output_wav): os.remove(output_wav)
                os.rename(expected_output, output_wav)
                return True
            time.sleep(1)
            
        print("❌ Error: Timeout waiting for Qwen3 service")
        return False

    finally:
        print("Terminating service...")
        process.terminate()

if __name__ == "__main__":
    if verify_qwen_integration():
        print("VERIFICATION SUCCESSFUL")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED")
        sys.exit(1)
