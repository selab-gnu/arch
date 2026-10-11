package layer;

public class Session extends L3Provider {

	@Override
	public void l3Service() {
		System.out.println("L3Service starting its job");	
		level2.l2Service();
		System.out.println("L3Service ending its job");			
	}

}
