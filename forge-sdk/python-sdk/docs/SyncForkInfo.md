# SyncForkInfo

SyncForkInfo information about syncing a fork

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**allowed** | **bool** |  | [optional] 
**base_commit** | **str** |  | [optional] 
**commits_behind** | **int** |  | [optional] 
**fork_commit** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.sync_fork_info import SyncForkInfo

# TODO update the JSON string below
json = "{}"
# create an instance of SyncForkInfo from a JSON string
sync_fork_info_instance = SyncForkInfo.from_json(json)
# print the JSON string representation of the object
print(SyncForkInfo.to_json())

# convert the object into a dict
sync_fork_info_dict = sync_fork_info_instance.to_dict()
# create an instance of SyncForkInfo from a dict
sync_fork_info_from_dict = SyncForkInfo.from_dict(sync_fork_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


