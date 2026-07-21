import slumber
import json
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

__friendly_name__ = "Delete a Site"

def delete_a_site(site_id=None):
    """
    Delete a specific site

    Args:
        site_id (str): The ID of the site to delete

    Returns:
        dict: The API response after deletion
    """
    # If site_id wasn't provided as an argument, ask for it
    if site_id is None:
        site_id = input("Enter site ID to delete: ")

    confirmation = input(f"Are you sure you want to delete site {site_id}? (y/n): ").lower()
    if confirmation != 'y':
        print("Deletion cancelled.")
        return None

    try:
        api = slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))
        result = api.sites(site_id).delete()

        print("\nSite deleted successfully.")
        print(json.dumps(result, indent=4))

        return result

    except Exception as e:
        print('\nDeleteSite raised an exception:')
        print(str(e))
        return None

if __name__ == "__main__":
    delete_a_site()
