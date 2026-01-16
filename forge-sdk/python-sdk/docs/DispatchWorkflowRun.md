# DispatchWorkflowRun

DispatchWorkflowRun represents a workflow run

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | the workflow run id | [optional] 
**jobs** | **List[str]** | the jobs name | [optional] 
**run_number** | **int** | a unique number for each run of a repository | [optional] 

## Example

```python
from openapi_client.models.dispatch_workflow_run import DispatchWorkflowRun

# TODO update the JSON string below
json = "{}"
# create an instance of DispatchWorkflowRun from a JSON string
dispatch_workflow_run_instance = DispatchWorkflowRun.from_json(json)
# print the JSON string representation of the object
print(DispatchWorkflowRun.to_json())

# convert the object into a dict
dispatch_workflow_run_dict = dispatch_workflow_run_instance.to_dict()
# create an instance of DispatchWorkflowRun from a dict
dispatch_workflow_run_from_dict = DispatchWorkflowRun.from_dict(dispatch_workflow_run_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


