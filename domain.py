from typing import List, Dict, Set
from uuid import uuid4, UUID, uuid5, NAMESPACE_URL

from eventsourcing.domain import Aggregate, AggregateCreated, AggregateEvent


class Example(Aggregate):
    """
    This is an example domain entity modeled by event sourcing.
    Notice the base class :class:`eventsourcing.domain.Aggregate`.

    Attributes:
        name        Some descriptive name of this domain entity.
                    This is the main state, that is controlled in this example.
        related     Example for a uni-directional relation to other
                    example instances.
        deleted     A flag that marks this instance as deleted.
    """

    name: str
    related: List[UUID]
    deleted: bool

    def __init__(self, name: str):
        """
        Constructor method for this aggregate, will be used by the :class:`Example.Created`
        event to create the aggregate in its initial state.

        :param name: an example parameter used for the initial state of this aggregate
        """
        self.name = name
        self.related = []
        self.deleted = False

    @classmethod
    def create(cls, name: str) -> 'Example':
        """
        Used to create a new aggregate by the :class:`Examples` application.

        :param name: example parameter to control the initial aggregate
        :return: a new example aggregate
        """
        return cls._create(cls.Created, id=uuid4(), name=name)

    def update_name(self, name: str) -> None:
        """
        This command triggers a domain event. It will be called from outside,
        i.e. the application layer. Changes state of this aggregate by creating
        and attaching the :class:`Update` event to this aggregate. It is not
        responsible for saving or recording it, which instead is done by the
        Application.

        :param name: the new name of our example
        """
        self.trigger_event(self.Update, new_name=name)

    def link(self, other: UUID) -> None:
        """
        This command will link this example domain entity to another one,
        forming the uni-directional relation self -> other. Other will not
        be altered, as in this case the relation is owned by the domain
        entity the method `link` is called on.

        :param other: id of the other Example instance
        """
        self.trigger_event(self.Link, other_id=other)

    def delete(self) -> None:
        """
        This command will mark the aggregate as deleted, but not really removing
        anything from persistence. It does so by triggering the :class:`Deleted`
        event.
        """
        self.trigger_event(self.Deleted)

    class Created(AggregateCreated):
        """
        This is the event sourcing event that creates a new domain entity.
        It inherits from :class:`eventsourcing.domain.AggregateCreated`, so
        it doesn't need to implement the apply method, which usually is used
        to mutate the aggregate.
        """

        name: str

    class Update(AggregateEvent):
        """
        An example domain event, that is normally triggered by outside interaction
        (e.g. the user) and mutates the state of our domain entity (aggregate)
        via the :func:`apply` method. Just like the :class:`Created` event it
        will be passed any attributes defined below, here: `new_name`
        """

        new_name: str

        def apply(self, example: 'Example'):
            example.name = self.new_name

    class Link(AggregateEvent):
        other_id: UUID

        def apply(self, example: 'Example'):
            example.related.append(self.other_id)

    class Deleted(AggregateEvent):
        """
        In event sourcing aggregates are never truly removed, only marked "inactive".
        State of other aggregates or views (query models) should still be updated,
        so they can treat the specific aggregate as if it no longer exists.
        """

        def apply(self, example: 'Example'):
            example.deleted = True


class ExampleQueryModel(Aggregate):
    """
    This is an example query model for the example domain entity.
    Query models manage special state used to retrieve domain entities,
    as such they can become very complicated. Still, they are "only"
    aggregates and should change state according to domain events.

    Attributes:
         reversed_related_index     a dictionary used to look up Example
                                    instances that hold a reference to
                                    a given Example instance.
         index                      a collection of known instances.
    """

    reversed_related_index: Dict[UUID, Set[UUID]]
    index: Set[UUID]

    def __init__(self):
        self.reversed_related_index = {}
        self.index = set()

    @classmethod
    def create_id(cls):
        """
        :return: uuid of the single index aggregate
        """
        return uuid5(NAMESPACE_URL, '/index/example')

    @classmethod
    def create(cls) -> 'ExampleQueryModel':
        """
        Creating an aggregate normally involves a random uuid, but
        in this case we only will ever have exactly one. We can
        therefore create the id via uuid5, which is deterministic
        and later retrieve that aggregate via the same uuid.

        :return: the newly created index aggregate
        """
        index_id = cls.create_id()
        return cls._create(cls.Created, id=index_id)

    def add(self, example_id: UUID):
        self.trigger_event(self.AddToModel, example_id=example_id)

    def remove(self, example_id: UUID):
        self.trigger_event(self.RemoveFromModel, example_id=example_id)

    def add_link(self, owner_id: UUID, other_id: UUID):
        self.trigger_event(self.AddLinkToModel, owner_id=owner_id, other_id=other_id)

    class AddToModel(AggregateEvent):
        example_id: UUID

        def apply(self, aggregate: 'ExampleQueryModel'):
            aggregate.index.add(self.example_id)
            aggregate.reversed_related_index[self.example_id] = set()

    class RemoveFromModel(AggregateEvent):
        example_id: UUID

        def apply(self, aggregate: 'ExampleQueryModel'):
            aggregate.index.remove(self.example_id)
            del aggregate.reversed_related_index[self.example_id]
            # removing all references to the removed example, could be
            # improved performance-wise by holding a second dictionary
            for links in aggregate.reversed_related_index.values():
                links.remove(self.example_id)

    class AddLinkToModel(AggregateEvent):
        owner_id: UUID
        other_id: UUID

        def apply(self, aggregate: 'ExampleQueryModel'):
            if self.other_id not in aggregate.reversed_related_index:
                aggregate.reversed_related_index[self.other_id] = set()
            aggregate.reversed_related_index[self.other_id].add(self.owner_id)
