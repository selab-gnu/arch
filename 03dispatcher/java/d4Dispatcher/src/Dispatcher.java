
import java.util.*;
public class Dispatcher {
	Hashtable<String,Vector<Service>> registry = new Hashtable<String, Vector<Service>>(); 	
	Random rnd = new Random(123456);
	
	public void registerService(String svc, Service obj) {
		Vector<Service> v = registry.get(svc);
		if (v == null) {
			v = new Vector<Service>();
			registry.put(svc, v); 
		} 
		v.add(obj);
	} 
	public Service locateServer(String svc)	throws Exception { 
		Vector<Service> v = registry.get(svc);
		if (v == null) throw new Exception();
		if (v.size() == 0) throw new Exception();
		int i = rnd.nextInt() % v.size();
		return v.elementAt(i);
	}
}
