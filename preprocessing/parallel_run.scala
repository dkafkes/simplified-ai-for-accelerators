// Databricks notebook source
import scala.concurrent.{Future, Await}
import scala.concurrent.duration._
import scala.util.control.NonFatal
/**
@author:Arun Pamulapati
@numNotebooksInParallel: Number of notebooks you would like this class to parallleize.
@path: Notebook you would like to parallelize
@timeout:timeout after which you like to terminate the notbook
@params: key values your notebook widget can use.
**/
case class ParallelNotebookRunner(path: String, timeout: Int, parameters: Map[String, String] = Map.empty[String, String])

def parallelNotebooks(notebooks: Seq[ParallelNotebookRunner]): Future[Seq[String]] = {
  import scala.concurrent.{Future, blocking, Await}
  import java.util.concurrent.Executors
  import scala.concurrent.ExecutionContext
  import com.databricks.WorkflowException
  //numNotebooksInParallel: int
  val numNotebooksInParallel = 5 
  // If you create too many notebooks in parallel the driver may crash when you submit all of the jobs at once. 
  // This code limits the number of parallel notebooks.
  implicit val ec = ExecutionContext.fromExecutor(Executors.newFixedThreadPool(numNotebooksInParallel))
  val ctx = dbutils.notebook.getContext()
  
  Future.sequence(
    notebooks.map { notebook => 
      Future {
        dbutils.notebook.setContext(ctx)
        if (notebook.parameters.nonEmpty)
          dbutils.notebook.run(notebook.path, notebook.timeout, notebook.parameters)
        else
          dbutils.notebook.run(notebook.path, notebook.timeout)
      }
      .recover {
        case NonFatal(e) => s"ERROR: ${e.getMessage}"
      }
    }
  )
}


