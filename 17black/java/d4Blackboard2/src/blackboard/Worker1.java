package blackboard;

public class Worker1 extends KnowledgeWorker {
	
	public Worker1(BlackBoard blackboard, String Name)	{
		super(blackboard, Name);
	}

	public Worker1(String Name)	{
		super(Name);
	}

	@Override
	public void executeAction() {
		System.out.println("Worker1-executeAction");
	}

	@Override
	public void executeCondition() {
		System.out.println("Worker1-executeCondition");
	}

	@Override
	public void updateBlackboard() {
		System.out.println("Worker1-updateBlackboard");
	}

}
