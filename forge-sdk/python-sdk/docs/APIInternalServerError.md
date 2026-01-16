# APIInternalServerError


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** |  | [optional] 
**url** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.api_internal_server_error import APIInternalServerError

# TODO update the JSON string below
json = "{}"
# create an instance of APIInternalServerError from a JSON string
api_internal_server_error_instance = APIInternalServerError.from_json(json)
# print the JSON string representation of the object
print(APIInternalServerError.to_json())

# convert the object into a dict
api_internal_server_error_dict = api_internal_server_error_instance.to_dict()
# create an instance of APIInternalServerError from a dict
api_internal_server_error_from_dict = APIInternalServerError.from_dict(api_internal_server_error_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


