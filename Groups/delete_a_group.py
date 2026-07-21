import slumber
import json
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

__friendly_name__ = "Delete a Group"

def delete_a_group(group_id=None):
    """
    Delete a specific group

    Args:
        group_id (str): The ID of the group to delete

    Returns:
        dict: The API response after deletion
    """
    # If group_id wasn't provided as an argument, ask for it
    if group_id is None:
        group_id = input("Enter group ID to delete: ")

    confirmation = input(f"Are you sure you want to delete group {group_id}? (y/n): ").lower()
    if confirmation != 'y':
        print("Deletion cancelled.")
        return None

    try:
        api = slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))
        result = api.groups(group_id).delete()

        print("\nGroup deleted successfully.")
        print(json.dumps(result, indent=4))

        return result

    except Exception as e:
        print('\nDeleteGroup raised an exception:')
        print(str(e))
        return None

if __name__ == "__main__":
    delete_a_group()
