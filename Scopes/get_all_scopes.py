import slumber
import json
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

__friendly_name__ = "Get All Scopes"

def get_all_scopes():
    try:
        api = slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))
        # use $top & $skip parameters
        params = {'top': '50', 'skip': '0'}
        result = api.scopes.get(**params)
        
        print("\nAll scopes:")
        print(json.dumps(result, indent=4))
        
    except Exception as e:
        print('\nGetScopes raised an exception:')
        print(str(e))

if __name__ == "__main__":
    get_all_scopes()
