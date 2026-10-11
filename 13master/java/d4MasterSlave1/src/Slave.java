class Slave extends Thread {
	private boolean done = false;
	public void halt() {
		done = true;
	}
	protected boolean task() {
		/*
		if (state == goal) return true;
		improve state;
		return false;
		*/
		return true; // for now
	}
    public void run() {
      while(!done) {
         done = task();
		 // be cooperative:
         try {
			 Thread.sleep(1000);
		 } // sleep for 1 sec.
         catch(Exception e) {}
      }
   }
}