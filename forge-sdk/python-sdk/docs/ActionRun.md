# ActionRun

ActionRun represents an action run

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**schedule_id** | **int** | the cron id for the schedule trigger | [optional] 
**approved_by** | **int** | who approved this action run | [optional] 
**commit_sha** | **str** | the commit sha the action run ran on | [optional] 
**created** | **datetime** | when the action run was created | [optional] 
**duration** | **int** | A Duration represents the elapsed time between two instants as an int64 nanosecond count. The representation limits the largest representable duration to approximately 290 years. | [optional] 
**event** | **str** | the webhook event that causes the workflow to run | [optional] 
**event_payload** | **str** | the payload of the webhook event that causes the workflow to run | [optional] 
**html_url** | **str** | the url of this action run | [optional] 
**id** | **int** | the action run id | [optional] 
**index_in_repo** | **int** | a unique number for each run of a repository | [optional] 
**is_fork_pull_request** | **bool** | If this is triggered by a PR from a forked repository or an untrusted user, we need to check if it is approved and limit permissions when running the workflow. | [optional] 
**is_ref_deleted** | **bool** | has the commit/tag/… the action run ran on been deleted | [optional] 
**need_approval** | **bool** | may need approval if it&#39;s a fork pull request | [optional] 
**prettyref** | **str** | the commit/tag/… the action run ran on | [optional] 
**repository** | [**Repository**](Repository.md) |  | [optional] 
**started** | **datetime** | when the action run was started | [optional] 
**status** | **str** | the current status of this run | [optional] 
**stopped** | **datetime** | when the action run was stopped | [optional] 
**title** | **str** | the action run&#39;s title | [optional] 
**trigger_event** | **str** | the trigger event defined in the &#x60;on&#x60; configuration of the triggered workflow | [optional] 
**trigger_user** | [**User**](User.md) |  | [optional] 
**updated** | **datetime** | when the action run was last updated | [optional] 
**workflow_id** | **str** | the name of workflow file | [optional] 

## Example

```python
from openapi_client.models.action_run import ActionRun

# TODO update the JSON string below
json = "{}"
# create an instance of ActionRun from a JSON string
action_run_instance = ActionRun.from_json(json)
# print the JSON string representation of the object
print(ActionRun.to_json())

# convert the object into a dict
action_run_dict = action_run_instance.to_dict()
# create an instance of ActionRun from a dict
action_run_from_dict = ActionRun.from_dict(action_run_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


