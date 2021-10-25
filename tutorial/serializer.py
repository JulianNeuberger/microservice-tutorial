from typing import List

from flask import request
from flask_hal.document import Document, Embedded, BaseDocument
from flask_hal.link import Collection, Link

from tutorial.domain import Example
from tutorial.service import ExampleService


class ExampleSerializer:
    def __init__(self, service: ExampleService):
        self._service = service

    def serialize_single(self, example: Example):
        return self._serialize(example, embed=True).to_dict()

    def serialize_examples(self, examples: List[Example]):
        hal_document = Document(
            data={
                'total': len(examples),
                'count': len(examples)
            },
            embedded={
                'examples': self._embed(examples)
            }
        )
        return hal_document.to_dict()

    def _embed(self, examples: List[Example]):
        return Embedded(
            data=[
                self._serialize(example, embed=False)
                for example
                in examples
            ]
        )

    def _serialize(self, example: Example, embed: bool = True):
        embedded = None
        if embed:
            related_examples = [self._service.get_one(related_example_id.hex) for related_example_id in example.related]
            serialized_related = [self._serialize(related_example, embed=False) for related_example in related_examples]
            embedded = {
                'related': Embedded(serialized_related)
            }

        print(request.url)

        return BaseDocument(
            data={
                'id': example.id.hex,
                'name': example.name
            },
            links=Collection(
                Link(rel='self', href=f'/api/examples/{example.id.hex}')
            ),
            embedded=embedded
        )
