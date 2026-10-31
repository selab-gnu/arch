package blackboard;

import java.util.Calendar;
import java.util.Date;

public class ControlData {
	public String problem;
	public Object[] input;
	public Object[] output;
	public String updateby;
	public Date updated;

	public ControlData() {
		this.problem = null;
		this.input = null;
		this.output = null;
	}

	public ControlData(String problem, Object[] input) {
		this.problem = problem;
		this.input = input;
		this.updated = Calendar.getInstance().getTime();
	}

	public Object getResult() {
		return this.output;
	}

	public Object Clone() {
		ControlData clone;
		clone = new ControlData(this.problem, this.input);
		clone.updated = this.updated;
		clone.updateby = this.updateby;
		clone.output = this.output;
		return clone;
	}
}