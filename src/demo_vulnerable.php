<?php
// src/demo_vulnerable.php
// Intentionally vulnerable code for CloudThinker demo review.
// DO NOT USE IN PRODUCTION.

// Hardcoded secrets (fake)
$API_KEY = "sk_test_FAKE_1234567890";
$DB_PASSWORD = "password123";

// Unvalidated user inputs
$q    = $_GET['q'];     // XSS, SQL injection
$id   = $_GET['id'];    // SQL injection
$url  = $_GET['url'];   // SSRF
$file = $_GET['file'];  // Path traversal
$cmd  = $_GET['cmd'];   // Command injection

// XSS vulnerability
echo "<h1>Search query: " . $q . "</h1>";

// Assume $conn exists (undefined variable risk)
$sql = "SELECT * FROM users WHERE id = $id OR name = '$q'";
$result = mysqli_query($conn, $sql);

// No error handling
$row = mysqli_fetch_assoc($result);
echo "User name: " . $row['name'];

// SSRF vulnerability
$data = file_get_contents($url);
echo "<pre>$data</pre>";

// Path traversal vulnerability
$contents = file_get_contents($file);
echo "<pre>$contents</pre>";

// Command injection vulnerability
$output = shell_exec("sh -c " . $cmd);
echo "<pre>$output</pre>";

// Performance issue: unnecessary heavy loop + repeated queries
for ($i = 0; $i < 10000; $i++) {
    $sql2 = "SELECT * FROM users WHERE id = " . $i;
    mysqli_query($conn, $sql2);
}

// Weak cryptography
echo md5($q);
?>
