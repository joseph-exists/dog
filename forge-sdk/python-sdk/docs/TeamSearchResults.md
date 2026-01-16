# TeamSearchResults


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**List[Team]**](Team.md) |  | [optional] 
**ok** | **bool** |  | [optional] 

## Example

```python
from openapi_client.models.team_search_results import TeamSearchResults

# TODO update the JSON string below
json = "{}"
# create an instance of TeamSearchResults from a JSON string
team_search_results_instance = TeamSearchResults.from_json(json)
# print the JSON string representation of the object
print(TeamSearchResults.to_json())

# convert the object into a dict
team_search_results_dict = team_search_results_instance.to_dict()
# create an instance of TeamSearchResults from a dict
team_search_results_from_dict = TeamSearchResults.from_dict(team_search_results_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


