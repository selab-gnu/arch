"""Java의 ExampleRunner.main 에 해당하는 실행 진입점.

실행:  python -m pubsub.example_runner   (python/exPubSub 폴더에서)
"""
from pubsub.message import Message
from pubsub.publisher.publisher_impl import PublisherImpl
from pubsub.service.pub_sub_service import PubSubService
from pubsub.subscriber.subscriber_impl import SubscriberImpl


def main() -> None:
    java_publisher = PublisherImpl()
    java_subscriber = SubscriberImpl()
    pub_sub_service = PubSubService()

    # 메시지를 만들고 PubSubService 에 게시
    java_msg1 = Message("Java", "Core Java Concepts")
    java_msg2 = Message("Java", "Spring MVC : Dependency Injection and AOP")

    java_publisher.publish(java_msg1, pub_sub_service)
    java_publisher.publish(java_msg2, pub_sub_service)

    # 구독자 등록: Java 구독자는 Java 주제만 구독
    java_subscriber.add_subscriber("Java", pub_sub_service)

    # 모든 구독자에게 브로드캐스트. 이후 PubSubService 의 큐는 비워진다
    pub_sub_service.broadcast()

    # 구독자가 받은 메시지 출력
    print("Messages of Java Subscriber are: ")
    java_subscriber.print_messages()


if __name__ == "__main__":
    main()
