from uuid import uuid4

# if/when this works, we'll migrate this to the startup script
# then add it to 

# Load at module import (startup-safe)
SYSTEM_TYPES: dict[str, uuid4] = {
    'TYPE1':'673f1787-8474-4e1c-986c-8e19f14c989c',  # From provider_type.id WHERE name='Type1'
    'TYPE2':'008dc763-4309-43cd-ba5f-1eb1323a0964',
    'TYPE3':'e09ade10-8563-4748-8deb-1a6c87c97134',
    'TYPE4':'186672e2-f50a-4457-a7dd-a50084077ff7',
    'TYPE5':'ae07eb0b-929e-4844-8b75-4fe6abca09df',
# ... populate via script or manual from `provider_type` where is_system=True
}


# TYPE1 - openai
# TYPE2 - anthropic
# TYPE3 - openai_compatible
# TYPE4 - custom
# TYPE5 - google

# # Module-level constants for direct imports
TYPE1 = SYSTEM_TYPES['TYPE1']
TYPE2 = SYSTEM_TYPES['TYPE2']
TYPE3 = SYSTEM_TYPES['TYPE3']
TYPE4 = SYSTEM_TYPES['TYPE4']
TYPE5 = SYSTEM_TYPES['TYPE5']

# Optional: UUID → friendly name map for docs/forms
TYPE_MAP: dict[uuid4, str] = {v: k for k, v in SYSTEM_TYPES.items()}
