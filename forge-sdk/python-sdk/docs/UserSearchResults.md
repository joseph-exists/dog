# UserSearchResults


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**List[User]**](User.md) |  | [optional] 
**ok** | **bool** |  | [optional] 

## Example

```python
from openapi_client.models.user_search_results import UserSearchResults

# TODO update the JSON string below
json = "{}"
# create an instance of UserSearchResults from a JSON string
user_search_results_instance = UserSearchResults.from_json(json)
# print the JSON string representation of the object
print(UserSearchResults.to_json())

# convert the object into a dict
user_search_results_dict = user_search_results_instance.to_dict()
# create an instance of UserSearchResults from a dict
user_search_results_from_dict = UserSearchResults.from_dict(user_search_results_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


