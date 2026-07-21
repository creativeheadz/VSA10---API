import slumber
import json
import sys
import os

__friendly_name__ = "Cancel a Workflow Execution"

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def cancel_workflow_execution(execution_id=None):
    # If execution_id wasn't provided as an argument, ask for it
    if execution_id is None:
        while True:
            try:
                execution_id = int(input("Enter workflow execution ID to cancel: "))
                break
            except ValueError:
                print("Please enter a valid integer for the execution ID.")

    confirmation = input(f"Are you sure you want to cancel workflow execution {execution_id}? (y/n): ").lower()
    if confirmation != 'y':
        print("Cancellation aborted.")
        return None

    try:
        api = slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))
        result = api.automation.workflows.executions(str(execution_id)).cancel.put({})

        print("\nWorkflow execution cancelled successfully:")
        print(json.dumps(result, indent=4))

        return result

    except Exception as e:
        print('\nCancelWorkflowExecution raised an exception:')
        print(str(e))
        return None

if __name__ == "__main__":
    cancel_workflow_execution()
