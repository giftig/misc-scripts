import akka.actor.ActorSystem
import akka.stream.alpakka.dynamodb._
import akka.stream.alpakka.dynamodb.scaladsl.DynamoDb
import com.amazonaws.services.dynamodbv2.model._

// Avoid clashing with alpakka's DynamoDb object
object Dynamo {
  import scala.collection.JavaConverters._
  import scala.concurrent.Future
  import akka.stream.Materializer
  import akka.stream.scaladsl._

  def awsClient(implicit system: ActorSystem, mat: Materializer): DynamoClient = {
    val settings = DynamoSettings("eu-west-1", "dynamodb.eu-west-1.amazonaws.com")
    DynamoClient(settings)
  }

  def localClient(implicit system: ActorSystem, mat: Materializer): DynamoClient = {
    val settings = DynamoSettings("eu-west-1", "localhost").withPort(8000).withTls(false)
    DynamoClient(settings)
  }

  def put(table: String, data: Map[String, String]): PutItemRequest = {
    new PutItemRequest(table, data.mapValues { new AttributeValue(_) }.asJava)
  }

  def single(op: AwsOp)(implicit mat: Materializer, c: DynamoClient) = {
    val src = DynamoDb.source(op).withAttributes(DynamoAttributes.client(c))
    val g = src.toMat(Sink.head)(Keep.right)
    g.run()
  }
}
