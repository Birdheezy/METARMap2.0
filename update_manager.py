#!/usr/bin/env python3
"""
METARMap Update Manager
Handles system updates, validation, and backup operations
"""

import os
import subprocess
import shutil
import datetime
import json
import ast
import sys
from typing import Tuple, Dict, List, Optional


def get_python_path() -> str:
    """Get the appropriate Python interpreter path."""
    # Try virtual environment first
    venv_path = '/home/pi/metar/bin/python3'
    if os.path.exists(venv_path):
        return venv_path
    
    # Fall back to system Python
    system_path = '/usr/bin/python3'
    if os.path.exists(system_path):
        return system_path
    
    # Last resort
    return 'python3'


def check_disk_space(path: str, required_mb: int = 100) -> bool:
    """Check if there's enough disk space available."""
    try:
        statvfs = os.statvfs(path)
        free_space_mb = (statvfs.f_frsize * statvfs.f_bavail) / (1024 * 1024)
        return free_space_mb >= required_mb
    except Exception:
        return True  # If we can't check, assume it's okay


def validate_config_file(config_path: str) -> Tuple[bool, str]:
    """Validate that a config.py file is syntactically correct and has required structure."""
    try:
        # Check if file exists
        if not os.path.exists(config_path):
            return False, "Config file does not exist"
        
        # Check file size (should not be empty)
        if os.path.getsize(config_path) < 100:
            return False, "Config file appears to be too small or empty"
        
        # Test Python syntax
        python_path = get_python_path()
        result = subprocess.run(
            [python_path, '-m', 'py_compile', config_path],
            capture_output=True, text=True, cwd='/home/pi'
        )
        
        if result.returncode != 0:
            return False, f"Python syntax error: {result.stderr}"
        
        # Check for required variables (basic check)
        with open(config_path, 'r') as f:
            content = f.read()
            
        required_vars = ['AIRPORTS_FILE', 'PIXEL_PIN', 'NUM_PIXELS', 'BRIGHTNESS']
        missing_vars = []
        
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        if missing_vars:
            return False, f"Missing required variables: {', '.join(missing_vars)}"
        
        # Check for unclosed brackets (common issue)
        open_brackets = content.count('[') + content.count('(') + content.count('{')
        close_brackets = content.count(']') + content.count(')') + content.count('}')
        
        if open_brackets != close_brackets:
            return False, f"Bracket mismatch: {open_brackets} open, {close_brackets} close"
        
        return True, "Config file is valid"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def parse_config_file(config_path: str) -> Dict:
    """Parse a config.py file and extract all variable assignments."""
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Parse the Python code
        tree = ast.parse(content)
        
        config_dict = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Convert the value to a string representation
                        try:
                            # For simple values, we can evaluate them
                            if isinstance(node.value, (ast.Constant, ast.Num, ast.Str)):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.Tuple):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.List):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.Dict):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.NameConstant):  # True, False, None
                                config_dict[target.id] = ast.literal_eval(node.value)
                            else:
                                # For complex expressions, store as string
                                config_dict[target.id] = ast.unparse(node.value)
                        except:
                            # If we can't evaluate, store as string
                            config_dict[target.id] = ast.unparse(node.value)
        
        # Validate that we got some config
        if not config_dict:
            raise Exception("No configuration variables found in file")
        
        return config_dict
        
    except Exception as e:
        print(f"Error parsing config file: {e}")
        raise Exception(f"Failed to parse config file: {str(e)}")


def create_backup() -> Tuple[str, int]:
    """Create a timestamped backup of all tracked files."""
    # Check disk space before backup
    if not check_disk_space('/home/pi', 100):
        raise Exception("Insufficient disk space for backup (need at least 100MB)")
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'/home/pi/BACKUP/{timestamp}'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Get list of tracked files
    try:
        tracked_files_output = subprocess.check_output(
            ['/usr/bin/git', 'ls-files'], 
            text=True, 
            cwd='/home/pi'
        ).strip()
        
        tracked_files = tracked_files_output.split('\n') if tracked_files_output else []
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to get tracked files: {e}")
    
    # Also backup important files even if they're not tracked
    important_files = ['config.py', 'airports.txt']
    for file in important_files:
        file_path = f'/home/pi/{file}'
        if file not in tracked_files and os.path.exists(file_path):
            tracked_files.append(file)
    
    # Copy files to backup directory
    files_backed_up = 0
    for file in tracked_files:
        if not file or file.startswith('BACKUP/'):
            continue
            
        source_path = f'/home/pi/{file}'
        dest_path = f'{backup_dir}/{file}'
        
        if not os.path.exists(source_path):
            continue
            
        # Create destination directory if needed
        dest_dir = os.path.dirname(dest_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        # Copy the file
        try:
            shutil.copy2(source_path, dest_path)
            files_backed_up += 1
        except Exception as e:
            print(f"Error copying file {file}: {e}")
    
    # Verify backup was created
    if files_backed_up == 0:
        raise Exception("No files were backed up")
    
    return backup_dir, files_backed_up


def check_for_updates() -> Dict:
    """Check for available updates from the remote repository."""
    try:
        # Check if git is available
        try:
            subprocess.run(['/usr/bin/git', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Git is not installed or not accessible")
        
        # Get current branch
        branch_cmd = subprocess.run(['/usr/bin/git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                  capture_output=True, text=True, check=True,
                                  cwd='/home/pi')
        current_branch = branch_cmd.stdout.strip()
        
        # Fetch updates from remote
        subprocess.run(['/usr/bin/git', 'fetch', 'origin', current_branch],
                      capture_output=True, text=True, check=True,
                      cwd='/home/pi')
        
        # Compare local HEAD with remote HEAD
        diff_cmd = subprocess.run(['/usr/bin/git', 'rev-list', 'HEAD...origin/' + current_branch, '--count'],
                                capture_output=True, text=True, check=True,
                                cwd='/home/pi')
        commits_behind = int(diff_cmd.stdout.strip())
        
        if commits_behind > 0:
            # Get changed files
            files_cmd = subprocess.run(['/usr/bin/git', 'diff', '--name-only', 'HEAD..origin/' + current_branch],
                                   capture_output=True, text=True, check=True,
                                   cwd='/home/pi')
            changed_files = files_cmd.stdout.strip().split('\n')
            
            return {
                'has_updates': True,
                'branch': current_branch,
                'commits_behind': commits_behind,
                'files': changed_files
            }
        else:
            return {
                'has_updates': False,
                'branch': current_branch,
                'message': 'Your system is up to date!'
            }
            
    except subprocess.CalledProcessError as e:
        raise Exception(f"Git command failed: {e.stderr.strip() if e.stderr else 'No error output'}")
    except Exception as e:
        raise Exception(f"Error checking for updates: {str(e)}")


def merge_configs(user_config: Dict, new_config: Dict) -> Dict:
    """Merge configs: keep user values, add new keys with defaults."""
    if not user_config:
        raise Exception("User configuration is empty - cannot proceed with merge")
    
    if not new_config:
        raise Exception("New configuration is empty - cannot proceed with merge")
    
    result = {}
    
    # For each key in the new config
    for key, new_value in new_config.items():
        if key in user_config:
            # User has this key - keep their value (regardless of whether it was default or custom)
            result[key] = user_config[key]
        else:
            # New key - use new default
            result[key] = new_value
    
    return result


def write_config_file(config_dict: Dict, config_path: str):
    """Write a config dictionary back to a config.py file."""
    try:
        # Read the original file to preserve imports and comments
        with open(config_path, 'r') as f:
            original_content = f.read()
        
        # Parse to get the structure
        tree = ast.parse(original_content)
        
        # Create new content
        new_lines = []
        
        # Add imports first
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    new_lines.append(ast.unparse(node))
                except AttributeError:
                    # Fallback for older Python versions
                    new_lines.append(ast.dump(node))
        
        if new_lines:
            new_lines.append('')  # Add blank line after imports
        
        # Add variables in the order they appear in the new config
        for key, value in config_dict.items():
            if isinstance(value, str) and not value.startswith(('"', "'")):
                # It's a complex expression, write as-is
                new_lines.append(f"{key} = {value}")
            else:
                # It's a simple value, format it properly
                if isinstance(value, str):
                    new_lines.append(f'{key} = "{value}"')
                elif isinstance(value, tuple):
                    new_lines.append(f'{key} = {value}')
                elif isinstance(value, list):
                    new_lines.append(f'{key} = {value}')
                elif isinstance(value, dict):
                    new_lines.append(f'{key} = {value}')
                else:
                    new_lines.append(f'{key} = {value}')
        
        # Write the new config file
        with open(config_path, 'w') as f:
            f.write('\n'.join(new_lines))
            
    except Exception as e:
        print(f"Error writing config file: {e}")
        # Fallback: write simple format
        with open(config_path, 'w') as f:
            f.write('# METARMap Configuration\n\n')
            for key, value in config_dict.items():
                f.write(f'{key} = {repr(value)}\n')


def perform_update() -> Dict:
    """Perform the system update with simplified logic."""
    try:
        print("Starting update process...")
        
        # Get current branch
        branch = subprocess.check_output(['/usr/bin/git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                        text=True, 
                                        cwd='/home/pi').strip()
        print(f"Current branch: {branch}")
        
        # Create backup
        print("Creating backup...")
        backup_dir, files_backed_up = create_backup()
        print(f"Created backup directory: {backup_dir}")
        print(f"Total files backed up: {files_backed_up}")
        
        # Step 1: Capture user's current configuration
        print("Capturing user's current configuration...")
        try:
            user_config = parse_config_file('/home/pi/config.py')
            print(f"Found {len(user_config)} configuration variables")
        except Exception as e:
            raise Exception(f"Failed to parse user config: {e}")
        
        # Backup airports.txt (we'll restore it completely)
        print("Backing up airports.txt...")
        if os.path.exists('/home/pi/airports.txt'):
            subprocess.run(['cp', '/home/pi/airports.txt', '/tmp/airports.txt.backup'], check=True)
        else:
            print("Warning: airports.txt does not exist")
        
        # Step 2: Clean pull from repository
        print("Performing clean pull from repository...")
        
        # Stash any local changes
        try:
            subprocess.run(['/usr/bin/git', 'stash'], check=True, cwd='/home/pi', 
                          capture_output=True, text=True)
            print("Local changes stashed successfully")
        except subprocess.CalledProcessError:
            print("No local changes to stash")
        
        # Clean untracked files
        try:
            subprocess.run(['/usr/bin/git', 'clean', '-fd'], check=True, cwd='/home/pi')
            print("Untracked files cleaned successfully")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Clean failed: {e}")
        
        # Fetch and reset to get new files
        subprocess.run(['/usr/bin/git', 'fetch', 'origin', branch], check=True, cwd='/home/pi')
        subprocess.run(['/usr/bin/git', 'reset', '--hard', f'origin/{branch}'], check=True, cwd='/home/pi')
        print("Repository updated successfully")
        
        # Step 3: Parse the new config
        print("Parsing new configuration...")
        try:
            new_config = parse_config_file('/home/pi/config.py')
            print(f"New config has {len(new_config)} variables")
        except Exception as e:
            raise Exception(f"Failed to parse new config: {e}")
        
        # Step 4: Merge configurations
        print("Merging configurations...")
        try:
            merged_config = merge_configs(user_config, new_config)
            print(f"Merged config has {len(merged_config)} variables")
        except Exception as e:
            raise Exception(f"Failed to merge configs: {e}")
        
        # Step 5: Write the merged config
        print("Writing merged configuration...")
        write_config_file(merged_config, '/home/pi/config.py')
        
        # Step 6: Restore airports.txt completely
        print("Restoring airports.txt...")
        if os.path.exists('/tmp/airports.txt.backup'):
            subprocess.run(['mv', '/tmp/airports.txt.backup', '/home/pi/airports.txt'], check=True)
        else:
            print("Warning: airports.txt backup not found")
        
        # Step 7: Validate the result
        print("Validating final configuration...")
        is_valid, validation_msg = validate_config_file('/home/pi/config.py')
        if not is_valid:
            print(f"Warning: Final config validation failed: {validation_msg}")
            # Try to restore from backup
            if os.path.exists(f'{backup_dir}/config.py'):
                print("Restoring config.py from backup...")
                subprocess.run(['cp', f'{backup_dir}/config.py', '/home/pi/config.py'], check=True)
                print("Config.py restored from backup")
                raise Exception(f"Update failed: {validation_msg}")
        
        # Clean up old backups (keep last 5)
        cleanup_old_backups()
        
        # Set ownership of all files to pi:pi recursively
        print("Setting file ownership...")
        subprocess.run(['chown', '-R', 'pi:pi', '.'], check=True, cwd='/home/pi')
        
        print("Update completed successfully")
        return {
            'success': True,
            'message': f'Update applied successfully. {files_backed_up} files backed up to {backup_dir}. Services will restart momentarily.',
            'backup_dir': backup_dir,
            'files_backed_up': files_backed_up,
            'config_variables_preserved': len(user_config),
            'new_variables_added': len(new_config) - len(user_config)
        }
        
    except Exception as e:
        print(f"Update failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def cleanup_old_backups():
    """Clean up old backups, keeping only the last 5."""
    backup_base = '/home/pi/BACKUP'
    if os.path.exists(backup_base):
        backups = sorted([d for d in os.listdir(backup_base) if os.path.isdir(os.path.join(backup_base, d))])
        print(f"Found {len(backups)} backup directories")
        while len(backups) > 5:
            oldest = os.path.join(backup_base, backups[0])
            print(f"Removing old backup: {oldest}")
            shutil.rmtree(oldest)
            backups.pop(0)


def get_config_validation_status() -> Dict:
    """Get the current validation status of config.py."""
    try:
        is_valid, message = validate_config_file('/home/pi/config.py')
        return {
            'valid': is_valid,
            'message': message,
            'file_size': os.path.getsize('/home/pi/config.py') if os.path.exists('/home/pi/config.py') else 0
        }
    except Exception as e:
        return {
            'valid': False,
            'message': f"Validation error: {str(e)}",
            'file_size': 0
        } 