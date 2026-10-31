package blackboard;

import java.util.Map.Entry;

public class Control {
	BlackBoard blackBoard = null;

	public Control(BlackBoard blackBoard) {
		this.blackBoard = blackBoard;
	}

	public void loop() throws Exception {
		System.out.println("Starting loop");
		if (blackBoard == null)
			throw new Exception("blackboard is null");
		this.nextSource();
		System.out.println("Loop ended");
	}

	/// Selects the next source of knowledge (knowledgeworker by inspecting the blackgoard)
	void nextSource() {
		// observers the blackboard
		for (Entry<String, ControlData> value : this.blackBoard.inspect().entrySet()) {
			if (value.getValue().problem == "PrimeNumbers") {
				for (KnowledgeWorker worker : this.blackBoard.knowledgeWorkers) {
					if (worker.getName() == "PrimeFinder") 	{
						System.out.println("Knowledge Worker Found");
						worker.executeCondition();
						worker.executeAction();
						worker.updateBlackboard();
					}
				}
			}                
		}
	}
}