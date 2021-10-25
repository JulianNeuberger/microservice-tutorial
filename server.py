import os
from configparser import ConfigParser

from flask import Flask
from flask_cors import CORS
from flask_hal import HAL
from flask_restful import Api

from messages import AMQPListener, MessageDispatcher
from resources import Example, ExamplesList
from service import ExampleService

if __name__ == '__main__':
    config: ConfigParser = ConfigParser()
    config.read('config.ini')

    eventsourcing_config_keys = [
        'INFRASTRUCTURE_FACTORY',
        'POSTGRES_DBNAME',
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_CONN_MAX_AGE',
        'POSTGRES_PRE_PING',
        'POSTGRES_LOCK_TIMEOUT',
        'POSTGRES_IDLE_IN_TRANSACTION_SESSION_TIMEOUT',
        'POSTGRES_PASSWORD',
        'POSTGRES_USER'
    ]
    for key in eventsourcing_config_keys:
        os.environ[key] = config['eventsourcing'][key]

    app = Flask(__name__)
    cors = CORS(app, resources={
        r'/api/*': {
            'origins': '*'
        }
    })
    HAL(app)
    api = Api(app, prefix='/api/')

    example_service = ExampleService()

    api.add_resource(Example, '/examples/<example_id>', resource_class_kwargs={'service': example_service})
    api.add_resource(ExamplesList, '/examples', resource_class_kwargs={'service': example_service})

    rabbit_mq_host = config['rabbitmq']['host']
    rabbit_mq_port = config['rabbitmq']['port']
    rabbit_mq_user = config['rabbitmq']['user']
    rabbit_mq_pass = config['rabbitmq']['pass']

    dispatcher = MessageDispatcher(example_service)
    listener = AMQPListener(rabbit_mq_host, int(rabbit_mq_port), rabbit_mq_user, rabbit_mq_pass, dispatcher.dispatch)
    listener.start()

    app.run(debug=True, use_reloader=False)

    listener.stop()
    listener.join()
    example_service.shutdown()
