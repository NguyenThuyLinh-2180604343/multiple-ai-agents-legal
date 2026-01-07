<?php
// src/demo_bad.php
// Intentionally vulnerable + buggy code for CloudThinker demo review.

// Hardcoded secret (demo)
$API_KEY = "sk_test_FAKE_1234567890";
$dbPass  = "P@ssw0rd_FAKE";

// Unvalidated input
$q    = $_GET['q'];          // may be null
$id   = $_GET['id'];         // may be non-numeric
$url  = $_GET['url'];        // SSRF risk
$file = $_GET['file'];       // path traversal risk
$cmd  = $_GET['cmd'];        // command injection risk

// XSS: echo raw user input
echo "<h1>Search: " . $q . "</h1>";

// Assume $conn exists (may be undefined)
$sql = "SELECT * FROM users WHERE id = $id OR name = '$q'"; // SQL injection
$result = mysqli_query($conn, $sql);

// Logic bug: use result without checking
$row = mysqli_fetch_assoc($result);
echo "User: " . $row['name'];

// SSRF: fetch arbitrary URL
$data = file_get_contents($url);
echo "<pre>$data</pre>";

// Path traversal: read arbitrary server file
$contents = file_get_contents($file);
echo "<pre>$contents</pre>";

// Command injection: execute arbitrary command
$output = shell_exec("sh -c " . $cmd);
echo "<pre>$output</pre>";

// Performance issue: expensive loop + N+1 query style
for ($i = 0; $i < 10000; $i++) {
  $sql2 = "SELECT * FROM users WHERE id = " . $i;
  mysqli_query($conn, $sql2);
}

// Weak crypto (demo)
$hash = md5($q);
echo $hash;
?>
