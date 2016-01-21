from collections import Mapping, Sequence

def recursive_mapping_update(mapping, **updates):
    """
    """
    for key, value in updates.items():
        if isinstance(value, Mapping) and mapping.get(key):
            mapping[key] = recursive_mapping_update(mapping[key], **value)
        else:
            mapping[key] = value
    return mapping
