
public class TestClient {

	public static void main(String[] args) {
		new PrintService("printSvc","srv1"); 
		new PrintService("printSvc","srv2");
		Client client = new Client (); 
		client.doTask (); 
	}

}
