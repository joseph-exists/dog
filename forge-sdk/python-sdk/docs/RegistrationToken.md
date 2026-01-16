# RegistrationToken

RegistrationToken is a string used to register a runner with a server

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**token** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.registration_token import RegistrationToken

# TODO update the JSON string below
json = "{}"
# create an instance of RegistrationToken from a JSON string
registration_token_instance = RegistrationToken.from_json(json)
# print the JSON string representation of the object
print(RegistrationToken.to_json())

# convert the object into a dict
registration_token_dict = registration_token_instance.to_dict()
# create an instance of RegistrationToken from a dict
registration_token_from_dict = RegistrationToken.from_dict(registration_token_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


