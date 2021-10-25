from functools import singledispatchmethod
from uuid import UUID

from eventsourcing.application import Application, ProcessEvent, AggregateNotFound
from eventsourcing.domain import AggregateEvent
from eventsourcing.system import Follower

from tutorial.domain import Example, ExampleQueryModel


class Examples(Application):
    """
    A application in domain driven design is responsible for
    querying and changing the state of specific part of the
    domain.

    Following the Command-Query-Responsibility-Segregation pattern
    we make a distinction between queries (getting state) and
    commands (changing state). This means that we don't have
    methods that both change and query state. With this distinction
    we can build robust services in the next layer up.
    """

    def create(self, name: str) -> UUID:
        """
        Command for creating a new aggregate. In event sourcing
        creating a new aggregate works by triggering the appropriate
        event (in this case Example.Created) and then writing it
        to the notification log, here: `self.save`.

        :param name: name of the new aggregate (initial state)
        :return: the id of the newly created aggregate
        """
        example = Example.create(name)
        self.save(example)
        return example.id

    def get_one(self, example_id: UUID) -> Example:
        """
        Query method for loading a single aggregate. We use
        the provided repository to load it from the persistence
        layer. Internally all events belonging to the aggregate
        with the provided id are loaded and applied one after
        the other until we arrive at the latest version of the
        queried aggregate.

        :param example_id: id of the :class:`Example` to load
        :raises AggregateNotFound: if no aggregate with given id exists
        :return: the requested aggregate at latest version, iff it exists
        """
        return self.repository.get(example_id)

    def update_one(self, example_id: UUID, new_name: str) -> None:
        """
        Command for updating the state of our example aggregate. The
        application will trigger the appropriate event via the aggregate
        and save all unsaved events to the event log afterwards. It
        doesn't return the aggregate in question, to preserve the
        segregation between commands and queries.

        :param example_id: id of the :class:`Example` to update
        :param new_name: new state, or state changes
        :return: None
        """
        # the repository is generic and has no type hint to know that
        # we will load an instance of `Example`, so we type hint the
        # variable `example`, to get proper IDE support
        example: Example = self.repository.get(example_id)
        example.name = new_name
        self.save(example)

    def delete_one(self, example_id: UUID) -> None:
        """
        Command for deleting the aggregate with given id. Deleting this
        example aggregate will set it's `deleted` flag to True. This is
        not handled by the eventsourcing library, but instead it's part
        of the developers responsibility to manage the deleted state of
        your aggregates, if needed.

        :param example_id: aggregate id to mark as deleted.
        """
        example: Example = self.repository.get(example_id)
        example.delete()
        self.save(example)


class ExamplesIndex(Follower):
    """
    If you take a look at the :class:`Examples` application, you will notice
    it doesn't provide a `get_all` method, for retrieving all existing
    aggregates. This is because there is nothing tracking this information.
    In fact, this information would be state that has to be managed, which
    is what this application does.

    Instead of inheriting from a plain :class:`Application` we instead extend
    the :class:`Follower` class, which can be used with a
    :class:`eventsourcing.system.System` on the interface level, to notify this
    application about domain events and produce new ones in response.
    The :meth:`ExamplesIndex.policy` method is responsible for dispatching any
    domain events.
    """

    def get(self):
        query_model_id = ExampleQueryModel.create_id()
        query_model: ExampleQueryModel

        try:
            query_model = self.repository.get(query_model_id)
        except AggregateNotFound:
            query_model = ExampleQueryModel.create()

        return query_model

    @singledispatchmethod
    def policy(self, domain_event: AggregateEvent, process_event: ProcessEvent) -> None:
        """
        This method is passed any domain events that occur in the application it
        follows. It can record new (process) events by writing to the provided
        process event argument.

        The @singledispatchmethod annotator marks this method as being a dispatcher
        for different behaviours depending on the type of the domain_event argument.
        Instead of building an if/elif statement for all options you write separate
        methods and annotate them with `policy.register`, passing the expected type
        as a type hint, see e.g. :meth:`_handle_created`

        :param domain_event: event that occurred in the leading application
        :param process_event:
        """

    @policy.register(Example.Created)
    def _handle_created(self, domain_event: Example.Created, process_event: ProcessEvent) -> None:
        assert isinstance(domain_event, Example.Created)
        query_model = self.get()
        # originator_id refers to the aggregate this domain event belongs to
        example_id = domain_event.originator_id
        query_model.add(example_id)
        process_event.save(query_model)

    @policy.register(Example.Deleted)
    def _handle_deleted(self, domain_event: Example.Deleted, process_event: ProcessEvent) -> None:
        assert isinstance(domain_event, Example.Deleted)
        query_model = self.get()
        example_id = domain_event.originator_id
        query_model.remove(example_id)
        process_event.save(query_model)

    @policy.register(Example.Link)
    def _handle_linked(self, domain_event: Example.Link, process_event: ProcessEvent) -> None:
        assert isinstance(domain_event, Example.Link)
        query_model = self.get()
        owner_id = domain_event.originator_id
        other_id = domain_event.other_id
        query_model.add_link(owner_id, other_id)
        process_event.save(query_model)
