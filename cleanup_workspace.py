import os
import shutil
import glob
from pathlib import Path

def clean_workspace():
    """Remove all unneeded temporary files and data outside /data and /restoration folders"""
    
    # Define folders to keep
    folders_to_keep = {
        'data', 'restoration', '.github', '.venv', '.vscode', 
        'analysis', 'notebooks', 'scrapers'
    }
    
    # Define essential files to keep
    essential_files = {
        'README.md', 'requirements.txt', 'codes.csv',
        'website_analyzer.py', 'clean_finale_data.py', 'update_seven_percent_field.py'
    }
    
    # Files and patterns to remove
    files_to_remove = []
    
    print("=== CLEANING WORKSPACE ===")
    
    # Get all files in root directory
    for item in os.listdir('.'):
        if os.path.isfile(item):
            # Keep essential files
            if item in essential_files:
                continue
            
            # Remove temporary and data files
            if any(item.startswith(prefix) for prefix in [
                'combo_', 'debug_', 'finale', 'flow_', 'investigation_',
                'playwright_', 'requests_', 'selenium_', 'results_',
                'tunisia_university_', 'test_', 'phase1_', 'phase2_'
            ]):
                files_to_remove.append(item)
            
            # Remove files with specific extensions or patterns
            elif any(item.endswith(ext) for ext in [
                '.json', '.csv', '.png', '.html', '.js', '.txt', '.log'
            ]) and item not in essential_files:
                files_to_remove.append(item)
            
            # Remove Python scripts that are no longer needed
            elif item.endswith('.py') and item not in essential_files:
                # Keep only essential scripts
                if not any(keep in item for keep in [
                    'analyzer', 'clean_finale', 'update_seven_percent'
                ]):
                    files_to_remove.append(item)
    
    # Show what will be removed
    print(f"Files to remove ({len(files_to_remove)}):")
    for i, file in enumerate(sorted(files_to_remove)[:20]):  # Show first 20
        print(f"  {i+1:2d}. {file}")
    if len(files_to_remove) > 20:
        print(f"  ... and {len(files_to_remove) - 20} more files")
    
    # Confirm removal
    print(f"\nFolders to keep: {sorted(folders_to_keep)}")
    print(f"Essential files to keep: {sorted(essential_files)}")
    
    confirmation = input(f"\nRemove {len(files_to_remove)} files? (y/N): ")
    
    if confirmation.lower() == 'y':
        # Remove files
        removed_count = 0
        for file in files_to_remove:
            try:
                os.remove(file)
                removed_count += 1
                if removed_count <= 10:  # Show first 10 removals
                    print(f"  ✅ Removed: {file}")
                elif removed_count == 11:
                    print(f"  ... removing remaining files ...")
            except Exception as e:
                print(f"  ❌ Error removing {file}: {e}")
        
        print(f"\n✅ Successfully removed {removed_count} files")
        
        # Show final workspace structure
        print(f"\n=== FINAL WORKSPACE STRUCTURE ===")
        remaining_items = []
        for item in sorted(os.listdir('.')):
            if os.path.isdir(item):
                remaining_items.append(f"{item}/")
            else:
                remaining_items.append(item)
        
        for item in remaining_items:
            print(f"  {item}")
        
        # Show data folder contents
        print(f"\n=== DATA FOLDER CONTENTS ===")
        try:
            for item in sorted(os.listdir('data')):
                size = os.path.getsize(f'data/{item}') / 1024  # KB
                print(f"  {item} ({size:.0f} KB)")
        except:
            print("  No data folder found")
    else:
        print("❌ Cleanup cancelled")

if __name__ == "__main__":
    # Change to the workspace directory
    os.chdir(r'c:\Users\ouede\ba')
    clean_workspace()
