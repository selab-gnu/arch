package mvc;
import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;

public class View implements PropertyChangeListener {
	Model model;
	Controller controller;
	
	public View(Model model){
		this.model = model;
		this.model.addPropertyChangeListener(this);
		this.makeController();
	}
	
	public void makeController() {
		Controller controller = new Controller(model, this);
		model.addPropertyChangeListener(controller);
	}
	
    public void propertyChange(PropertyChangeEvent evt) {
        this.show();
    }
    
    public void show() {
    	System.out.println("View updates the information.");
    	System.out.println("* party: " + model.party);
    	System.out.println("* votes: " + model.votes);
    }
}