import slumber
import json
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

__friendly_name__ = "Delete an Organisation"

def delete_an_organisation(organisation_id=None):
    """
    Delete a specific organisation

    Args:
        organisation_id (str): The ID of the organisation to delete

    Returns:
        dict: The API response after deletion
    """
    # If organisation_id wasn't provided as an argument, ask for it
    if organisation_id is None:
        organisation_id = input("Enter organisation ID to delete: ")

    confirmation = input(f"Are you sure you want to delete organisation {organisation_id}? (y/n): ").lower()
    if confirmation != 'y':
        print("Deletion cancelled.")
        return None

    try:
        api = slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))
        result = api.organizations(organisation_id).delete()

        print("\nOrganisation deleted successfully.")
        print(json.dumps(result, indent=4))

        return result

    except Exception as e:
        print('\nDeleteOrganization raised an exception:')
        print(str(e))
        return None

if __name__ == "__main__":
    delete_an_organisation()
