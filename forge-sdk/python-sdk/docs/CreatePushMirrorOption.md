# CreatePushMirrorOption


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**branch_filter** | **str** |  | [optional] 
**interval** | **str** |  | [optional] 
**remote_address** | **str** |  | [optional] 
**remote_password** | **str** |  | [optional] 
**remote_username** | **str** |  | [optional] 
**sync_on_commit** | **bool** |  | [optional] 
**use_ssh** | **bool** |  | [optional] 

## Example

```python
from openapi_client.models.create_push_mirror_option import CreatePushMirrorOption

# TODO update the JSON string below
json = "{}"
# create an instance of CreatePushMirrorOption from a JSON string
create_push_mirror_option_instance = CreatePushMirrorOption.from_json(json)
# print the JSON string representation of the object
print(CreatePushMirrorOption.to_json())

# convert the object into a dict
create_push_mirror_option_dict = create_push_mirror_option_instance.to_dict()
# create an instance of CreatePushMirrorOption from a dict
create_push_mirror_option_from_dict = CreatePushMirrorOption.from_dict(create_push_mirror_option_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


