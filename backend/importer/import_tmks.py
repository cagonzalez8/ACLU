#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2017
#
# Distributed under terms of the MIT license.

import click
import datetime
import json
import logging
import logging.config
import os
import requests
import sys
import uuid


logging.config.fileConfig(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logging.conf'))
logger = logging.getLogger("aclu_importer.tmk")


API_BASE_URL = "http://localhost:50050"
API_BASE_URL_FORMAT = "{0}/{{0}}".format(API_BASE_URL)


@click.command()
@click.option('--tmk_feature_collection_path', default=None, help='Path to tmk feature collection file being imported.')
def import_tmk(tmk_feature_collection_path):
    if tmk_feature_collection_path and os.path.isfile(os.path.realpath(tmk_feature_collection_path)):
        organization = _get_organization("Park")

        if organization:
            for feature in _features_from_path(os.path.realpath(tmk_feature_collection_path)):
                f = {
                    "_id": str(uuid.uuid4()),
                    "geojson": feature,
                    "restrictions": {},
                    "organization": organization["_id"],
                    "name": "TMK " + str(feature['properties']['TMK']),
                    "last_imported_at": datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                }
                try:
                    _post_features(f)
                except Exception as e:
                    logger.error(e)

        return sys.exit(0)
    else:
        logger.error("Please input a valid, importable feature collection file.")
        return sys.exit(100)


def _features_from_path(feature_collection_path=None):
    with open(feature_collection_path) as json_data:
        feature_collection = json.load(json_data)
        if 'features' in feature_collection:
            for feature in feature_collection["features"]:
                yield feature


def _post_features(feature_as_json):
    resource_base_url = _get_resource_url('features')
    r = requests.post(resource_base_url, json=feature_as_json)
    if r.status_code == 201:
        logger.info("Successfully uploaded feature(id=" +
                    feature_as_json["_id"] + ")")
    else:
        logger.info("Unsuccessful: " + r.content)


def _get_organization(organization_name):
    resource_base_url = _get_resource_url('organizations')
    resource_payload = _get_regex_payload("name", organization_name)
    r = requests.get(resource_base_url, params=resource_payload)
    if r.status_code == 200:
        json_resp = r.json()
        if (len(json_resp["_items"])) == 1:
            return json_resp["_items"][0]
    return None


# TODO - Unsafe. (Probably) Need to sanitize, but lazymode atm.
def _get_regex_payload(field, field_query):
    regex_payload = {field: {'$regex': ".*" + field_query + ".*"}}
    return {'where': json.dumps(regex_payload)}


def _get_resource_url(resource_name):
    return API_BASE_URL_FORMAT.format(resource_name)


if __name__ == '__main__':
    import_tmk()

# vim: fenc=utf-8
# vim: filetype=python