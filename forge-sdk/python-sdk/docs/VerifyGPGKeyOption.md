# VerifyGPGKeyOption

VerifyGPGKeyOption options verifies user GPG key

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**armored_signature** | **str** |  | [optional] 
**key_id** | **str** | An Signature for a GPG key token | 

## Example

```python
from openapi_client.models.verify_gpg_key_option import VerifyGPGKeyOption

# TODO update the JSON string below
json = "{}"
# create an instance of VerifyGPGKeyOption from a JSON string
verify_gpg_key_option_instance = VerifyGPGKeyOption.from_json(json)
# print the JSON string representation of the object
print(VerifyGPGKeyOption.to_json())

# convert the object into a dict
verify_gpg_key_option_dict = verify_gpg_key_option_instance.to_dict()
# create an instance of VerifyGPGKeyOption from a dict
verify_gpg_key_option_from_dict = VerifyGPGKeyOption.from_dict(verify_gpg_key_option_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


