import $ivy.`com.typesafe.akka::akka-actor:2.5.23`
import $ivy.`com.typesafe.akka::akka-slf4j:2.5.23`
import $ivy.`com.typesafe.akka::akka-stream:2.5.23`
import $ivy.`com.lightbend.akka::akka-stream-alpakka-dynamodb:1.1.0`
import $ivy.`com.typesafe.akka::akka-http:10.1.8`
import $ivy.`com.typesafe.akka::akka-testkit:2.5.23`
import akka.actor._
import akka.pattern.ask
import akka.stream._
import akka.stream.scaladsl._

implicit val system: ActorSystem = ActorSystem("amm")
implicit val mat: Materializer = ActorMaterializer()

object Akka {
  import scala.concurrent.ExecutionContext
  import scala.concurrent.duration.FiniteDuration

  /**
   * A simple actor which responds to a handful messages in interesting ways for easy testing
   */
  class SandboxActor extends Actor {
    private implicit val ec: ExecutionContext = context.system.dispatcher
    private var nextActor: Int = 1

    override def receive: Receive = {
      case "ping" =>
        sender() ! "pong"

      case props: Props =>
        val name = s"sandbox-$nextActor"
        nextActor += 1
        sender() ! context.actorOf(props, name)

      case s: String =>
        println(s"Received message ($self): $s")

      case t: Throwable =>
        throw t

      case d: FiniteDuration =>
        context.system.scheduler.scheduleOnce(
          d,
          self,
          SandboxActor.Reply(sender(), s"Timeout $d elapsed")
        )

      case SandboxActor.Reply(ref, msg) =>
        ref ! msg
    }
  }

  object SandboxActor {
    val props: Props = Props[SandboxActor]

    case class Reply[T](ref: ActorRef, msg: T)
  }
}
