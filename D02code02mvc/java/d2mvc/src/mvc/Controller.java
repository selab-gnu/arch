package mvc;
import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;

public class Controller implements PropertyChangeListener {
	Model model;
	View view;
	
	public Controller(Model model, View view) {
		this.model = model;
		this.view = view;
	}

    public void propertyChange(PropertyChangeEvent evt) {
        System.out.println("the controller notices the change of the model:"+evt.getPropertyName());
    }
   
}