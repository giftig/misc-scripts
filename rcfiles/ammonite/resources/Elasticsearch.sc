import $ivy.`com.sksamuel.elastic4s::elastic4s-core:8.11.4`
import $ivy.`com.sksamuel.elastic4s::elastic4s-client-esjava:8.11.4`

import com.sksamuel.elastic4s.{ElasticClient, ElasticProperties}
import com.sksamuel.elastic4s.ElasticDsl._
import com.sksamuel.elastic4s.fields._
import com.sksamuel.elastic4s.http.{JavaClient => EsJavaClient}

object Elasticsearch {
  def client(host: String = "http://localhost:9200"): ElasticClient = {
    ElasticClient(EsJavaClient(ElasticProperties(host)))
  }
}
