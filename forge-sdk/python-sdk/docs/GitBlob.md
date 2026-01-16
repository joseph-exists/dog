# GitBlob

GitBlob represents a git blob

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**content** | **str** |  | [optional] 
**encoding** | **str** |  | [optional] 
**sha** | **str** |  | [optional] 
**size** | **int** |  | [optional] 
**url** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.git_blob import GitBlob

# TODO update the JSON string below
json = "{}"
# create an instance of GitBlob from a JSON string
git_blob_instance = GitBlob.from_json(json)
# print the JSON string representation of the object
print(GitBlob.to_json())

# convert the object into a dict
git_blob_dict = git_blob_instance.to_dict()
# create an instance of GitBlob from a dict
git_blob_from_dict = GitBlob.from_dict(git_blob_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


