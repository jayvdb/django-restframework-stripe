from collections import Mapping, Sequence

def recursive_mapping_update(mapping, **updates):
    """ Recursively update a dict-tree without clobbering any of the nested dictionaries.

    :param mapping: a dict-like object to perform updates on
    :type mapping: dict
    :returns: the updated mapping
    """
    for key, value in updates.items():
        if isinstance(value, Mapping) and mapping.get(key):
            mapping[key] = recursive_mapping_update(mapping[key], **value)
        else:
            mapping[key] = value
    return mapping
