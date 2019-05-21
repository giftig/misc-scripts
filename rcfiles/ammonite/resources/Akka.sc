import $ivy.`com.typesafe.akka::akka-actor:2.5.19`
import $ivy.`com.typesafe.akka::akka-slf4j:2.5.19`
import $ivy.`com.typesafe.akka::akka-stream:2.5.19`
import $ivy.`com.typesafe.akka::akka-http:10.1.3`
import $ivy.`com.typesafe.akka::akka-testkit:2.5.19`
import akka.actor._
import akka.stream._
import akka.stream.scaladsl._
import akka.util.Timeout

object Akka {
  /**
   * A simple actor which responds to a handful messages in interesting ways for easy testing
   */
  class SandboxActor extends Actor {
    private var nextActor: Int = 1

    override def receive: Receive = {
      case props: Props =>
        val name = s"sandbox-$nextActor"
        nextActor += 1
        sender() ! context.actorOf(props, name)

      case t: Throwable =>
        throw t
    }
  }

  object SandboxActor {
    val props: Props = Props[SandboxActor]
  }
}
