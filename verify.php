<?php
/**
 * ==============================================================================
 * API ENDPOINT : verify.php
 * APPLICATION  : FeaturesticLeaks License Verification & HWID Binding Server
 * AUTHOR       : Senior PHP & Security Engineer
 * PURPOSE      : Validate user keys, enforce single-device HWID locks & expiry
 * ==============================================================================
 */

// Enable Error Reporting for Debugging (Disable in Production)
error_reporting(E_ALL);
ini_set('display_errors', 0);

// Force JSON Content-Type and Security Headers
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('X-XSS-Protection: 1; mode=block');

// Allow CORS if needed
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, User-Agent");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

/**
 * Send Standardized JSON Response
 */
function send_json($status, $message, $data = null, $http_code = 200) {
    http_response_code($http_code);
    $response = [
        'status'    => $status,        // 'SUCCESS', 'EXPIRED', 'INVALID', 'DEVICE_MISMATCH', 'ERROR'
        'message'   => $message,
        'timestamp' => date('Y-m-d H:i:s')
    ];
    if ($data !== null) {
        $response['data'] = $data;
    }
    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit();
}

// ------------------------------------------------------------------------------
// 1. INPUT EXTRACTION (Supports POST form-data, x-www-form-urlencoded, & Raw JSON)
// ------------------------------------------------------------------------------
$key  = isset($_POST['key']) ? trim($_POST['key']) : '';
$hwid = isset($_POST['hwid']) ? trim($_POST['hwid']) : '';

// Fallback to Raw JSON payload if POST parameters are empty
if (empty($key) || empty($hwid)) {
    $raw_input = file_get_contents('php://input');
    if (!empty($raw_input)) {
        $json_data = json_decode($raw_input, true);
        if (is_array($json_data)) {
            $key  = isset($json_data['key']) ? trim($json_data['key']) : $key;
            $hwid = isset($json_data['hwid']) ? trim($json_data['hwid']) : $hwid;
        }
    }
}

// Validate basic input presence
if (empty($key)) {
    send_json('INVALID', 'License Key parameter is required.', null, 400);
}
if (empty($hwid)) {
    send_json('INVALID', 'Hardware ID (HWID) parameter is required.', null, 400);
}

// ------------------------------------------------------------------------------
// 2. DATABASE STORAGE ENGINE (Supports MySQL PDO & JSON Fallback Engine)
// ------------------------------------------------------------------------------
$db_file = __DIR__ . '/keys_db.json';

// Initialize default JSON database if file does not exist
if (!file_exists($db_file)) {
    $initial_db = [
        "KEYS" => [
            "PAK-VIP-9999-ULTIMATE" => [
                "expiry_date"     => "2028-12-31",
                "registered_hwid" => null, // Unbound - will lock on first use
                "status"          => "ACTIVE",
                "note"            => "Master VIP License"
            ],
            "PAK-TEST-2026-KEY1" => [
                "expiry_date"     => "2027-06-30",
                "registered_hwid" => "FL-HWID-3A7F92B0C41E8D5A",
                "status"          => "ACTIVE",
                "note"            => "Registered Test Key"
            ],
            "PAK-EXPIRED-KEY-00" => [
                "expiry_date"     => "2024-01-01",
                "registered_hwid" => null,
                "status"          => "ACTIVE",
                "note"            => "Expired Key Test"
            ]
        ]
    ];
    file_put_contents($db_file, json_encode($initial_db, JSON_PRETTY_PRINT));
}

// Load Database Keys
$db_raw = file_get_contents($db_file);
$database = json_decode($db_raw, true);
$keys_table = isset($database['KEYS']) ? $database['KEYS'] : [];

// ------------------------------------------------------------------------------
// 3. KEY AUTHENTICATION & HWID BINDING LOGIC
// ------------------------------------------------------------------------------

// Check if Key exists in DB
if (!array_key_exists($key, $keys_table)) {
    send_json('INVALID', 'License Key does not exist or has been revoked.', null, 200);
}

$key_data = $keys_table[$key];

// Check Key Revocation Status
if (isset($key_data['status']) && $key_data['status'] !== 'ACTIVE') {
    send_json('INVALID', 'License Key has been disabled or revoked.', null, 200);
}

// Check Expiration Date
$current_date = new DateTime('now');
$expiry_date  = new DateTime($key_data['expiry_date']);

if ($current_date > $expiry_date) {
    send_json('EXPIRED', 'License Key has expired on ' . $key_data['expiry_date'], [
        'key'         => $key,
        'expiry_date' => $key_data['expiry_date'],
        'days_remaining' => 0
    ], 200);
}

// Calculate Days Remaining
$interval = $current_date->diff($expiry_date);
$days_remaining = (int)$interval->format('%r%a');

// Handle HWID Binding & Lock
$registered_hwid = $key_data['registered_hwid'];

if (empty($registered_hwid) || $registered_hwid === null) {
    // FIRST TIME ACTIVATION: Lock Key to this HWID
    $keys_table[$key]['registered_hwid'] = $hwid;
    $database['KEYS'] = $keys_table;
    file_put_contents($db_file, json_encode($database, JSON_PRETTY_PRINT));
    $registered_hwid = $hwid;
} elseif ($registered_hwid !== $hwid) {
    // DEVICE MISMATCH: Key belongs to a different HWID
    send_json('DEVICE_MISMATCH', 'Hardware ID mismatch. Key is locked to a different device.', [
        'key'             => $key,
        'your_hwid'       => $hwid,
        'registered_hwid' => $registered_hwid
    ], 200);
}

// ------------------------------------------------------------------------------
// 4. RETURN SUCCESSFUL AUTHENTICATION DATA
// ------------------------------------------------------------------------------
send_json('SUCCESS', 'Authentication successful. Access granted.', [
    'key'             => $key,
    'expiry_date'     => $key_data['expiry_date'],
    'days_remaining'  => $days_remaining,
    'registered_hwid' => $registered_hwid,
    'hwid_matched'    => true
], 200);
?>
