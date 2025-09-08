#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
from pathlib import Path
import difflib
from datetime import datetime
from config_manager import ConfigManager

class DotfilesManager:
    def __init__(self):
        self.repo_path = Path(__file__).parent.absolute()
        self.home_path = Path.home()
        self.config = ConfigManager(self.repo_path)
        
    def run_git_command(self, args):
        """Run a git command in the repo directory"""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e.stderr}")
            return None
    
    def get_config_files(self, pattern=""):
        """Get list of config files using configuration"""
        return self.config.get_config_files(pattern)
    
    def multi_select_files(self):
        """Interactive multi-select for files"""
        print("🔍 Scanning for configuration files...")
        files = self.get_config_files()
        
        if not files:
            print("❌ No configuration files found in ~/.config/")
            return []
        
        print(f"\n📁 Found {len(files)} configuration files:")
        print("Use numbers separated by spaces (e.g., '1 3 5') or 'all' for all files:")
        
        for i, file_path in enumerate(files, 1):
            repo_file = self.repo_path / file_path
            status = "✅" if repo_file.exists() else "➕"
            print(f"{i:3d}. {status} {file_path}")
        
        while True:
            try:
                selection = input("\n📝 Select files to add: ").strip()
                
                if selection.lower() == 'all':
                    return files
                
                if not selection:
                    return []
                
                indices = [int(x) for x in selection.split()]
                selected_files = []
                
                for idx in indices:
                    if 1 <= idx <= len(files):
                        selected_files.append(files[idx - 1])
                    else:
                        print(f"❌ Invalid selection: {idx}")
                        continue
                
                return selected_files
                
            except ValueError:
                print("❌ Invalid input. Use numbers separated by spaces or 'all'")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled")
                return []
    
    def add_files(self):
        """Add selected files to the repository"""
        selected_files = self.multi_select_files()
        
        if not selected_files:
            print("❌ No files selected")
            return
        
        print(f"\n📋 Adding {len(selected_files)} files to repository...")
        
        added_files = []
        for file_path in selected_files:
            source = self.home_path / file_path
            dest = self.repo_path / file_path
            
            if not source.exists():
                print(f"❌ Source file not found: {source}")
                continue
            
            # Create directory structure if needed
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Copy file
                import shutil
                shutil.copy2(source, dest)
                added_files.append(file_path)
                print(f"✅ Added: {file_path}")
            except Exception as e:
                print(f"❌ Failed to add {file_path}: {e}")
        
        if added_files:
            # Stage files in git
            for file_path in added_files:
                self.run_git_command(['add', str(file_path)])
            
            print(f"\n🎉 Successfully added {len(added_files)} files!")
            print("💡 Use 'commit' command to save changes")
    
    def show_diff(self, file_path=None):
        """Show differences between repo and filesystem files"""
        if file_path:
            files_to_check = [file_path]
        else:
            # Get all tracked files in repo
            tracked_files = self.run_git_command(['ls-files'])
            if not tracked_files:
                print("❌ No tracked files found")
                return
            files_to_check = tracked_files.split('\n')
        
        print("🔍 Checking for differences...\n")
        
        for file_rel_path in files_to_check:
            repo_file = self.repo_path / file_rel_path
            home_file = self.home_path / file_rel_path
            
            if not repo_file.exists():
                print(f"❌ Repo file not found: {file_rel_path}")
                continue
            
            if not home_file.exists():
                print(f"❌ Home file not found: {file_rel_path}")
                continue
            
            try:
                with open(repo_file, 'r') as f:
                    repo_content = f.readlines()
                with open(home_file, 'r') as f:
                    home_content = f.readlines()
                
                diff = list(difflib.unified_diff(
                    repo_content,
                    home_content,
                    fromfile=f"repo/{file_rel_path}",
                    tofile=f"home/{file_rel_path}",
                    lineterm=""
                ))
                
                if diff:
                    print(f"📄 {file_rel_path}:")
                    for line in diff:
                        if line.startswith('+++') or line.startswith('---'):
                            print(f"📁 {line}")
                        elif line.startswith('@@'):
                            print(f"🔵 {line}")
                        elif line.startswith('+'):
                            print(f"🟢 {line}")
                        elif line.startswith('-'):
                            print(f"🔴 {line}")
                        else:
                            print(f"   {line}")
                    print()
                else:
                    print(f"✅ {file_rel_path}: No differences")
            
            except Exception as e:
                print(f"❌ Error comparing {file_rel_path}: {e}")
    
    def commit_and_push(self):
        """Commit changes and push to remote"""
        # Check for staged changes
        status = self.run_git_command(['status', '--porcelain'])
        if not status:
            print("❌ No changes to commit")
            return
        
        print("📋 Current changes:")
        print(status)
        
        # Get commit message
        message = input("\n💬 Enter commit message (or press Enter for auto-generated): ").strip()
        
        if not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            template = self.config.get_commit_message_template()
            message = template.format(timestamp=timestamp)
        
        # Commit
        print("💾 Committing changes...")
        result = self.run_git_command(['commit', '-m', message])
        if result is None:
            return
        
        print(f"✅ Committed: {message}")
        
        # Push
        print("🚀 Pushing to remote...")
        result = self.run_git_command(['push'])
        if result is None:
            print("❌ Failed to push")
            return
        
        print("🎉 Successfully pushed to remote!")
    
    def restore_file(self):
        """Restore a file from git history"""
        # Get list of tracked files
        tracked_files = self.run_git_command(['ls-files'])
        if not tracked_files:
            print("❌ No tracked files found")
            return
        
        files = tracked_files.split('\n')
        
        print("📁 Select file to restore:")
        for i, file_path in enumerate(files, 1):
            print(f"{i:3d}. {file_path}")
        
        try:
            selection = int(input("\n📝 Enter file number: "))
            if not (1 <= selection <= len(files)):
                print("❌ Invalid selection")
                return
            
            selected_file = files[selection - 1]
            
            # Get commit history for this file
            log_result = self.run_git_command([
                'log', '--oneline', '--follow', '-n', '10', '--', selected_file
            ])
            
            if not log_result:
                print(f"❌ No history found for {selected_file}")
                return
            
            commits = log_result.split('\n')
            print(f"\n📅 Recent commits for {selected_file}:")
            for i, commit in enumerate(commits, 1):
                print(f"{i:3d}. {commit}")
            
            commit_selection = int(input("\n📝 Enter commit number to restore from: "))
            if not (1 <= commit_selection <= len(commits)):
                print("❌ Invalid commit selection")
                return
            
            commit_hash = commits[commit_selection - 1].split()[0]
            
            # Restore file from specific commit
            print(f"🔄 Restoring {selected_file} from commit {commit_hash}...")
            
            # Restore to repo
            result = self.run_git_command(['checkout', commit_hash, '--', selected_file])
            if result is None:
                return
            
            # Copy to home directory
            repo_file = self.repo_path / selected_file
            home_file = self.home_path / selected_file
            
            if repo_file.exists():
                import shutil
                home_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(repo_file, home_file)
                print(f"✅ Restored {selected_file} to home directory")
                
                # Stage the change
                self.run_git_command(['add', selected_file])
                print("💡 File staged for commit. Use 'commit' to save this restoration.")
            else:
                print(f"❌ Failed to restore {selected_file}")
        
        except (ValueError, KeyboardInterrupt):
            print("❌ Operation cancelled")

def main():
    manager = DotfilesManager()
    
    if len(sys.argv) < 2:
        print("🛠️  Dotfiles Manager")
        print("\nAvailable commands:")
        print("  add      - Add files to repository (interactive multi-select)")
        print("  diff     - Show differences between repo and filesystem")
        print("  commit   - Commit and push changes")
        print("  restore  - Restore a file from git history")
        print("\nUsage: python dotfiles_manager.py <command>")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'add':
        manager.add_files()
    elif command == 'diff':
        file_path = sys.argv[2] if len(sys.argv) > 2 else None
        manager.show_diff(file_path)
    elif command == 'commit':
        manager.commit_and_push()
    elif command == 'restore':
        manager.restore_file()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: add, diff, commit, restore")

if __name__ == "__main__":
    main()