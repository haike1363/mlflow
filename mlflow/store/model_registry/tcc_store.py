import json
import logging
import os

from tencentcloud.common import credential
from tencentcloud.common.common_client import CommonClient

from mlflow.entities.model_registry import RegisteredModel
from mlflow.exceptions import MlflowException
from mlflow.store.model_registry.abstract_store import AbstractStore
from mlflow.utils.annotations import experimental


def _get_create_time_from_resp(resp):
    return resp["Audit"]["CreatedTime"]


def _get_last_updated_time_from_resp(resp):
    return resp["Audit"]["LastModifiedTime"]


@experimental
class TCCStore(AbstractStore):
    """
    Client for an Open Source Unity Catalog Server accessed via REST API calls.
    """

    def __init__(self, store_uri=None, tracking_uri=None):
        super().__init__(store_uri, tracking_uri)
        ak = os.getenv("TENCENTCLOUD_SECRET_KEY", None)
        if len(ak) == 0:
            raise MlflowException("TENCENTCLOUD_SECRET_KEY is not set")
        sk = os.getenv("TENCENTCLOUD_SECRET_ID", None)
        if len(sk) == 0:
            raise MlflowException("TENCENTCLOUD_SECRET_ID is not set")
        region = os.getenv("TENCENTCLOUD_REGION", None)
        if len(region) == 0:
            raise MlflowException("TENCENTCLOUD_REGION is not set")
        cred = credential.Credential(ak, sk)
        self.client = CommonClient("tccatalog", "2024-10-24", cred, region)
        logging.info("initialized tencent tccatalog client successfully {}".format(region))

    def _call(self, action, req):
        print("req: {}\n{}".format(action, json.dumps(req, indent=2)))
        body = self.client.call(action, req)
        body_obj = json.loads(body)
        print("body: {}\n{}".format(action, json.dumps(body_obj, indent=2)))
        resp = body_obj["Response"]
        return resp

    def create_registered_model(self, name, tags=None, description=None):
        """
        Create a new registered model in backend store.

        Args:
            name: Name of the new model. This is expected to be unique in the backend store.
            tags: Not supported for Unity Catalog OSS yet.
            description: Description of the model.

        Returns:
            A single object of :py:class:`mlflow.entities.model_registry.RegisteredModel`
            created in the backend.

        """
        [catalog_name, schema_name, model_name] = name.split(".")
        comment = description if description else ""
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "Comment": comment
        }
        resp = self._call("RegisterModel", req)
        return RegisteredModel(
            name=resp["Name"],
            creation_timestamp=_get_create_time_from_resp(resp["Audit"]),
            last_updated_timestamp=_get_last_updated_time_from_resp(resp["Audit"]),
            description=resp["Comment"],
        )

    def update_registered_model(self, name, description):
        raise NotImplementedError("Method not implemented")

    def rename_registered_model(self, name, new_name):
        raise NotImplementedError("Method not implemented")

    def delete_registered_model(self, name):
        raise NotImplementedError("Method not implemented")

    def search_registered_models(
            self, filter_string=None, max_results=None, order_by=None, page_token=None
    ):
        raise NotImplementedError("Method not implemented")

    def get_registered_model(self, name):
        raise NotImplementedError("Method not implemented")

    def get_latest_versions(self, name, stages=None):
        raise NotImplementedError("Method not implemented")

    def set_registered_model_tag(self, name, tag):
        raise NotImplementedError("Method not implemented")

    def delete_registered_model_tag(self, name, key):
        raise NotImplementedError("Method not implemented")

    def create_model_version(
            self,
            name,
            source,
            run_id=None,
            tags=None,
            run_link=None,
            description=None,
            local_model_path=None,
    ):
        raise NotImplementedError("Method not implemented")

    def update_model_version(self, name, version, description):
        raise NotImplementedError("Method not implemented")

    def transition_model_version_stage(self, name, version, stage, archive_existing_versions):
        raise NotImplementedError("Method not implemented")

    def delete_model_version(self, name, version):
        raise NotImplementedError("Method not implemented")

    def _get_model_version_endpoint_response(self, name, version):
        raise NotImplementedError("Method not implemented")

    def get_model_version(self, name, version):
        raise NotImplementedError("Method not implemented")

    def search_model_versions(
            self, filter_string=None, max_results=None, order_by=None, page_token=None
    ):
        raise NotImplementedError("Method not implemented")

    def set_model_version_tag(self, name, version, tag):
        raise NotImplementedError("Method not implemented")

    def delete_model_version_tag(self, name, version, key):
        raise NotImplementedError("Method not implemented")

    def set_registered_model_alias(self, name, alias, version):
        raise NotImplementedError("Method not implemented")

    def delete_registered_model_alias(self, name, alias):
        raise NotImplementedError("Method not implemented")

    def get_model_version_by_alias(self, name, alias):
        raise NotImplementedError("Method not implemented")

    def get_model_version_download_uri(self, name, version):
        raise NotImplementedError("Method not implemented")
