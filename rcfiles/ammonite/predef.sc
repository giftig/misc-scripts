import $exec.resources.Akka
import $exec.resources.Elasticsearch
import $exec.resources.Json
import $exec.resources.Mongo
import $exec.resources.Time
import $exec.resources.TypesafeConfig

import $ivy.`org.scalaz::scalaz-core:7.2.12`

import scala.collection.JavaConverters._
import scala.concurrent.{ExecutionContext, Future}

import ammonite.ops._

import ExecutionContext.Implicits.global

repl.prompt() = "> "
interp.colors().prompt() = fansi.Color.Green
