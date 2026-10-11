package layer;

public abstract class L2Provider {
	
	public L1Provider level1;
	
	abstract void l2Service();
	
	public void setLowerLayer(L1Provider level1) {
		this.level1 = level1;
	}
}
