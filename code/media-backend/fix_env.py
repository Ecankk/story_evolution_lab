import os

env_path = ".env"

try:
    with open(env_path, "rb") as f:
        content = f.read()
    
    # Remove null bytes (0x00) which are common in UTF-16 when interpreted as ASCII/UTF-8
    clean_content = content.replace(b"\x00", b"")
    
    # Decode to string (fallback to latin-1 if utf-8 fails, then re-encode)
    try:
        text = clean_content.decode("utf-8")
    except UnicodeDecodeError:
        text = clean_content.decode("latin-1")
        
    lines = text.splitlines()
    clean_lines = [line.strip() for line in lines if line.strip()]
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_lines))
        f.write("\n")
        
    print(f"cleaned .env, size: {len(content)} -> {os.path.getsize(env_path)}")

except Exception as e:
    print(f"Error fixing .env: {e}")
