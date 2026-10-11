package layer;

public abstract class L3Provider {
	public L2Provider level2;
	abstract void l3Service();
	public void setLowerLayer(L2Provider level2) {
		this.level2 = level2;
	}
}
