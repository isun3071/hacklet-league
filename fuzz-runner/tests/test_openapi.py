"""OpenAPI/Swagger spec parsing — pure, no network. Locks the surface a JSON API exposes so the
declarative fan-out and injection probes get correct paths/params/body fields."""
from hacklet_runner.openapi import parse_endpoints


def _by_key(eps, path, method):
    return next(e for e in eps if e.path == path and e.method == method)


def test_openapi3_paths_params_body_and_servers():
    spec = {
        "openapi": "3.0.0",
        "servers": [{"url": "https://api.example.com/v2"}],
        "paths": {
            "/users": {
                "get": {"parameters": [{"in": "query", "name": "search"}]},
                "post": {"requestBody": {"content": {"application/json": {
                    "schema": {"properties": {"username": {}, "password": {}}}}}}},
            },
            "/users/{id}": {
                "parameters": [{"in": "path", "name": "id"}],
                "get": {},
            },
        },
    }
    eps = parse_endpoints(spec)
    # servers[].url path component is prepended as a base path
    get_users = _by_key(eps, "/v2/users", "get")
    assert get_users.query_params == ["search"]
    post_users = _by_key(eps, "/v2/users", "post")
    assert post_users.body_fields == ["username", "password"]
    # path-level param applies to the operation; {id} is concretized for fetches, template kept
    get_user = _by_key(eps, "/v2/users/1", "get")
    assert get_user.path_params == ["id"]
    assert get_user.raw_path == "/v2/users/{id}"


def test_swagger2_basepath_body_and_formdata():
    spec = {
        "swagger": "2.0",
        "basePath": "/api",
        "paths": {
            "/login": {"post": {"parameters": [
                {"in": "body", "name": "creds", "schema": {"properties": {"user": {}, "pass": {}}}},
            ]}},
            "/upload": {"post": {"parameters": [{"in": "formData", "name": "file"}]}},
        },
    }
    eps = parse_endpoints(spec)
    assert _by_key(eps, "/api/login", "post").body_fields == ["user", "pass"]
    assert _by_key(eps, "/api/upload", "post").body_fields == ["file"]


def test_malformed_specs_do_not_raise():
    assert parse_endpoints({}) == []
    assert parse_endpoints({"paths": None}) == []
    # junk operations / params are skipped, not crashed on
    weird = {"paths": {"/x": {"get": {"parameters": ["notadict", {"no": "name"}]}}, "/y": "nope"}}
    eps = parse_endpoints(weird)
    assert _by_key(eps, "/x", "get").query_params == []
