"""
Script to run both search_api and personalize_api FastAPI servers
"""
import subprocess
import sys
import os

def main():
    """Run both FastAPI servers"""
    
    # Get the directory of this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Starting FastAPI servers...")
    print("=" * 50)
    
    # Option 1: Run search_api on port 8000
    print("\nTo run search_api server on port 8000:")
    print("uvicorn app.search_api:app --host 0.0.0.0 --port 8000 --reload")
    
    # Option 2: Run personalize_api on port 8001
    print("\nTo run personalize_api server on port 8001:")
    print("uvicorn app.personalize_api:app --host 0.0.0.0 --port 8001 --reload")
    
    print("\n" + "=" * 50)
    print("Choose which server to run:")
    print("1. search_api (port 8000)")
    print("2. personalize_api (port 8001)")
    print("3. Both (requires 2 terminal windows)")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        os.chdir(base_dir)
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.search_api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    elif choice == "2":
        os.chdir(base_dir)
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.personalize_api:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ])
    elif choice == "3":
        print("\nPlease open 2 terminal windows and run:")
        print("\nTerminal 1:")
        print(f"cd {base_dir}")
        print("uvicorn app.search_api:app --host 0.0.0.0 --port 8000 --reload")
        print("\nTerminal 2:")
        print(f"cd {base_dir}")
        print("uvicorn app.personalize_api:app --host 0.0.0.0 --port 8001 --reload")
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
