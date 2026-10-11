package layer;

public class Test {

	public static void main(String[] args) {
		DataLink dataLink = new DataLink();
		Transport transport = new Transport();
		Session session = new Session();
		
		transport.setLowerLayer(dataLink);
		session.setLowerLayer(transport);
		
		session.l3Service();
	}

}
