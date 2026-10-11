package mvc;

public class Test {
	public static void main(String[] args) {
		Model model = new Model();
		View view = new View(model);
		model.setVotes(3);
		model.setParty("black");
	}
}
