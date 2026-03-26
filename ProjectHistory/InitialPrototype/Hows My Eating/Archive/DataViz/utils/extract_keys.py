def extract_keys(data):
    unique_keys = set()

    def recursive_keys(d, parent_key=''):
        for key, value in d.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            unique_keys.add(full_key)
            if isinstance(value, dict):
                recursive_keys(value, full_key)
    
    for entry in data:
        recursive_keys(entry)
    
    return unique_keys