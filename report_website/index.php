<?php
if (!isset($_SERVER["PATH_INFO"])) {
?>
  <!doctype html>
  <html lang="en">
    <head>
      <!-- Required meta tags -->
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

      <!-- Bootstrap CSS -->
      <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
      <link rel="stylesheet" type="text/css" href="static/style.css">
      <title>RelMon Reports</title>
    </head>
    <body>
      <div class="container">
        <h1 class="mt-3">RelMon Reports</h1>
        <ul>
          <li><a href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/RelMon">RelMon twiki</a></li>
          <li><a href="http://cmsweb.cern.ch/dqm/online">Link to the Online DQM GUI</a></li>
          <li><a href="http://cmsweb.cern.ch/dqm/offline">Link to the Offline DQM GUI</a></li>
          <li><a href="http://cmsweb.cern.ch/dqm/relval">Link to the RelVal DQM GUI</a></li>
        </ul>
  <?php
        $relmons = glob('./*.sqlite');
        rsort($relmons);
        foreach($relmons as $relmon) {
  ?>
          <div class="row card mt-2">
            <div class="card-body">
              <div class="row">
                <div class="col-sm-12 col-md-8">
  <?php
                  $stat = stat($relmon);
                  $lastModified = date("Y-m-d H:i:s", $stat['mtime']);
                  $size = round($stat['size'] / (1024.0 * 1024.0), 2);
                  $relmonName = str_replace("./", "", $relmon);
                  $relmonName = str_replace(".sqlite", "", $relmonName);
                  print("<h5 id=\"$relmonName\" style=\"word-break:break-all;\">$relmonName</h5><small>Last modified: $lastModified<br>Size: $size MB</small>");
  ?>
                </div>
                <div class="col-sm-12 col-md-4">
                  <h5>Subcategories:</h5>
                  <ul>
  <?php
                    try {
                      $handle = new SQLite3($relmon);
                      $tablesquery = $handle->query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;");
                      while ($table = $tablesquery->fetchArray(SQLITE3_ASSOC)) {
                        $category = $table['name'];
                        print("<li><a href=\"$relmonName/$category/RelMonSummary.html\">$category</a></li>");
                      }
                      $handle->close();
                    } catch (Exception $e) {
                      print("<li><i>Error getting subcategories. Error:" + $e->getMessage());
                    }
                    /*foreach(glob("./$directory/*.zip") as $zipFile) {
                      $category = str_replace('.zip', '', $zipFile);
                      $category = str_replace("./$directory/", '', $category);
                      $lastModified = date("F d Y H:i:s", filemtime($zipFile));
                      print("<li title=\"Last modified: $lastModified\"><a href=\"$directory/$category/RelMonSummary.html\">$category</a></li>");
                    }*/
  ?>
                  </ul>
                </div>
              </div>
            </div>
          </div>
  <?php
        }
  ?>
      </div>
    </body>
  </html>
<?php
} else {
  header("Content-Encoding: gzip");
  header('Expires: '.gmdate('D, d M Y H:i:s \G\M\T', time() + (5))); # 5 seconds
  header('Cache-Control: no-store, no-cache, must-revalidate');
  header('Cache-Control: post-check=0, pre-check=0', FALSE);
  header('Pragma: no-cache');
  $pathArray = explode("/", $_SERVER["PATH_INFO"]);
  $relmon = $pathArray[1];
  $category = $pathArray[2];
  $fileName = str_replace("/$relmon/", "", $_SERVER["PATH_INFO"]);
  $dbFileName = "$relmon.sqlite";
  // echo $dbFileName; 
  $handle = new SQLite3($dbFileName);
  // echo $fileName;
  $queryString = "SELECT htmlgz FROM $category WHERE path='$fileName';";
  // echo $queryString;
  $result = $handle->querySingle($queryString);
  $handle->close();
  echo $result;
}
?>