// Needs to be early, before slf4j loggers get initialised
import $exec.resources.Logging

import $exec.resources.Akka, Akka._
import $exec.resources.Elasticsearch, Elasticsearch._
import $exec.resources.Json
import $exec.resources.Kamon
import $exec.resources.Mongo
import $exec.resources.Scalike
import $exec.resources.Testing
import $exec.resources.Time
import $exec.resources.TypesafeConfig

import $exec.resources.Slick, Slick._

import $exec.resources.LocalJars
import scala.collection.JavaConverters._
import scala.concurrent.{Await, ExecutionContext, Future}
import scala.concurrent.duration._

import com.typesafe.config.ConfigFactory
import kamon.Kamon

import ExecutionContext.Implicits.global

repl.prompt() = "> "
interp.colors().prompt() = fansi.Color.Green
