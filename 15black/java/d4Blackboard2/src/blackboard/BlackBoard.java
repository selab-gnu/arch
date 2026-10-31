package blackboard;

import java.util.Hashtable;
import java.util.LinkedList;
import java.util.List;
import java.util.Map.Entry;
   public class BlackBoard
    {
        public List<KnowledgeWorker> knowledgeWorkers;
        protected Hashtable<String, ControlData> data;
        public Control control;

        public BlackBoard() {
            this.knowledgeWorkers = new LinkedList<KnowledgeWorker>();
            this.control = new Control(this);
            this.data = new Hashtable<String, ControlData>();
        }

        public void addKnowledgeWorker(KnowledgeWorker newKnowledgeWorker) {
            newKnowledgeWorker.blackboard = this;
            this.knowledgeWorkers.add(newKnowledgeWorker);
        }       

        public Hashtable<String, ControlData> inspect() {
            return this.data;
        }
        public void update(Entry<String, ControlData> blackboardEntry) throws Exception  {
            if (this.data.containsKey(blackboardEntry.getKey())) {
                this.data.put(blackboardEntry.getKey(), blackboardEntry.getValue());
            }
            else
                throw new Exception(blackboardEntry.getKey() + " Not Found!");
        }

        public void update(String key, ControlData data) {
                this.data.put(key, data);
        }

        public void print() {
            System.out.println("Blackboard state");
            for (Entry<String, ControlData> cdata : this.data.entrySet()) {
            	System.out.println(String.format("data:{0}", cdata.getKey()));
            	System.out.println(String.format("\tProblem:{0}", cdata.getValue().problem));
                if(cdata.getValue().input!=null) {
                	String s = join(cdata.getValue().input);
                	System.out.println(String.format("\tInput:{0}", s));
                }
                if(cdata.getValue().output!=null) {
                	String s = join(cdata.getValue().output);
                	System.out.println(String.format("\tOutput:{0}", s));
                }
            }
        }
        
        String join(Object[] s) {
            StringBuilder builder = new StringBuilder();
            for (int i = 0; i < s.length; i++) {
            	builder.append(s[i] + ", ");
            }
            return builder.toString();
        }

    }