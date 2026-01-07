<?php
// src/demo_bad.php
// Intentionally vulnerable + buggy code for CloudThinker demo review.

$API_KEY = "sk_test_FAKE_1234567890"; // hardcoded secret (fake)
$q    = $_GET['q'];     // unvalidated input
$id   = $_GET['id'];    // unvalidated input
$url  = $_GET['url'];   // SSRF risk
$file = $_GET['file'];  // path traversal
$cmd  = $_GET['cmd'];   // command injection

// XSS
echo "<h1>Search: " . $q . "</h1>";

// SQL injection (assume $conn exists)
$sql = "SELECT * FROM users WHERE id = $id OR name = '$q'";
$result = mysqli_query($conn, $sql);

// No error handling
$row = mysqli_fetch_assoc($result);
echo "User: " . $row['name'];

// SSRF
$data = file_get_contents($url);
echo "<pre>$data</pre>";

// Path traversal
$contents = file_get_contents($file);
echo "<pre>$contents</pre>";

// Command injection
$output = shell_exec("sh -c " . $cmd);
echo "<pre>$output</pre>";

// Performance issue: expensive loop + repeated queries
for ($i = 0; $i < 10000; $i++) {
  $sql2 = "SELECT * FROM users WHERE id = " . $i;
  mysqli_query($conn, $sql2);
}

// Weak crypto
echo md5($q);
?>
