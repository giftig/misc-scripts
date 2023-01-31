//import $ivy.`io.netty:netty-all:4.1.68.Final`
//import $ivy.`io.netty:netty-buffer:4.1.68.Final`
import $ivy.`org.apache.spark::spark-sql:3.3.1`
import $ivy.`sh.almond::ammonite-spark:0.13.5`

import org.apache.spark.sql._

val spark = AmmoniteSparkSession.builder().master("local[*]").getOrCreate()
import spark.implicits._
