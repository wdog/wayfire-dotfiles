#!/usr/bin/env python3

import json
import fnmatch
from pathlib import Path
from typing import Dict, List, Any, Optional
import os

class ConfigManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.config_file = repo_path / "config.json"
        self.gitignore_file = repo_path / ".gitignore"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        default_config = {
            "search_paths": ["~/.config"],
            "file_patterns": ["*"],
            "gitignore_patterns": [],
            "exclude_dirs": [".git", "__pycache__", "node_modules"],
            "max_file_size_mb": 1,
            "auto_add_to_gitignore": True,
            "backup_before_restore": True,
            "default_commit_template": "Update dotfiles - {timestamp}",
            "show_hidden_files": True,
            "sort_files_by": "name",
            "color_scheme": {
                "header": "blue",
                "selected": "white_on_blue",
                "success": "green", 
                "error": "red",
                "warning": "yellow",
                "info": "cyan",
                "special": "magenta"
            },
            "keybindings": {
                "select_all": ["a", "A"],
                "select_none": ["n", "N"], 
                "quit": ["q", "Q"],
                "help": ["h", "H", "?"]
            }
        }
        
        if not self.config_file.exists():
            # Create default config file
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                elif isinstance(value, dict) and isinstance(config[key], dict):
                    for subkey, subvalue in value.items():
                        if subkey not in config[key]:
                            config[key][subkey] = subvalue
            
            return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading config: {e}. Using defaults.")
            return default_config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_search_paths(self) -> List[Path]:
        """Get list of search paths, expanding ~ to home directory"""
        paths = []
        for path_str in self.config["search_paths"]:
            path = Path(path_str).expanduser()
            if path.exists():
                paths.append(path)
        return paths
    
    def should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included based on patterns and exclusions"""
        relative_path = file_path.relative_to(Path.home()) if file_path.is_relative_to(Path.home()) else file_path
        file_name = file_path.name
        
        # Check file size
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.config["max_file_size_mb"]:
                return False
        except (OSError, PermissionError):
            return False
        
        # Check if hidden files should be shown
        if not self.config["show_hidden_files"] and file_name.startswith('.') and file_name not in ['.bashrc', '.zshrc', '.profile']:
            return False
        
        # Check exclude directories
        for part in file_path.parts:
            if part in self.config["exclude_dirs"]:
                return False
        
        # Check gitignore patterns
        for pattern in self.config["gitignore_patterns"]:
            if fnmatch.fnmatch(str(relative_path), pattern) or fnmatch.fnmatch(file_name, pattern):
                return False
        
        # Check file patterns (if specified, file must match at least one)
        if self.config["file_patterns"] and self.config["file_patterns"] != ["*"]:
            matches_pattern = False
            for pattern in self.config["file_patterns"]:
                if fnmatch.fnmatch(file_name, pattern):
                    matches_pattern = True
                    break
            if not matches_pattern:
                return False
        
        return True
    
    def get_config_files(self, pattern: str = "") -> List[str]:
        """Get list of config files from all search paths"""
        files = []
        home_path = Path.home()
        
        for search_path in self.get_search_paths():
            if not search_path.exists():
                continue
            
            try:
                for file_path in search_path.rglob('*'):
                    if not file_path.is_file():
                        continue
                    
                    # Check if file should be included
                    if not self.should_include_file(file_path):
                        continue
                    
                    try:
                        relative_path = file_path.relative_to(home_path)
                        if pattern.lower() in str(relative_path).lower():
                            files.append(str(relative_path))
                    except ValueError:
                        # File is not relative to home, skip it
                        continue
            except (PermissionError, OSError):
                continue
        
        # Sort files
        if self.config["sort_files_by"] == "name":
            files.sort()
        elif self.config["sort_files_by"] == "path":
            files.sort(key=lambda x: (Path(x).parent, Path(x).name))
        elif self.config["sort_files_by"] == "size":
            files.sort(key=lambda x: (home_path / x).stat().st_size if (home_path / x).exists() else 0)
        
        return files
    
    def update_gitignore(self):
        """Update .gitignore file with patterns from config"""
        if not self.config["auto_add_to_gitignore"]:
            return
        
        gitignore_content = []
        
        # Read existing .gitignore if it exists
        if self.gitignore_file.exists():
            with open(self.gitignore_file, 'r') as f:
                gitignore_content = f.read().splitlines()
        
        # Add header comment
        header = "# Auto-generated patterns from dotfiles manager config"
        if header not in gitignore_content:
            gitignore_content.extend(["", header])
        
        # Add patterns that aren't already there
        for pattern in self.config["gitignore_patterns"]:
            if pattern not in gitignore_content:
                gitignore_content.append(pattern)
        
        # Write updated .gitignore
        with open(self.gitignore_file, 'w') as f:
            f.write('\n'.join(gitignore_content))
            if gitignore_content and not gitignore_content[-1].endswith('\n'):
                f.write('\n')
    
    def get_commit_message_template(self) -> str:
        """Get commit message template"""
        return self.config["default_commit_template"]
    
    def should_backup_before_restore(self) -> bool:
        """Check if files should be backed up before restoration"""
        return self.config["backup_before_restore"]
    
    def get_color_scheme(self) -> Dict[str, str]:
        """Get color scheme configuration"""
        return self.config["color_scheme"]
    
    def get_keybindings(self) -> Dict[str, List[str]]:
        """Get keybinding configuration"""
        return self.config["keybindings"]
    
    def is_key_bound_to(self, key: str, action: str) -> bool:
        """Check if a key is bound to a specific action"""
        bindings = self.get_keybindings()
        return action in bindings and key in bindings[action]
    
    def add_search_path(self, path: str):
        """Add a new search path"""
        if path not in self.config["search_paths"]:
            self.config["search_paths"].append(path)
            self.save_config()
    
    def remove_search_path(self, path: str):
        """Remove a search path"""
        if path in self.config["search_paths"]:
            self.config["search_paths"].remove(path)
            self.save_config()
    
    def add_gitignore_pattern(self, pattern: str):
        """Add a new gitignore pattern"""
        if pattern not in self.config["gitignore_patterns"]:
            self.config["gitignore_patterns"].append(pattern)
            self.save_config()
            self.update_gitignore()
    
    def remove_gitignore_pattern(self, pattern: str):
        """Remove a gitignore pattern"""
        if pattern in self.config["gitignore_patterns"]:
            self.config["gitignore_patterns"].remove(pattern)
            self.save_config()
            self.update_gitignore()
    
    def add_file_pattern(self, pattern: str):
        """Add a new file pattern"""
        if pattern not in self.config["file_patterns"]:
            self.config["file_patterns"].append(pattern)
            self.save_config()
    
    def remove_file_pattern(self, pattern: str):
        """Remove a file pattern"""
        if pattern in self.config["file_patterns"]:
            self.config["file_patterns"].remove(pattern)
            self.save_config()
    
    def export_config(self, file_path: Path):
        """Export configuration to a file"""
        with open(file_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def import_config(self, file_path: Path):
        """Import configuration from a file"""
        try:
            with open(file_path, 'r') as f:
                imported_config = json.load(f)
            
            # Validate and merge with current config
            for key, value in imported_config.items():
                if key in self.config:
                    self.config[key] = value
            
            self.save_config()
            self.update_gitignore()
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        if self.config_file.exists():
            self.config_file.unlink()
        self.config = self._load_config()
        self.update_gitignore()