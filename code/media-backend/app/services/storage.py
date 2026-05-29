import json
import os
import uuid
from typing import Any, Dict, List

from app.core.config import settings

def _read_json_safe(path: str) -> Dict[str, Any]:
    """Robustly read JSON file. Returns empty dict if file missing or corrupt."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            # Handle empty file explicitly
            content = f.read().strip()
            if not content: 
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️ [Storage] Corrupt JSON at {path}: {e}. Resetting to empty.")
        return {}

def _ensure_data_files():
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    # Just ensure files exist, don't validate content here (handled by safe read)
    for path in [settings.STORIES_PATH, os.path.join(settings.DATA_DIR, "temp_stories.json")]:
        if not os.path.exists(path):
             with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

# --- One-Story-Per-File Architecture ---

def _get_stories_dir():
    path = os.path.join(settings.DATA_DIR, "stories")
    os.makedirs(path, exist_ok=True)
    return path

def _get_story_path(story_id: str) -> str:
    return os.path.join(_get_stories_dir(), f"{story_id}.json")

def _migrate_legacy_data():
    """Migrate from monolithic temp_stories.json/stories.db to individual files."""
    legacy_temp = os.path.join(settings.DATA_DIR, "temp_stories.json")
    
    # 1. Load Legacy Data
    data_to_migrate = {}
    
    # From Main DB
    if os.path.exists(settings.STORIES_PATH):
        main = _read_json_safe(settings.STORIES_PATH)
        data_to_migrate.update(main)
        
    # From Temp
    if os.path.exists(legacy_temp):
        temp = _read_json_safe(legacy_temp)
        data_to_migrate.update(temp)
        
    # 2. Write to Individual Files
    count = 0
    for sid, turns in data_to_migrate.items():
        path = _get_story_path(sid)
        if not os.path.exists(path) and turns: # Don't overwrite if already exists (safe migration)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(turns, f, ensure_ascii=False, indent=2)
            count += 1
            
    if count > 0:
        print(f"✅ [Storage] Migrated {count} stories to single-file storage.")
        
    # Optional: Rename legacy files to .bak?
    # For now, we leave them as backup but don't read them anymore.

def _ensure_data_files():
    # Helper to ensure directory exists. Migration runs on module import or first load.
    _get_stories_dir()

# Run migration lazily or globally?
# Let's run it once on first load_all_stories or write.
_MIGRATION_DONE = False

def _check_migration():
    global _MIGRATION_DONE
    if not _MIGRATION_DONE:
        _migrate_legacy_data()
        _MIGRATION_DONE = True

def load_all_stories() -> Dict[str, List[Dict[str, Any]]]:
    """
    Scans data/stories/*.json and returns all.
    """
    _check_migration()
    stories_dir = _get_stories_dir()
    db = {}
    
    try:
        files = os.listdir(stories_dir)
        for fname in files:
            if fname.endswith(".json"):
                sid = fname[:-5]
                path = os.path.join(stories_dir, fname)
                db[sid] = _read_json_safe(path)
    except OSError as e:
        print(f"Error scanning stories dir: {e}")
        
    return db

def _save_story_file(story_id: str, turns: List[Dict[str, Any]]) -> None:
    _ensure_data_files()
    path = _get_story_path(story_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(turns, f, ensure_ascii=False, indent=2)

def create_story() -> str:
    story_id = str(uuid.uuid4())[:8]
    _save_story_file(story_id, [])
    return story_id

def get_story_turns(story_id: str) -> List[Dict[str, Any]]:
    _check_migration()
    path = _get_story_path(story_id)
    if os.path.exists(path):
        return _read_json_safe(path)
    return []

def append_turns(story_id: str, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    _check_migration()
    # Read-Modify-Write for single file is safer than monolithic
    cur = get_story_turns(story_id)
    start_turn = len(cur)

    saved = []
    for i, t in enumerate(turns):
        t2 = dict(t)
        t2["story_id"] = story_id
        t2["turn"] = start_turn + i + 1
        saved.append(t2)
        cur.append(t2)

    _save_story_file(story_id, cur)
    return saved

def update_turn(story_id: str, turn_index: int, new_text: str) -> List[Dict[str, Any]]:
    story_data = get_story_turns(story_id)
    if not story_data or turn_index >= len(story_data):
        return []
    
    story_data[turn_index]["text"] = new_text
    _save_story_file(story_id, story_data)
    return story_data

def delete_turn(story_id: str, turn_index: int) -> List[Dict[str, Any]]:
    story_data = get_story_turns(story_id)
    if not story_data or turn_index >= len(story_data):
        return []
    
    story_data.pop(turn_index)
    
    # Re-index
    for i, t in enumerate(story_data):
        t["turn"] = i + 1
        
    _save_story_file(story_id, story_data)
    return story_data

def overwrite_story_turns(story_id: str, turns: List[Dict[str, Any]]) -> None:
    _save_story_file(story_id, turns)

def save_story(story_id: str) -> bool:
    # Deprecated concept: "Saving" used to mean promote temp->main.
    # Now all stories are persistent files.
    # We can just return True.
    return True

def list_saved_stories() -> List[Dict[str, Any]]:
    """List stories in main db"""
    main_db = _read_json_safe(settings.STORIES_PATH)
    
    history = []
    for sid, turns in main_db.items():
        if not turns: continue
        title = turns[0]["text"][:30] + "..." if turns else "Empty Story"
        history.append({
            "story_id": sid,
            "title": title,
            "turn_count": len(turns),
            "last_updated": turns[-1].get("timestamp", "") 
        })
    return sorted(history, key=lambda x: x["last_updated"], reverse=True)

# --- Multiverse Graph Management ---

def _get_mv_index_path():
    return os.path.join(settings.DATA_DIR, "multiverse_index.json")

def get_multiverse_graph() -> Dict[str, Dict[str, Any]]:
    """
    Returns the graph structure: { story_id: { parent_id: str, source_turn: int, created_at: str } }
    """
    return _read_json_safe(_get_mv_index_path())

def record_branch(new_sid: str, parent_sid: str, source_turn: int):
    """
    Records a branching event in the multiverse index.
    """
    path = _get_mv_index_path()
    index = _read_json_safe(path)
    
    import datetime
    index[new_sid] = {
        "parent_id": parent_sid,
        "source_turn": source_turn, # The turn index in PARENT that this new story continues FROM (or branches AT)
        "created_at": datetime.datetime.now().isoformat()
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def get_story_metadata(story_id: str) -> Dict[str, Any]:
    index = get_multiverse_graph()
    return index.get(story_id, {})
