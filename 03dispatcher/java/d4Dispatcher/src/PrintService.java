
public class PrintService implements Service {
	String nameofservice; // service name 
	String nameofserver; // server name 
	String greeting;

	public PrintService(String svc, String srv) {
		nameofservice = svc; 
		nameofserver = srv;
		Client.dsp.registerService(nameofservice,this) ; 
	} 

	public void runService() { 
		//test output 
		System.out.println("Service: " + " " + nameofservice + " by " + nameofserver); 
	} 
} 
