from typing import List
from uuid import UUID

from eventsourcing.system import System, SingleThreadedRunner

from tutorial.application import Examples, ExamplesIndex
from tutorial.domain import Example


class ExampleService:
    """
    The interface layer of domain driven design. Combines
    multiple applications to provide an interface to the
    domain entities, allowing manipulation (commands) and
    selection (queries).
    """

    def __init__(self):
        """
        Create an event sourcing system, that controls how
        applications interact with each other. The System is
        then passed to a Runner that executes it.

        A system is created with a List of Lists of Applications.
        Every List is a "pipe" of the structure
        `Application [-> ProcessApplication]* -> Follower`.
        """
        self._system = System(pipes=[
            [Examples, ExamplesIndex]
        ])
        self._runner = SingleThreadedRunner(self._system)
        self._runner.start()

    def shutdown(self):
        self._runner.stop()

    def get_one(self, example_id: str) -> Example:
        example_id = UUID(example_id)
        examples = self._runner.get(Examples)
        return examples.get_one(example_id)

    def get_all(self) -> List[Example]:
        indices = self._runner.get(ExamplesIndex)
        examples = self._runner.get(Examples)
        example_ids = indices.get().index
        return [examples.get_one(example_id) for example_id in example_ids]

    def create(self, name: str) -> UUID:
        examples = self._runner.get(Examples)
        example_id = examples.create(name)
        return example_id

    def update(self, examples_id: str, name: str) -> None:
        examples = self._runner.get(Examples)
        examples_id = UUID(examples_id)
        examples.update_one(examples_id, name)

    def delete(self, example_id: str) -> None:
        examples = self._runner.get(Examples)
        examples.delete_one(UUID(example_id))
