import os
from storages.backends.azure_storage import AzureStorage

class AzureMediaStorage(AzureStorage):
    account_name = os.getenv("AZURE_ACCOUNT_NAME", "").strip()
    account_key = os.getenv("AZURE_ACCOUNT_KEY", "").strip()
    azure_container = os.getenv("AZURE_CONTAINER", "media").strip()

    custom_domain = f"{account_name}.blob.core.windows.net" if account_name else None

    overwrite_files = False
    expiration_secs = None  # public link
