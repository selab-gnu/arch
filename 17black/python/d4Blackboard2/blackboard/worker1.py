from .knowledge_worker import KnowledgeWorker


class Worker1(KnowledgeWorker):
    def execute_action(self) -> None:
        print("Worker1-executeAction")

    def execute_condition(self) -> None:
        print("Worker1-executeCondition")

    def update_blackboard(self) -> None:
        print("Worker1-updateBlackboard")
