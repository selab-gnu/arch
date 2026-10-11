
public class Master {
	private int slaveCount = 10;
    private Slave[] slaves = new Slave[slaveCount];
    public void run() {
   	  // create slaves:
      for(int i = 0; i < slaveCount; i++) {
         slaves[i] = new Slave();
      }
      // start slaves:
      for(int i = 0; i < slaveCount; i++) {
         slaves[i].start();
      }
      // wait for slaves to die:
      for(int i = 0; i < slaveCount; i++) {
         try {
            slaves[i].join();
         } catch(InterruptedException ie) {
               System.err.println(ie.getMessage());
         } finally {
            System.out.println(slaves[i].getName() + " has died");
         }
      }
      System.out.println("The master will now die ... ");
   }
}