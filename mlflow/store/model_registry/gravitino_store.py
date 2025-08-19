import json
import uuid

import requests

from mlflow.entities.model_registry import RegisteredModel, ModelVersion
from mlflow.exceptions import MlflowException
from mlflow.store.model_registry.abstract_store import AbstractStore
from mlflow.utils.annotations import experimental


def _get_create_time_from_entity(obj):
    return obj["audit"]["createTime"]


def _get_last_updated_time_from_entity(obj):
    if "lastModifiedTime" in obj["audit"]:
        return obj["audit"]["lastModifiedTime"]
    return _get_create_time_from_entity(obj)


def to_string(obj):
    if obj is None:
        return "None"
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return json.dumps(obj, indent=2)
    if isinstance(obj, requests.Response):
        return obj.text
    try:
        return json.dumps(obj, indent=2)
    except:
        return str(obj)


def log_msg(msg):
    print(msg)


def _get(url, params=None):
    log_msg("get: {}\n{}".format(url, to_string(params)))
    resp = requests.get(url, params)
    log_msg("resp: {}\n{}".format(url, to_string(resp)))
    if resp.status_code != 200:
        raise MlflowException("request failed: {}".format(resp.text))
    body_obj = resp.json()
    return body_obj


def _post(url, body=None, params=None):
    log_msg("post: {}\nparams: {}\nbody: {}".format(url, to_string(params), to_string(body)))
    resp = requests.post(url=url, params=params, json=body)
    log_msg("resp: {}\n{}".format(url, to_string(resp)))

    if resp.status_code != 200:
        raise MlflowException("request failed: {}".format(resp.text))
    body_obj = resp.json()
    if body_obj["code"] != 0:
        raise MlflowException("request failed: {}".format(to_string(body_obj)))
    return body_obj


def _get_tags_from_properties(properties):
    return json.loads(properties["tags"]) if "tags" in properties else None


def _set_tags_to_properties(properties, tags):
    if tags:
        properties["tags"] = json.dumps(tags)
    return properties


def _make_model(resp):
    model = resp["model"]
    properties = model["properties"]
    return RegisteredModel(
        name=model["name"],
        creation_timestamp=_get_create_time_from_entity(model),
        last_updated_timestamp=_get_last_updated_time_from_entity(model),
        description=model["comment"],
        tags=_get_tags_from_properties(properties),
    )


def _make_model_version(resp, name):
    model_version = resp["modelVersion"]
    properties = model_version["properties"]
    return ModelVersion(
        name=name,
        version=model_version["version"],
        creation_timestamp=_get_create_time_from_entity(model_version),
        last_updated_timestamp=_get_last_updated_time_from_entity(model_version),
        description=model_version["comment"],
        source=model_version["uri"],
        run_id=properties["run_id"] if "run_id" in properties else None,
        tags=_get_tags_from_properties(properties),
        run_link=properties["run_link"] if "run_link" in properties else None,
        status="READY",
    )


@experimental
class GravitinoStore(AbstractStore):
    """
    Client for an Open Source Unity Catalog Server accessed via REST API calls.
    """

    def __init__(self, store_uri=None, tracking_uri=None):
        super().__init__(store_uri, tracking_uri)
        if not store_uri.startswith("gravitino:"):
            raise MlflowException("set store_uri gravitino:http://localhost:8090/api/metalakes/example")
        gravitino_url = store_uri[len("gravitino:"):]
        print("gravitino_url: {}".format(gravitino_url))
        self.endpoint = gravitino_url

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
        log_msg("create_registered_model {} {} {}".format(name, tags, description))
        [catalog_name, schema_name, model_name] = name.split(".")
        req_body = {
            "name": model_name,
            "comment": description if description else "",
            "properties": {}
        }
        _set_tags_to_properties(req_body["properties"], tags)
        # http://localhost:8090/api/metalakes/example/catalogs/model_catalog/schemas/model_schema/models
        url = "{}/catalogs/{}/schemas/{}/models".format(self.endpoint, catalog_name, schema_name)
        resp = _post(url, req_body)
        return _make_model(resp)

    def update_registered_model(self, name, description):
        log_msg("update_registered_model {} {}".format(name, description))
        raise NotImplementedError("Method not implemented")

    def rename_registered_model(self, name, new_name):
        log_msg("rename_registered_model {} {}".format(name, new_name))
        raise NotImplementedError("Method not implemented")

    def delete_registered_model(self, name):
        log_msg("delete_registered_model {}".format(name))
        raise NotImplementedError("Method not implemented")

    def search_registered_models(
            self, filter_string=None, max_results=None, order_by=None, page_token=None
    ):
        log_msg("search_registered_models {} {} {} {}".format(filter_string, max_results, order_by, page_token))
        raise NotImplementedError("Method not implemented")

    def get_registered_model(self, name):
        log_msg("get_registered_model {}".format(name))
        [catalog_name, schema_name, model_name] = name.split(".")
        # http://localhost:8090/api/metalakes/example/catalogs/model_catalog/schemas/model_schema/models/example_model
        url = "{}/catalogs/{}/schemas/{}/models/{}".format(self.endpoint, catalog_name, schema_name, model_name)
        resp = _get(url)
        return _make_model(resp)

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
        log_msg("create_model_version {} {} {} {} {} {} {}".format(name, source, run_id, tags, run_link, description,
                                                                   local_model_path))
        [catalog_name, schema_name, model_name] = name.split(".")
        version_alias = str(uuid.uuid4())
        req_body = {
            "uri": source,
            "comment": description if description else "",
            "properties": {},
            "aliases": [version_alias]
        }
        _set_tags_to_properties(req_body["properties"], tags)
        if run_id:
            req_body["properties"]["run_id"] = run_id
        if run_link:
            req_body["properties"]["run_link"] = run_link
        # http://localhost:8090/api/metalakes/example/catalogs/model_catalog/schemas/model_schema/models/example_model/versions
        url = "{}/catalogs/{}/schemas/{}/models/{}/versions".format(
            self.endpoint, catalog_name, schema_name, model_name)
        _post(url, req_body)
        # http://localhost:8090/api/metalakes/example/catalogs/model_catalog/schemas/model_schema/models/example_model/aliases/alias1
        url = "{}/catalogs/{}/schemas/{}/models/{}/aliases/{}".format(
            self.endpoint, catalog_name, schema_name, model_name, version_alias)
        resp = _get(url)
        return _make_model_version(resp, name)

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
