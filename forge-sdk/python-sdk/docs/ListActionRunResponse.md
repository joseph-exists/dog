# ListActionRunResponse

ListActionRunResponse return a list of ActionRun

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_count** | **int** |  | [optional] 
**workflow_runs** | [**List[ActionRun]**](ActionRun.md) |  | [optional] 

## Example

```python
from openapi_client.models.list_action_run_response import ListActionRunResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ListActionRunResponse from a JSON string
list_action_run_response_instance = ListActionRunResponse.from_json(json)
# print the JSON string representation of the object
print(ListActionRunResponse.to_json())

# convert the object into a dict
list_action_run_response_dict = list_action_run_response_instance.to_dict()
# create an instance of ListActionRunResponse from a dict
list_action_run_response_from_dict = ListActionRunResponse.from_dict(list_action_run_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


