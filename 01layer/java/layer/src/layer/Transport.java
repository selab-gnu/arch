package layer;

public class Transport extends L2Provider {

	@Override
	public void l2Service() {
		System.out.println("L2Service doing its job");	
		level1.l1Service();
		System.out.println("L2Service ending its job");
	}

}
