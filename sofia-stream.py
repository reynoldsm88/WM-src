#!/usr/bin/env python3

import json
import os
import ssl
from datetime import datetime
from os.path import basename

import faust
import requests
from requests.auth import HTTPBasicAuth

from sofia import *


def create_kafka_app(broker, user, pwd):
    credentials = None
    if user is not None and pwd is not None:
        credentials = faust.SASLCredentials(
            username=user,
            password=pwd,
            ssl_context=ssl.create_default_context()
        )

    # create your application
    app = faust.App(
        'sofia',
        autodiscover=False,
        broker=broker,
        broker_credentials=credentials,
        topic_disable_leader=True,
        consumer_auto_offset_reset='earliest' )

    return app


def remove_empty_lines(text_init):
    lines = text_init.split('\n')
    new_lines = []
    for line in lines:
        line = line.strip('\n')
        if len(line) > 20:
            new_lines.append(line)
    return '\n'.join(new_lines)


def get_cdr_text(doc_id, cdr_api, sofia_user, sofia_pass):
    url = f'{cdr_api}/{doc_id}'

    http_auth = None
    if sofia_user is not None and sofia_pass is not None:
        http_auth = HTTPBasicAuth(sofia_user, sofia_pass)

    response = requests.get(url, auth=http_auth)

    if response.status_code == 200:
        cdr_json = json.loads(response.text)
        return remove_empty_lines(cdr_json['extracted_text'])
    else:
        print(f'error getting CDR data from DART service: {response.status_code} : {response.text}')
        return None


def upload_sofia_output(doc_id, file, output_api, sofia_user, sofia_pass):
    metadata = {
        "identity": "sofia",
        "version": "1.1",
        "document_id": doc_id
    }

    form_request = {"file": (basename(file.name), file), "metadata": (None, json.dumps(metadata), 'application/json')}

    http_auth = None
    if sofia_user is not None and sofia_pass is not None:
        http_auth = HTTPBasicAuth(sofia_user, sofia_pass)

    response = requests.post(output_api, files=form_request, auth=http_auth)

    if response.status_code == 201:
        print("File uploaded!")
    else:
        print(f"Uploading of {doc_id} failed! Please re-try")


def run_sofia_stream(kafka_broker,
                     upload_api,
                     cdr_api,
                     sofia_user,
                     sofia_pass,
                     ontology='compositional',
                     experiment='may2021',
                     version='v1'):
    sofia = SOFIA(ontology)

    app = create_kafka_app(kafka_broker, sofia_user, sofia_pass)
    dart_update_topic = app.topic("dart.cdr.streaming.updates", key_type=str, value_type=str)

    @app.agent(dart_update_topic)
    async def process_document(stream: faust.StreamT):
        doc_stream = stream.events()
        async for cdr_event in doc_stream:
            doc_id = cdr_event.key
            extracted_text = get_cdr_text(doc_id, cdr_api, sofia_user, sofia_pass)
            print("fourth")
            if extracted_text is not None:
                output = sofia.get_online_output(extracted_text, experiment=experiment, file_name=f'{doc_id}_{version}')
                if output is not None:
                    upload_sofia_output(doc_id, output, upload_api, sofia_user, sofia_pass)

    try:
        app.main()
    except ConnectionError as ce:
        print(f'error connecting to kafka broker @ {kafka_broker} - {ce}')
        exit(1) # exit as failed so the Docker environment can control restarts


if __name__ == '__main__':
    datetime_slug = datetime.now().strftime("%m/%d/%Y-%H:%M:%S")
    _kafka_broker = os.environ.get('KAFKA_BROKER') if os.environ.get('KAFKA_BROKER') is not None else 'localhost:9092'
    _upload_api = os.environ.get('UPLOAD_API_URL') if os.environ.get('UPLOAD_API_URL') is not None else 'localhost:1337'
    _cdr_api = os.environ.get('CDR_API_URL') if os.environ.get('CDR_API_URL') is not None else 'localhost:8090'
    _sofia_user = os.environ.get('SOFIA_USER')
    _sofia_pass = os.environ.get('SOFIA_PASS')
    _ontology = os.environ.get('ONTOLOGY') if os.environ.get('ONTOLOGY') is not None else 'compositional'
    _experiment = os.environ.get('EXPERIMENT') if os.environ.get('EXPERIMENT') is not None else f'test-{datetime_slug}'
    _version = os.environ.get('VERSION') if os.environ.get('VERSION') is not None else 'v1'

    run_sofia_stream(_kafka_broker, _upload_api, _cdr_api, _sofia_user, _sofia_pass, _experiment, _version)
