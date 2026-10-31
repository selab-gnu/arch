package blackboard;

public class TestBlackBoard {
	public static void main(String[] args) {
		BlackBoard board = new BlackBoard();

		KnowledgeWorker worker1 = new Worker1(board, "PrimeFinder");
		board.addKnowledgeWorker(worker1);
		
		Integer[] intArray = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
		ControlData data = new ControlData("PrimeNumbers", intArray);
		
		try {
			board.update("PrimeNumbers", data);
			board.control.loop();
		} catch (Exception e) {
			e.printStackTrace();
		}
	}
}
