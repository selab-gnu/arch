package peer2peer;

public class PeerTest {
	public static void main(String[] args) throws InterruptedException {
		Thread serverThread = new Thread(new SimpleServer());
		Thread clientThread = new Thread(new SimpleClient());
		serverThread.start();
		Thread.sleep(3000);
		clientThread.start();
	}
}
