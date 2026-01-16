# APPersonFollowItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**actor_id** | **str** |  | [optional] 
**note** | **str** |  | [optional] 
**original_item** | **str** |  | [optional] 
**original_url** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.ap_person_follow_item import APPersonFollowItem

# TODO update the JSON string below
json = "{}"
# create an instance of APPersonFollowItem from a JSON string
ap_person_follow_item_instance = APPersonFollowItem.from_json(json)
# print the JSON string representation of the object
print(APPersonFollowItem.to_json())

# convert the object into a dict
ap_person_follow_item_dict = ap_person_follow_item_instance.to_dict()
# create an instance of APPersonFollowItem from a dict
ap_person_follow_item_from_dict = APPersonFollowItem.from_dict(ap_person_follow_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


