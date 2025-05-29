import subprocess
import sys
import os
import json
import re

def test_ollama():
    # Test prompts
    prompts = [
        "Hello",
        """Generate a JSON object with a single field named test containing the value 123.
Output only the JSON, no explanations or markdown."""
    ]
    
    try:
        # Print environment info
        print("Python version:", sys.version)
        print("Current working directory:", os.getcwd())
        print("PATH:", os.environ.get('PATH', ''))
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\nTest {i}:")
            print("Running Ollama command...")
            process = subprocess.Popen(
                ["ollama", "run", "codellama:latest"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy()
            )
            
            print("Sending prompt:", repr(prompt))
            stdout, stderr = process.communicate(input=prompt, timeout=30)
            
            print("\nProcess return code:", process.returncode)
            print("\nSTDOUT:")
            print(stdout)
            print("\nSTDERR:")
            print(stderr)
            
            # Try to parse JSON if this was a JSON test
            if i == 2:
                try:
                    # Clean the output and try to parse JSON
                    output = stdout.strip()
                    json_match = re.search(r'\{[\s\S]*\}', output)
                    if json_match:
                        json_str = json_match.group(0)
                        data = json.loads(json_str)
                        print("\nParsed JSON:", json.dumps(data, indent=2))
                except Exception as e:
                    print("\nJSON parsing failed:", str(e))
        
    except Exception as e:
        print("Error:", str(e))
        print("Error type:", type(e).__name__)

if __name__ == "__main__":
    test_ollama() 