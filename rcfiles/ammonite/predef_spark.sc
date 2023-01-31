import $exec.predef

import $exec.resources.Spark

val spark = AmmoniteSparkSession.builder().master("local[*]").getOrCreate()
