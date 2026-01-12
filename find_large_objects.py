
import subprocess

def get_large_objects():
    # Get all objects
    cmd = ["git", "rev-list", "--objects", "--all"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    objects = result.stdout.strip().split("\n")
    
    data = []
    print(f"Found {len(objects)} objects. Checking sizes...")

    for line in objects:
        parts = line.split(maxsplit=1)
        sha = parts[0]
        path = parts[1] if len(parts) > 1 else "(no path)"
        
        # Get size
        size_cmd = ["git", "cat-file", "-s", sha]
        size_res = subprocess.run(size_cmd, capture_output=True, text=True)
        try:
            size = int(size_res.stdout.strip())
            data.append((size, sha, path))
        except:
            pass
            
    # Sort by size descending
    data.sort(key=lambda x: x[0], reverse=True)
    
    print("\nTop 10 largest objects:")
    for size, sha, path in data[:10]:
        mb = size / (1024 * 1024)
        print(f"{mb:.2f} MB - {sha} - {path}")

if __name__ == "__main__":
    get_large_objects()
