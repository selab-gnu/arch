package mvc;
import java.beans.PropertyChangeListener;
import java.beans.PropertyChangeSupport;
import java.util.Hashtable;

public class Model {
	String party;
	long votes;

	private PropertyChangeSupport support;

	public Model() {
		support = new PropertyChangeSupport(this);
		party = "none";
		votes = 0;
	}

	public void addPropertyChangeListener(PropertyChangeListener pcl) {
		support.addPropertyChangeListener(pcl);
	}

	public void removePropertyChangeListener(PropertyChangeListener pcl) {
		support.removePropertyChangeListener(pcl);
	}

	public void setVotes(long votes) {
		long prevVotes = this.votes;
		this.votes = votes;
		support.firePropertyChange("votes", prevVotes, votes);
	}
	
	public void setParty(String party) {
		String prevParty = this.party;
		this.party = party;
		support.firePropertyChange("party", prevParty, party);
	}
}