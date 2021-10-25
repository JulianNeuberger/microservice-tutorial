import json
from threading import Thread
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exchange_type import ExchangeType
from pika.spec import Basic, BasicProperties

from service import ExampleService

OnMessageListener = Callable[[BlockingChannel, Basic.Deliver, BasicProperties, bytes], None]


class AMQPListener(Thread):
    def __init__(self, host: str, port: int, username: str, password: str, on_message: OnMessageListener):
        super().__init__()
        self._credentials = pika.PlainCredentials(username, password)
        self._connection_params = pika.ConnectionParameters(host=host, port=port, credentials=self._credentials)
        self._on_message = on_message
        self._connection = None
        self._channel = None
        self._document_removed_consumer = None
        self._interrupted = True

    def stop(self):
        print('Stopping AMQP listener...')
        self._interrupted = True

    def run(self):
        self._interrupted = False

        self._connection = pika.BlockingConnection(self._connection_params)

        self._channel = self._connection.channel()

        # register a exchange at the message broker, where we publish events (e.g. when creating or deleting datasets)
        self._channel.exchange_declare(exchange='ms.datasets', exchange_type=ExchangeType.fanout.value, durable=True)

        # the queue we register at the message broker to listen for document changes
        document_update_queue = 'propagate-document-deletions'

        # the exchange the document service registers at the message broker
        document_exchange = 'documentExchange'

        # routing key to the events we are interested in
        routing_key = 'document.event.deleted'

        # register a queue where we want to listen to document deletions
        # make it durable, so it survives crashes / reboots of our service (and the message broker)
        self._channel.queue_declare(queue=document_update_queue, durable=True)

        # bind the queue to the exchange of the document micro service
        self._channel.queue_bind(exchange=document_exchange, queue=document_update_queue, routing_key=routing_key)

        # start listening to the document microservice
        # if it removes a document update our datasets accordingly
        for deliver, properties, body in self._channel.consume(queue=document_update_queue, inactivity_timeout=1):
            if self._interrupted:
                break
            if deliver is None:
                continue
            self._on_message(self._channel, deliver, properties, body)

        self._channel.cancel()
        self._connection.close()


class MessageDispatcher:
    def __init__(self, example_service: ExampleService):
        self._service = example_service

    def dispatch(self, channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        print(f'Got AMQP message with routing key {method.routing_key}.')
        if method.routing_key == 'document.event.deleted':
            pass
        channel.basic_ack(delivery_tag=method.delivery_tag)

