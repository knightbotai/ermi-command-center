import re

with open('ermi/api.py', 'r') as f:
    content = f.read()

# Add validation to watcher
duplicate_pattern2 = re.compile(
    r'        from ermi\.setup import load_setup\n\n'
    r'        allowed_dirs = \[root\.resolve\(\)\]\n'
    r'        setup_config = load_setup\(root\)\n'
    r'        if setup_config\.get\("chatgpt_source"\):\n'
    r'            allowed_dirs\.append\(\n'
    r'                Path\(setup_config\["chatgpt_source"\]\)\.expanduser\(\)\.resolve\(\)\.parent\n'
    r'            \)\n'
    r'        if setup_config\.get\("chatlasso_source"\):\n'
    r'            allowed_dirs\.append\(\n'
    r'                Path\(setup_config\["chatlasso_source"\]\)\.expanduser\(\)\.resolve\(\)\n'
    r'            \)\n\n'
    r'        if not any\(source\.is_relative_to\(d\) for d in allowed_dirs\):\n'
    r'            raise HTTPException\(\n'
    r'                status_code=403,\n'
    r'                detail="Source path is not within an allowed directory\.",\n'
    r'            \)\n', re.MULTILINE
)
content = duplicate_pattern2.sub('        validate_allowed_path(source, root)\n', content)


with open('ermi/api.py', 'w') as f:
    f.write(content)
