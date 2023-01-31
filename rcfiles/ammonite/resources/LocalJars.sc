// Try to find and import jar files belonging to the local project

object LocalJarImporter {
  import java.io.File
  import java.net.URL
  import scala.annotation.tailrec
  import scala.math.Ordering

  /**
   * List files directly under f safely, dealing with the potential null from .listFiles
   */
  private def listFiles(f: File): Seq[File] = Option(f.listFiles).toSeq.flatten

  implicit val ordering: Ordering[URL] = Ordering.by(_.toString)

  /**
   * Print the provided message in yellow with ANSI colouring
   */
  private def notice(s: String): Unit = println(s"\u001b[33m$s\u001b[0m")

  lazy val targetJars: Seq[URL] = {
    val target = new File("./target")

    if (target.isDirectory) {
      listFiles(target)
        .filter { f => f.isDirectory && f.getName.startsWith("scala-") }
        .flatMap(listFiles)
        .collect {
          case f if f.isFile && f.getName.endsWith(".jar") => f.getCanonicalFile.toURI.toURL
        }
    } else Nil
  }

  /**
   * Find jars in ./target/scala-xxx and load the last one alphabetically
   *
   * This is a naive way of trying to load the most recent version, if multiple versions are
   * present. It could probably do with a bit of refinement if this comes up a lot.
   */
  def load(): Unit = {
    targetJars.sorted.reverse match {
      case Nil =>
      case single :: Nil =>
        notice(s"Loaded jar file $single")
        interp.load.cp(single)
      case h :: t =>
        notice(s"Found ${t.length + 1} jar files, loaded only ${h}")
        interp.load.cp(h)
    }
  }
}

LocalJarImporter.load()
