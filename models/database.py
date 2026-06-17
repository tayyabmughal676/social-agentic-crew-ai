import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

class WorkflowDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "storage/db/workflows.db")
        
        # Ensure database directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with workflow table"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step TEXT,
                    progress_percentage REAL DEFAULT 0.0,
                    completed_steps TEXT,  -- JSON array
                    estimated_completion TEXT,  -- ISO datetime
                    error_details TEXT,  -- JSON object
                    result TEXT,           -- Generated content output
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
            
            # Non-destructive migration to add 'result' column if table already exists
            try:
                conn.execute("ALTER TABLE workflows ADD COLUMN result TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists, safe to ignore
                pass
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup and concurrency safety"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_workflow(self, workflow_id: str, topic: str) -> None:
        """Create a new workflow record"""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO workflows 
                (workflow_id, topic, status, current_step, progress_percentage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (workflow_id, topic, "in_progress", "initializing", 0.0, now, now))
            conn.commit()
    
    def update_workflow(self, workflow_id: str, **kwargs) -> None:
        """Update workflow fields"""
        now = datetime.now().isoformat()
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ["status", "current_step", "progress_percentage", "completed_steps", "estimated_completion", "error_details", "result"]:
                set_clauses.append(f"{key} = ?")
                if key in ["completed_steps", "error_details"] and isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if not set_clauses:
            return
        
        set_clauses.append("updated_at = ?")
        values.append(now)
        values.append(workflow_id)
        
        with self.get_connection() as conn:
            conn.execute(f"""
                UPDATE workflows 
                SET {', '.join(set_clauses)}
                WHERE workflow_id = ?
            """, values)
            conn.commit()
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a single workflow by ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM workflows WHERE workflow_id = ?", 
                (workflow_id,)
            ).fetchone()
            
            if row:
                workflow = dict(row)
                # Parse JSON fields
                if workflow["completed_steps"]:
                    workflow["completed_steps"] = json.loads(workflow["completed_steps"])
                else:
                    workflow["completed_steps"] = []
                    
                if workflow["error_details"]:
                    workflow["error_details"] = json.loads(workflow["error_details"])
                else:
                    workflow["error_details"] = None
                    
                return workflow
            return None
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM workflows ORDER BY created_at DESC"
            ).fetchall()
            
            workflows = []
            for row in rows:
                workflow = dict(row)
                # Parse JSON fields
                if workflow["completed_steps"]:
                    workflow["completed_steps"] = json.loads(workflow["completed_steps"])
                else:
                    workflow["completed_steps"] = []
                    
                if workflow["error_details"]:
                    workflow["error_details"] = json.loads(workflow["error_details"])
                else:
                    workflow["error_details"] = None
                    
                workflows.append(workflow)
            
            return workflows
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM workflows WHERE workflow_id = ?", 
                (workflow_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_old_workflows(self, days: int = 7) -> int:
        """Clean up workflows older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM workflows WHERE created_at < ? AND status IN ('completed', 'error', 'rejected')",
                (cutoff_date,)
            )
            conn.commit()
            return cursor.rowcount

# Global database instance
db = WorkflowDatabase()
