# TopicSearchResults


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**topics** | [**List[TopicResponse]**](TopicResponse.md) |  | [optional] 

## Example

```python
from openapi_client.models.topic_search_results import TopicSearchResults

# TODO update the JSON string below
json = "{}"
# create an instance of TopicSearchResults from a JSON string
topic_search_results_instance = TopicSearchResults.from_json(json)
# print the JSON string representation of the object
print(TopicSearchResults.to_json())

# convert the object into a dict
topic_search_results_dict = topic_search_results_instance.to_dict()
# create an instance of TopicSearchResults from a dict
topic_search_results_from_dict = TopicSearchResults.from_dict(topic_search_results_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


