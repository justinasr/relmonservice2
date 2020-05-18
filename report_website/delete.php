<?php
$authorizedUser = in_array('cms-ppd-pdmv-val-admin-pdmv', explode(';', strtolower($_SERVER['HTTP_ADFS_GROUP'])));
$name = $_POST['name'];
if ($authorizedUser) {
  unlink($name . '.sqlite');
}
?>
