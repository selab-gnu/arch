package blackboard;

import java.util.Hashtable;
import java.util.List;

/// each knowledgeworker is resposible for knowing the conditions under which it can contribute to a solution.
abstract public  class KnowledgeWorker {
	protected Boolean canContribute;        
	protected String Name;                  
	public BlackBoard blackboard = null;    
	protected Hashtable<String, ControlData> keys;
	
	public KnowledgeWorker(BlackBoard blackboard, String Name)	{
		this.blackboard = blackboard;
		this.Name = Name;
	}

	public KnowledgeWorker(String Name)	{
		this.Name = Name;
	}

	public String getName() {
		return this.Name;
	}

	abstract public void executeAction();

	abstract public void executeCondition();

	abstract public void updateBlackboard();

}