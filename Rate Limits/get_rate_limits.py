import slumber
import json
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

__friendly_name__ = "Get Rate Limits"

def get_rate_limits():
    try:
        api = slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))
        result = api.ratelimits.get()

        print("\nRate limits:")
        print(json.dumps(result, indent=4))

    except Exception as e:
        print('\nGetRateLimits raised an exception:')
        print(str(e))

if __name__ == "__main__":
    get_rate_limits()
