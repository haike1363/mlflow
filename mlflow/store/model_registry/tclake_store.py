import json
import os
import uuid

from tencentcloud.common import credential
from tencentcloud.common.common_client import CommonClient

from mlflow.entities.model_registry import RegisteredModel, ModelVersion
from mlflow.exceptions import MlflowException
from mlflow.store.model_registry.abstract_store import AbstractStore
from mlflow.utils.annotations import experimental


def gen_uuid():
    return str(uuid.uuid4())


def to_string(obj):
    if obj is None:
        return "None"
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return json.dumps(obj, indent=2)
    try:
        return json.dumps(obj, indent=2)
    except:
        return str(obj)


def log_msg(msg):
    print(msg)


def _get_create_time_from_audit(audit):
    return audit["CreatedTime"]


def _get_last_updated_time_from_audit(audit):
    return audit["LastModifiedTime"]


def _get_tags_from_properties(properties):
    if properties is None or len(properties) == 0:
        return None
    for p in properties:
        if p["Key"] == "tags":
            return json.loads(p["Value"])
    return None


def _add_kv_to_properties(properties, key, value):
    if value is not None:
        properties.append({"Key": key, "Value": value})
    return properties


def _set_uuid_to_properties(properties, uuid_str):
    return _add_kv_to_properties(properties, "mlflow.uuid", uuid_str)


def _get_uuid_from_properties(properties):
    if properties is None or len(properties) == 0:
        return None
    for p in properties:
        if p["Key"] == "mlflow.uuid":
            return p["Value"]
    return None


def _set_tags_to_properties(properties, tags):
    if tags:
        _add_kv_to_properties(properties, "tags", json.dumps(tags))
    return properties


def _make_model(resp):
    properties = resp["Properties"]
    audit = resp["Audit"]
    return RegisteredModel(
        name=resp["Name"],
        creation_timestamp=_get_create_time_from_audit(audit),
        last_updated_timestamp=_get_last_updated_time_from_audit(audit),
        description=resp["Comment"],
        tags=_get_tags_from_properties(properties),
    )


def _make_model_version(entity, name):
    properties = entity["Properties"]
    audit = entity["Audit"]
    return ModelVersion(
        name=name,
        version=entity["Version"],
        creation_timestamp=_get_create_time_from_audit(audit),
        last_updated_timestamp=_get_last_updated_time_from_audit(audit),
        description=entity["Comment"],
        source=entity["Uri"],
        run_id=properties["run_id"] if "run_id" in properties else None,
        tags=_get_tags_from_properties(properties),
        run_link=properties["run_link"] if "run_link" in properties else None,
        status="READY",
    )


@experimental
class TCLakeStore(AbstractStore):
    """
    Client for an Open Source Unity Catalog Server accessed via REST API calls.
    """

    def __init__(self, store_uri=None, tracking_uri=None):
        super().__init__(store_uri, tracking_uri)
        log_msg("initializing tencent tclake client {} {}".format(store_uri, tracking_uri))
        sid = os.getenv("TENCENTCLOUD_SECRET_ID", "")
        if len(sid) == 0:
            raise MlflowException("TENCENTCLOUD_SECRET_ID is not set")
        sk = os.getenv("TENCENTCLOUD_SECRET_KEY", "")
        if len(sk) == 0:
            raise MlflowException("TENCENTCLOUD_SECRET_ID is not set")
        parts = store_uri.split(":")
        if len(parts) < 2:
            raise MlflowException("set store_uri tclake:{region}")
        region = parts[1]
        cred = credential.Credential(sid, sk)
        self.client = CommonClient("tccatalog", "2024-10-24", cred, region)
        log_msg("initialized tencent tclake client successfully {}".format(region))

    def _call(self, action, req):
        log_msg("req: {}\n{}".format(action, json.dumps(req, indent=2)))
        body = self.client.call(action, req)
        body_obj = json.loads(body)
        log_msg("body: {}\n{}".format(action, json.dumps(body_obj, indent=2)))
        resp = body_obj["Response"]
        return resp

    def create_registered_model(self, name, tags=None, description=None):
        log_msg("create_registered_model {} {} {}".format(name, tags, description))
        [catalog_name, schema_name, model_name] = name.split(".")
        properties = []
        _set_uuid_to_properties(properties, gen_uuid())
        _set_tags_to_properties(properties, tags)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "Comment": description if description else "",
            "Properties": properties
        }
        resp = self._call("RegisterModel", req_body)
        return _make_model(resp["Model"])

    def update_registered_model(self, name, description):
        log_msg("update_register_model {} {}".format(name, description))
        [catalog_name, schema_name, model_name] = name.split(".")
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "NewComment": description if description else ""
        }
        resp = self._call("ModifyModelComment", req_body)
        return _make_model(resp["Model"])

    def rename_registered_model(self, name, new_name):
        raise NotImplementedError("Method not implemented")

    def delete_registered_model(self, name):
        log_msg("delete_register_model {}".format(name))
        [catalog_name, schema_name, model_name] = name.split(".")
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
        }
        resp = self._call("DropModel", req_body)
        if not resp["Dropped"]:
            raise MlflowException("Failed to delete model {}".format(name))

    def search_registered_models(
            self, filter_string=None, max_results=None, order_by=None, page_token=None
    ):
        log_msg("search_registered_models {} {} {} {}".format(
            filter_string, max_results, order_by, page_token))
        # TODO
        raise NotImplementedError("Method not implemented")

    def get_registered_model(self, name):
        log_msg("get_registered_model {}".format(name))
        [catalog_name, schema_name, model_name] = name.split(".")
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
        }
        resp = self._call("DescribeModel", req)
        return _make_model(resp["Model"])

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
        log_msg("create_model_version {} {} {} {} {} {} {}".format(
            name, source, run_id, tags, run_link, description, local_model_path))
        [catalog_name, schema_name, model_name] = name.split(".")
        version_alias = str(uuid.uuid4())
        properties = []
        _set_uuid_to_properties(properties, gen_uuid())
        _set_tags_to_properties(properties, tags)
        _add_kv_to_properties(properties, "run_id", run_id)
        _add_kv_to_properties(properties, "run_link", run_link)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "Uri": source,
            "Comment": description if description else "",
            "Properties": properties,
            "Aliases": [version_alias]
        }
        self._call("CreateModelVersion", req_body)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
        }
        resp = self._call("DescribeModelVersions", req_body)
        model_version = None
        for mv in resp["ModelVersions"]:
            if version_alias in mv["Aliases"]:
                model_version = mv
                break
        return _make_model_version(model_version, name)

    def update_model_version(self, name, version, description):
        log_msg("update_model_version {} {} {}".format(name, version, description))
        [catalog_name, schema_name, model_name] = name.split(".")
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": version,
            "NewComment": description if description else ""
        }
        resp = self._call("ModifyModelVersionComment", req_body)
        return _make_model_version(resp["ModelVersion"], name)

    def transition_model_version_stage(self, name, version, stage, archive_existing_versions):
        raise NotImplementedError("Method not implemented")

    def delete_model_version(self, name, version):
        log_msg("delete_model_version {} {}".format(name, version))
        [catalog_name, schema_name, model_name] = name.split(".")
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": version,
        }
        resp = self._call("DropModelVersion", req_body)
        if not resp["Dropped"]:
            raise Exception("Failed to delete model version {} {}".format(name, version))

    def get_model_version(self, name, version):
        log_msg("get_model_version {} {}".format(name, version))
        [catalog_name, schema_name, model_name] = name.split(".")
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": version,
        }
        resp = self._call("DescribeModelVersion", req_body)
        return _make_model_version(resp["ModelVersion"], name)

    def search_model_versions(
            self, filter_string=None, max_results=None, order_by=None, page_token=None
    ):
        log_msg("search_model_versions {} {} {} {}".format(
            filter_string, max_results, order_by, page_token))
        # TODO
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
        log_msg("get_model_version_download_uri {} {}".format(name, version))
        model_version = self.get_model_version(name, version)
        return model_version.source
