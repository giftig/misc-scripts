import $ivy.`com.typesafe.slick::slick:3.3.3`
import $ivy.`org.postgresql:postgresql:42.2.5`

import slick.driver.PostgresDriver
import slick.driver.PostgresDriver.api._
import slick.jdbc.JdbcBackend.{Database, DatabaseDef}

object SlickDb {
  def postgres: DatabaseDef = Database.forURL(
    url = "jdbc://postgresql://localhost:5432/test",
    driver = "slick.driver.PostgresDriver"
  )
}
