package pubsub;

import pubsub.publisher.Publisher;
import pubsub.publisher.PublisherImpl;
import pubsub.service.PubSubService;
import pubsub.subscriber.Subscriber;
import pubsub.subscriber.SubscriberImpl;

public class ExampleRunner {
	public static void main(String[] args) {	
		Publisher javaPublisher = new PublisherImpl();
		Subscriber javaSubscriber = new SubscriberImpl();	
		PubSubService pubSubService = new PubSubService();
		
		//Declare Messages and Publish Messages to PubSubService
		Message javaMsg1 = new Message("Java", "Core Java Concepts");
		Message javaMsg2 = new Message("Java", "Spring MVC : Dependency Injection and AOP");
		
		javaPublisher.publish(javaMsg1, pubSubService);
		javaPublisher.publish(javaMsg2, pubSubService);
				
		//Declare Subscribers: Java subscriber only subscribes to Java topics
		javaSubscriber.addSubscriber("Java",pubSubService);
		
		//Broadcast message to all subscribers. After broadcast, messageQueue will be empty in PubSubService
		pubSubService.broadcast();
		
		//Print messages of each subscriber to see which messages they got
		System.out.println("Messages of Java Subscriber are: ");
		javaSubscriber.printMessages();
	}
}