<?php
if (!isset($_SERVER["PATH_INFO"])) {
?>
  <!doctype html>
  <html lang="en">
    <head>
      <!-- Required meta tags -->
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
      <link rel="icon" href="favicon.png">
      <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900">

      <!-- Bootstrap CSS -->
      <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
      <link rel="stylesheet" type="text/css" href="style.css">
      <title>RelMon Reports</title>
    </head>
    <body>
      <header class="v-sheet v-sheet--tile theme--light v-toolbar v-app-bar v-app-bar--fixed elevation-3" data-booted="true" style="height: 64px; margin-top: 0px; transform: translateY(0px); left: 0px; right: 0px;">
        <div class="v-toolbar__content" style="height: 64px;">
          <div class="headline">
            <span>RelMon</span><span class="font-weight-light">Reports</span>
          </div>
        </div>
      </header>
      <div class="container" style="padding: 12px">
        <div class="row card elevation-3">
          <div class="card-body">
            <ul>
              <li><a href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/RelMon">RelMon twiki</a></li>
              <li><a href="http://cmsweb.cern.ch/dqm/online">Link to the Online DQM GUI</a></li>
              <li><a href="http://cmsweb.cern.ch/dqm/offline">Link to the Offline DQM GUI</a></li>
              <li><a href="http://cmsweb.cern.ch/dqm/relval">Link to the RelVal DQM GUI</a></li>
            </ul>
          </div>
        </div>
  <?php
        $relmons = glob('./*.sqlite');
        usort($relmons, function($a, $b) { return filemtime($a) < filemtime($b); });
        foreach($relmons as $relmon) {
  ?>
          <div class="row card mt-2 elevation-3">
            <div class="card-body">
              <div class="row">
                <div class="col-sm-12 col-md-8">
  <?php
                  $stat = stat($relmon);
                  $lastModified = date("Y-m-d H:i", $stat['mtime']);
                  $size = round($stat['size'] / (1024.0 * 1024.0), 2);
                  $relmonName = str_replace("./", "", $relmon);
                  $relmonName = str_replace(".sqlite", "", $relmonName);
                  print("<span class=\"bigger-text\" id=\"$relmonName\">$relmonName</span><br><span class=\"font-weight-light\">Created:</span> $lastModified</span><br><span class=\"font-weight-light\">Size:</span> $size MB");
  ?>
                </div>
                <div class="col-sm-12 col-md-4">
                  <span class="bigger-text font-weight-light">Subcategories:</span>
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
  header('PATH: ' .$_SERVER["PATH_INFO"]);
  $pathArray = explode("/", $_SERVER["PATH_INFO"]);
  $relmon = $pathArray[1];
  $category = $pathArray[2];
  $fileName = str_replace("/$relmon/", "", $_SERVER["PATH_INFO"]);
  $dbFileName = "$relmon.sqlite";
  if (!file_exists($dbFileName)) {
    echo "";
  } else {
    $handle = new SQLite3($dbFileName);
    $queryString = "SELECT htmlgz FROM $category WHERE path='$fileName';";
    $result = $handle->querySingle($queryString);
    $handle->close();
    echo $result;
  }
}
?>
