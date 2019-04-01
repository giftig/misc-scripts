import $ivy.`com.sksamuel.elastic4s::elastic4s-core:6.4.0`
import $ivy.`com.sksamuel.elastic4s::elastic4s-http:6.4.0`

import scala.concurrent.{ExecutionContext, Future}

import com.sksamuel.elastic4s.http._
import com.sksamuel.elastic4s.http.ElasticDsl._
import com.sksamuel.elastic4s.http.index.IndexResponse

object ElasticsearchUtils {
  def client(uri: String = "http://localhost:9200"): ElasticClient = {
    ElasticClient(ElasticProperties(uri))
  }

  def indexTest()(implicit ec: ExecutionContext): Future[Response[IndexResponse]] = {
    val req = indexInto("hodor/test").fields("test" -> true, "name" -> "Hodor")
    client().execute(req)
  }
}
