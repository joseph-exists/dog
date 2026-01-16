# ActionRunJob

ActionRunJob represents a job of a run

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | the action run job id | [optional] 
**name** | **str** | the action run job name | [optional] 
**needs** | **List[str]** | the action run job needed ids | [optional] 
**owner_id** | **int** | the owner id | [optional] 
**repo_id** | **int** | the repository id | [optional] 
**runs_on** | **List[str]** | the action run job labels to run on | [optional] 
**status** | **str** | the action run job status | [optional] 
**task_id** | **int** | the action run job latest task id | [optional] 

## Example

```python
from openapi_client.models.action_run_job import ActionRunJob

# TODO update the JSON string below
json = "{}"
# create an instance of ActionRunJob from a JSON string
action_run_job_instance = ActionRunJob.from_json(json)
# print the JSON string representation of the object
print(ActionRunJob.to_json())

# convert the object into a dict
action_run_job_dict = action_run_job_instance.to_dict()
# create an instance of ActionRunJob from a dict
action_run_job_from_dict = ActionRunJob.from_dict(action_run_job_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


