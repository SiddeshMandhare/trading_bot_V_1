# fix_all_indentation.py
import os

def fix_indentation(file_path):
    """Convert all tabs to 4 spaces in a Python file"""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track if we made changes
    changed = False
    fixed_lines = []
    
    for i, line in enumerate(lines, 1):
        original = line
        # Replace tabs with 4 spaces
        new_line = line.replace('\t', '    ')
        
        if new_line != original:
            changed = True
            print(f"Line {i}: Fixed indentation")
        
        fixed_lines.append(new_line)
    
    if not changed:
        print("✅ No indentation issues found!")
        return True
    
    # Create backup
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"📦 Backup created: {backup_path}")
    
    # Write fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ Fixed indentation in {file_path}")
    return True

if __name__ == "__main__":
    # Fix the main file
    fix_indentation("Dhan_Tradehull_V3.py")
    
    # Also check other files
    other_files = ["auth_service.py", "main.py", "trade_execution.py", "config.py"]
    for f in other_files:
        if os.path.exists(f):
            fix_indentation(f)
    
    print("\n" + "="*50)
    print("✅ All files fixed! Run main.py again.")
    print("="*50)
