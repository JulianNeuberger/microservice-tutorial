from eventsourcing.application import AggregateNotFound
from flask import request
from flask_restful import Resource, abort

from tutorial.serializer import ExampleSerializer
from tutorial.service import ExampleService


def abort_not_json():
    abort(400, message='Only accepting requests with mime type application/json.')


def abort_missing_parameter(parameter_name: str):
    abort(400, message=f'Expected "{parameter_name}" to be part of the request body.')


class Example(Resource):
    def __init__(self, service: ExampleService):
        self._service = service
        self._serializer = ExampleSerializer(self._service)

    def get(self, example_id: str):
        example = self._service.get_one(example_id)
        if example.deleted:
            return abort(404)
        return self._serializer.serialize_single(example)

    def patch(self, example_id: str):
        if not request.is_json:
            return abort_not_json()

        body = request.json

        try:
            example = self._service.get_one(example_id)
            if example.deleted:
                return abort(404)
        except AggregateNotFound:
            return abort(404)

        if 'name' not in body:
            abort_missing_parameter('name')

        name = body.get('name', None)
        example = self._service.update(example_id, name)
        return self._serializer.serialize_single(example)

    def delete(self, example_id):
        example = self._service.get_one(example_id)
        if example.deleted:
            return abort(404)
        self._service.delete(example_id)


class ExamplesList(Resource):
    def __init__(self, service: ExampleService):
        self._service = service
        self._serializer = ExampleSerializer(self._service)

    def get(self):
        examples = self._service.get_all()
        return self._serializer.serialize_examples(examples)

    def post(self):
        if not request.is_json:
            return abort_not_json()

        body = request.json
        if 'name' not in body:
            return abort_missing_parameter('name')

        example_name = body['name']
        example_id = self._service.create(example_name)
        example_id = example_id.hex

        example = self._service.get_one(example_id)
        return self._serializer.serialize_single(example)
