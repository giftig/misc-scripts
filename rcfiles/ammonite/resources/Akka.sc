import $ivy.`com.typesafe.akka::akka-actor:2.5.23`
import $ivy.`com.typesafe.akka::akka-slf4j:2.5.23`
import $ivy.`com.typesafe.akka::akka-stream:2.5.23`
import $ivy.`com.lightbend.akka::akka-stream-alpakka-dynamodb:1.1.1`
import $ivy.`com.typesafe.akka::akka-http:10.1.8`
import $ivy.`com.typesafe.akka::akka-http-spray-json:10.1.8`
import $ivy.`com.typesafe.akka::akka-testkit:2.5.23`
import $ivy.`com.typesafe.akka::akka-stream-testkit:2.5.23`
import $ivy.`com.typesafe.akka::akka-http-testkit:10.1.8`
import akka.actor._
import akka.pattern.ask
import akka.stream._
import akka.stream.scaladsl._
import akka.stream.testkit.scaladsl._
import akka.util.Timeout
import com.typesafe.config.{Config, ConfigFactory}

val defaultAkkaConfig: Config = ConfigFactory.parseString(
  """
  akka {
    loggers = ["akka.event.slf4j.Slf4jLogger"]
    loglevel = DEBUG
    logging = "akka.event.slf4j.Slf4jLoggingFilter"
  }
  """
)
implicit val system: ActorSystem = ActorSystem("amm", defaultAkkaConfig)
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

    // Only one handler which gets overwritten because I don't want this too complex
    private var additionalHandler: PartialFunction[Any, Any] = PartialFunction.empty

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

      case SandboxActor.Handle(f) =>
        additionalHandler = f

      case msg =>
        additionalHandler.lift(msg) foreach { res => sender() ! res }
    }
  }

  object SandboxActor {
    val props: Props = Props[SandboxActor]

    case class Reply[T](ref: ActorRef, msg: T)
    case class Handle(f: PartialFunction[Any, Any])
  }
}
