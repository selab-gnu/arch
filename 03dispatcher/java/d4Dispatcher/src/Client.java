public class Client {
	public static Dispatcher dsp = new Dispatcher();
	public void doTask() { 
		Service s; 
		try { 
			s=	dsp.locateServer ("printSvc") ; 
			s.runService ( ) ; 
		}catch (Exception n) { 
			System.out .println ("Printer 1 Not available") ; 
		} 
		try { 
			s = dsp.locateServer("printSvc");
			s.runService ( ) ; 
		}catch (Exception n) { 
			System.out.println("Printer 2 Not available"); 
		} 
		try { 
			s = dsp.locateServer("printSvc3"); 
			s .runService () ;
		}catch (Exception n) { 
			System.out.println("Printer 3 Not available") ; 
		} 
	}
}
